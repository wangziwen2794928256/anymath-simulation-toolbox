"""csf_archetypes —— 顶会顶刊图表原型库（P1 核心）

设计动机
--------
`csf_fig.py` 解决了"组件不自动撑开、颜色语义不一致、导出不规范"，
但它仍是**低层绘图原语**：每次画图都要从第一个矩形开始手摆，于是不同题目的
出图质量方差极大，且无法保证"看起来像顶会论文"。

本模块补上**原型层**：把顶会论文里最高频的四种图固化成参数化模板，
调用者只填内容，不摆坐标。

| 原型 | 对应顶会惯例 | 关键约束（自动保证） |
|---|---|---|
| `method_figure()` | Figure 1 方法总览图 | 分层带状布局、模块自动撑开、箭头吸附框边、虚线=反馈/实线=数据流、模块数×名称长度自适应字号 |
| `result_panels()` | 主结果复合组图 a/b/c/d | 统一面板标签、跨面板共享配色、误差棒/显著性自动标注、每面板一句 takeaway |
| `comparison_table()` | 主实验大表 | 行=方法/列=指标、mean±std、最优加粗次优斜体、按列自动对齐、显著性角标 |
| `ablation_matrix()` | 消融/排列组合矩阵 | 网格热力 + 每格数值、组件轴×超参轴、贡献差值列 |

为什么是这四个：它们是顶会论文的"骨架图"——审稿人与评委对论文的第一印象
几乎完全由这四类图表决定（方法图看懂了才读正文，主结果表决定可信度，
复合图决定工作量观感，消融矩阵决定严谨性）。

统一约定
--------
* 所有原型共用 `csf_fig.SemanticPalette`，一个角色一个颜色，跨图一致。
* 所有原型默认导出 **PDF（矢量）+ SVG（可编辑）+ PNG（300dpi）** 三份。
* 所有原型**不在图内写标题**——标题交给 LaTeX `\\caption`（这条是实测换来的铁律：
  旧稿每张图的标题都出现了两次）。
* 所有文字使用 `csf_fig.use_style()` 建立的 CJK 字体链，缺字即报错。

用法见 `examples/` 与 `references/14-figure-archetypes.md`。
"""

from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime

import matplotlib

matplotlib.use("Agg")

import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from csf_fig import (  # noqa: E402
    SEMANTIC,
    SemanticPalette,
    _stamp_role,
    resolved_font_path,
    use_style,
)

__all__ = [
    "ArchNode",
    "ArchSpec",
    "method_figure",
    "result_panels",
    "comparison_table",
    "ablation_matrix",
    "MM_TO_INCH",
    "collect_labels",
    "export_label_ledger",
    "LABEL_ROLES",
    "LABEL_ROLE_DOC",
    "LABEL_COLUMNS",
]

MM_TO_INCH = 1.0 / 25.4

# 顶会常用宽度（mm）：单栏 89、1.5 栏 120、双栏 183
W_SINGLE, W_1_5, W_DOUBLE = 89.0, 120.0, 183.0

#: 方法图底部图例的文字（语言相关；中文保持历史文案不变）
METHOD_LEGEND: dict[str, dict[str, str]] = {
    "zh": {"data": "数据流", "feedback": "反馈闭环"},
    "en": {"data": "Data flow", "feedback": "Feedback loop"},
}


def _legend_text(lang: str) -> dict[str, str]:
    return METHOD_LEGEND.get((lang or "zh").lower(), METHOD_LEGEND["zh"])


def _mark(artist, role: str):
    """给 Text 打语义角色（台账用）。"""
    return _stamp_role(artist, role)


# =========================================================================== #
# 原型一：方法总览图（Figure 1 / method overview）
# =========================================================================== #

@dataclass
class ArchNode:
    """架构图中的一个模块块。

    只描述"是什么"，不描述"画在哪"——位置由 `ArchSpec` 的分层布局自动计算。
    """

    key: str
    title: str
    body: str = ""                       # 第二行：关键量/维度/公式，可为空
    role: str = "ours"                   # 语义角色，决定颜色（必须已在 SEMANTIC 登记）
    lane: int = 0                        # 所属层（0 起），同层横向排布
    order: int = 0                       # 同层内的左右次序
    width: float | None = None           # 覆盖自动宽度（画布单位）
    height: float | None = None          # 覆盖自动高度
    formula: str = ""                    # 右侧标注的公式编号/符号，如 r"$c_i=d_i+\lambda Q_e$"


@dataclass
class ArchSpec:
    """方法总览图规格：分层带状布局 + 自动撑开 + 箭头吸附。

    布局规则（顶会常见）：
      * 数据流自左向右（同一 lane 内按 `order` 排列），层与层之间自上而下；
      * 每层有一个**层标题**（如"环境层 Environment"），左对齐置于带首；
      * 带宽按该层模块最大高度自适应，层间留白固定；
      * 实线箭头 = 前向数据流，虚线箭头 = 反馈闭环。
    """

    lanes: list[str] = field(default_factory=list)      # 层标题
    width_mm: float = W_DOUBLE
    height_mm: float | None = None
    palette: SemanticPalette = field(default_factory=SemanticPalette)
    title: str = ""                                     # 仅用于文件名提示，不画进图里

    def __post_init__(self) -> None:
        self.nodes: dict[str, ArchNode] = {}
        self._edges: list[tuple[str, str, str, str, str]] = []  # src,dst,label,style,role

    # -- 声明 --------------------------------------------------------------- #
    def add(self, node: ArchNode) -> ArchNode:
        if node.role not in self.palette.mapping:
            raise KeyError(
                f"模块 {node.key!r} 使用了未登记的语义角色 {node.role!r}。"
                f"已登记：{sorted(self.palette.mapping)}"
            )
        if node.key in self.nodes:
            raise ValueError(f"模块 key 重复：{node.key!r}")
        self.nodes[node.key] = node
        return node

    def link(self, src: str, dst: str, label: str = "", *, style: str = "solid",
             role: str = "text") -> None:
        """连一条箭头。style='dashed' 表示反馈闭环（顶会惯例）。"""
        for k in (src, dst):
            if k not in self.nodes:
                raise KeyError(f"箭头端点 {k!r} 不在模块表中")
        self._edges.append((src, dst, label, style, role))

    # -- 布局 --------------------------------------------------------------- #
    def _lanes(self) -> dict[int, list[ArchNode]]:
        out: dict[int, list[ArchNode]] = {}
        for n in self.nodes.values():
            out.setdefault(n.lane, []).append(n)
        for v in out.values():
            v.sort(key=lambda n: n.order)
        return dict(sorted(out.items()))

    def _text_width(self, text: str, fontsize: float, canvas_w: float) -> float:
        """按最长行估算像素宽→画布单位（全角 1.0em、半角 0.55em）。"""
        em = fontsize * (canvas_w / (self.width_mm / MM_TO_INCH * 72.0))
        longest = 0.0
        for line in (text or "").split("\n"):
            longest = max(longest, sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in line))
        return longest * em

    def _em(self, fontsize: float, canvas_w: float) -> float:
        """1 em 对应多少画布单位。"""
        return fontsize * (canvas_w / (self.width_mm / MM_TO_INCH * 72.0))

    def check_topology(self) -> list[str]:
        """检查连线是否会造成视觉噪声，返回问题列表（不抛异常，只提示）。

        顶会方法总览图的读图习惯是"自上而下、自左向右"。违反该习惯的连线会让
        读者需要来回跳跃，是最常见的"图看不懂"原因。本检查把三类反模式显式列出：

        1. **跨层横穿**：连线两端分属不同层，但横向位移远大于纵向位移，
           箭头会横穿整幅图并压过中间模块。
        2. **同层反向**：同一层内 `order` 大的模块指向 `order` 小的模块（逆流）。
        3. **逆层回指**：从下层指向更上层，若为实线则与"数据流自上而下"矛盾
           （反馈应当用虚线，且 `role='bottleneck'`）。
        """
        issues: list[str] = []
        for src, dst, label, style, _role in self._edges:
            a, b = self.nodes[src], self.nodes[dst]
            tag = f"{src} → {dst}" + (f"（{label}）" if label else "")
            if a.lane != b.lane:
                same_src = [n for n in self.nodes.values() if n.lane == a.lane]
                same_dst = [n for n in self.nodes.values() if n.lane == b.lane]
                ax_ = sum(n.order for n in same_src) / max(len(same_src), 1)
                bx_ = sum(n.order for n in same_dst) / max(len(same_dst), 1)
                dx, dy = abs(bx_ - ax_), abs(b.lane - a.lane)
                if dx > 1.0 and dx > dy:
                    issues.append(
                        f"跨层横穿：{tag} 横向跨 {dx:.0f} 个模块位、纵向仅 {dy} 层，"
                        "箭头会斜穿并压过中间模块。建议改为相邻层、同位次的垂直连线。"
                    )
            else:
                if b.order < a.order and style == "solid":
                    issues.append(
                        f"同层反向：{tag} 在同层内逆流（order {a.order} → {b.order}）。"
                        "建议调整 order 或改为虚线反馈。"
                    )
            if b.lane < a.lane and style != "dashed":
                issues.append(
                    f"逆层回指：{tag} 自第 {a.lane} 层指回第 {b.lane} 层却用实线。"
                    "回指应使用 style='dashed'（顶会惯例：虚线表示反馈闭环）。"
                )
        return issues

    def render(self, *, font_size: float = 8.5, save: tuple[str, str] | None = None,
               show: bool = False, strict_topology: bool = False,
               lang: str = "zh", labels: bool = True,
               narrative_role: str = "", takeaway: str = "") -> plt.Figure:
        """按分层布局渲染。返回 Figure；`save=(outdir, name)` 时同时导出三份。

        `lang='en'` 时图例文字用英文；`labels=True` 时同时写文字台账
        （`<name>.labels.json` / `.csv`，含 narrative_role / takeaway）。

        迭代中修掉的三个实测缺陷（都是"手摆坐标"的典型病）：
          1. 层标题用竖直文字写在 x=0.4，**超出坐标范围被裁切** →
             改为占位的左侧留白栏（`lane_gutter`），并计入画布宽度。
          2. 模块的 `formula` 写在框下方 y-1.4，当 height 较小时**与框内第二行重叠**
             （实测"宏观指标"被 "ρ" 压住）→ 公式改为写在框内最后一行之后，
             并把所需高度计入自动高度；同时与外层留白一起计算。
          3. 画布高度按内容算出，但**宽度固定 100**，模块总宽小于画布时右侧留大片空白 →
             按各层最大总宽反推画布宽度，使内容填满。
        """
        lanes = self._lanes()
        n_lanes = len(lanes)
        if n_lanes == 0:
            raise ValueError("架构图至少需要一个模块")

        # 拓扑自检：把"图看不懂"的原因显式报出来，而不是画完才发现
        topo = self.check_topology()
        if topo:
            msg = "[archetype] 方法图拓扑警告（%d 项）：\n  - %s" % (len(topo), "\n  - ".join(topo))
            if strict_topology:
                raise ValueError(msg)
            print(msg)

        gap_x, gap_y = 3.0, 5.0
        pad_top, pad_bot = 3.0, 3.0
        lane_gutter = 7.0        # 左侧留给层标题的竖直文字
        has_feedback = any(e[3] == "dashed" for e in self._edges)
        legend_band = 7.0 if has_feedback else 0.0   # 底部专用图例带，避免与模块重叠
        canvas_w = 100.0

        # --- 先按内容算每层模块宽度与高度 ---
        node_boxes: dict[str, tuple[float, float, float, float, ArchNode]] = {}
        lane_heights: list[float] = []
        lane_widths: list[float] = []
        em = self._em(font_size, canvas_w)
        for lane_idx, nodes in lanes.items():
            x = lane_gutter
            max_h = 0.0
            for nd in nodes:
                lines = [nd.title] + ([nd.body] if nd.body else [])
                # 公式单独占一行（顶会惯例：模块内先名称、再关键量、再公式）
                text_lines = len(lines) + (1 if nd.formula else 0)
                w = nd.width or max(
                    16.0,
                    self._text_width("\n".join(lines + ([nd.formula] if nd.formula else [])),
                                     font_size, canvas_w) + 5.0,
                )
                # 高度 = 文本行数 × 行距 + 上下内边距；行距 1.75 保证不粘连
                h = nd.height or max(11.0, text_lines * font_size * 1.75 * em + 4.0)
                node_boxes[nd.key] = (x, 0.0, w, h, nd)
                x += w + gap_x
                max_h = max(max_h, h)
            lane_heights.append(max_h)
            lane_widths.append(x - gap_x)

        content_w = max(lane_widths) + gap_x
        canvas_w = max(content_w, 60.0)
        em = self._em(font_size, canvas_w)   # 宽度变了，重算 em（宽度不再固定 100）

        # 用新 canvas_w 重算一次宽度（一次迭代即可收敛到可读结果）
        node_boxes.clear()
        lane_heights.clear()
        lane_widths.clear()
        for lane_idx, nodes in lanes.items():
            x = lane_gutter
            max_h = 0.0
            for nd in nodes:
                lines = [nd.title] + ([nd.body] if nd.body else [])
                text_lines = len(lines) + (1 if nd.formula else 0)
                w = nd.width or max(
                    16.0,
                    self._text_width("\n".join(lines + ([nd.formula] if nd.formula else [])),
                                     font_size, canvas_w) + 5.0,
                )
                h = nd.height or max(11.0, text_lines * font_size * 1.75 * em + 4.0)
                node_boxes[nd.key] = (x, 0.0, w, h, nd)
                x += w + gap_x
                max_h = max(max_h, h)
            lane_heights.append(max_h)
            lane_widths.append(x - gap_x)
        canvas_w = max(max(lane_widths) + gap_x, 60.0)

        total_h = pad_top + sum(lane_heights) + gap_y * (n_lanes - 1) + pad_bot + legend_band
        canvas_h = max(total_h, 40.0)
        # 纵横比下限随层数放宽；上限 0.95 避免出现近正方形/纵向长条
        aspect_floor = min(0.95, 0.48 + 0.11 * n_lanes)
        canvas_h = max(canvas_h, canvas_w * aspect_floor)
        height_mm = self.height_mm or self.width_mm * (canvas_h / canvas_w)

        # 层间留白按实际可用高度自适应
        avail = canvas_h - pad_top - pad_bot - legend_band - sum(lane_heights)
        gap_y = max(2.0, min(gap_y, avail / (n_lanes - 1))) if n_lanes > 1 else 0.0

        fig = plt.figure(figsize=(self.width_mm * MM_TO_INCH, height_mm * MM_TO_INCH), dpi=300)
        ax = fig.add_axes((0.008, 0.008, 0.984, 0.984))
        ax.set_xlim(0, canvas_w)
        ax.set_ylim(0, canvas_h)
        ax.axis("off")

        # --- 自上而下分配 y ---
        # 注意：不能在这里再减 legend_band —— 画布高度已按
        # pad + lanes + gaps + legend_band 算过，若 y_top 再减一次，
        # 最底层会被压进图例带造成重叠（实测缺陷）。
        y_top = canvas_h - pad_top
        for li, (lane_idx, nodes) in enumerate(lanes.items()):
            h = lane_heights[li]
            y = y_top - h
            label = self.lanes[lane_idx] if lane_idx < len(self.lanes) else f"L{lane_idx}"
            _mark(ax.text(lane_gutter / 2, y + h / 2, label,
                          ha="center", va="center", fontsize=font_size - 0.5,
                          color="#7F7F7F", rotation=90, alpha=0.95), "lane-label")
            for nd in nodes:
                x, _, w, hh, _ = node_boxes[nd.key]
                node_boxes[nd.key] = (x, y + (h - hh) / 2, w, hh, nd)
            y_top = y - gap_y

        # --- 画块 ---
        for key, (x, y, w, h, nd) in node_boxes.items():
            color = self.palette(nd.role)
            for alpha, z in ((0.10, 2), (0.0, 3)):
                ax.add_patch(mpl.patches.FancyBboxPatch(
                    (x, y), w, h,
                    boxstyle=f"round,pad=0,rounding_size={min(1.6, h * 0.16)}",
                    linewidth=1.25, edgecolor=color,
                    facecolor=color if alpha else "none", alpha=1.0 if alpha else 1.0,
                    zorder=z,
                ))
                if alpha:
                    ax.patches[-1].set_alpha(0.10)
            txt = nd.title + (f"\n{nd.body}" if nd.body else "")
            if nd.formula:
                txt += f"\n{nd.formula}"
            # 名称行加粗、其余行常规：用多段文本堆叠实现
            _mark(ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center",
                          fontsize=font_size, color="#1A1A1A", linespacing=1.75,
                          zorder=4), "node")

        # --- 画箭头（锚点吸附到框边）---
        def anchor(src_box, dst_box):
            sx, sy, sw, sh, _ = src_box
            dx, dy, dw, dh, _ = dst_box
            scx, scy = sx + sw / 2, sy + sh / 2
            dcx, dcy = dx + dw / 2, dy + dh / 2
            vx, vy = dcx - scx, dcy - scy
            if abs(vx) >= abs(vy):
                return ((sx + sw, scy), (dx, dcy)) if vx >= 0 else ((sx, scy), (dx + dw, dcy))
            return ((scx, sy + sh), (dcx, dy)) if vy >= 0 else ((scx, sy), (dcx, dy + dh))

        # 累积已放置标签位置，用于标签避让
        placed_labels: list[tuple[float, float]] = []

        def box_hit(px: float, py: float, exclude: set[str] | None = None) -> bool:
            exclude = exclude or set()
            for k, (bx, by, bw, bh, _nd) in node_boxes.items():
                if k in exclude:
                    continue
                if bx - 1.0 <= px <= bx + bw + 1.0 and by - 1.0 <= py <= by + bh + 1.0:
                    return True
            return False

        for src, dst, label, style, role in self._edges:
            a, b = self.nodes[src], self.nodes[dst]
            p0, p1 = anchor(node_boxes[src], node_boxes[dst])
            c = self.palette(role) if role in self.palette.mapping else "#4D4D4D"
            ls = "--" if style == "dashed" else "-"

            cross_lane = a.lane != b.lane
            # 跨层连线：走**正交折线**，水平段沿"源框下边/目标框上边"，
            # 竖直段走在两层之间的空隙里（不穿任何框）。
            # 这样长连线不再斜穿模块（实测缺陷：斜线压过相邻框）。
            route_ok = False
            if cross_lane:
                src_box = node_boxes[src]
                dst_box = node_boxes[dst]
                sx, sy, sw, sh, _ = src_box
                dxb, dyb, dwb, dhb, _ = dst_box
                a_center = sx + sw / 2
                b_center = dxb + dwb / 2
                # 源框朝目标的那条边
                y_from = sy if b.lane > a.lane else sy + sh
                y_to = dyb + dhb if b.lane > a.lane else dyb
                mid_y = (y_from + y_to) / 2
                # 竖直段 x 的候选，按"离源/目标中心最近"排序，避开所有框
                cands = [a_center, b_center, (a_center + b_center) / 2]
                # 再补充相邻模块之间的空隙中心，作为兜底
                xs = sorted({round(v[0], 4) for v in node_boxes.values()} |
                            {round(v[0] + v[2], 4) for v in node_boxes.values()})
                for i in range(len(xs) - 1):
                    if xs[i + 1] - xs[i] > 1.0:
                        cands.append((xs[i] + xs[i + 1]) / 2)
                chosen_x = None
                for cx in cands:
                    if not box_hit(cx, mid_y, exclude={src, dst}) and not box_hit(cx, y_from, exclude={src, dst}) \
                       and not box_hit(cx, y_to, exclude={src, dst}):
                        chosen_x = cx
                        break
                if chosen_x is not None:
                    path = [(a_center, y_from), (chosen_x, y_from),
                            (chosen_x, y_to), (b_center, y_to)]
                    for i in range(len(path) - 1):
                        ax.plot([path[i][0], path[i + 1][0]], [path[i][1], path[i + 1][1]],
                                color=c, lw=1.3, ls=ls, zorder=5, solid_capstyle="round")
                    ax.annotate("", xy=(b_center, y_to), xytext=(b_center, y_to), zorder=5,
                                arrowprops=dict(arrowstyle="-|>", color=c, linewidth=1.3,
                                                linestyle=ls, shrinkA=0, shrinkB=0))
                    label_pos = (chosen_x, mid_y)
                    route_ok = True
            if not route_ok:
                ax.annotate("", xy=p1, xytext=p0, zorder=5,
                            arrowprops=dict(arrowstyle="-|>", color=c, linewidth=1.3,
                                            linestyle=ls, shrinkA=1.5, shrinkB=1.5))
                label_pos = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)

            if label and label_pos is not None:
                lx0, ly0 = label_pos
                # 标签避让：尝试若干候选偏移，挑第一个不压框、不压其他标签的
                chosen = None
                for off in ((0, 0), (0, 1.8), (0, -1.8), (3.0, 0), (-3.0, 0), (2.2, 1.6), (-2.2, 1.6)):
                    cx, cy = lx0 + off[0], ly0 + off[1]
                    if not box_hit(cx, cy) and not any(
                        abs(px - cx) < 5.0 and abs(py - cy) < 2.6 for px, py in placed_labels
                    ):
                        chosen = (cx, cy)
                        break
                if chosen is None:
                    chosen = (lx0, ly0)
                placed_labels.append(chosen)
                _mark(ax.text(chosen[0], chosen[1], label, ha="center", va="center",
                              fontsize=font_size - 1.4, color=c, zorder=7,
                              bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none",
                                        alpha=0.95)), "annotation")

        # 图例放在**专用底部带**内（legend_band），不再与模块或标签重叠
        if has_feedback:
            legend_txt = _legend_text(lang)
            lx = canvas_w - 34
            ly = pad_bot + legend_band / 2 + 1.4
            ax.plot([lx, lx + 6], [ly + 1.5, ly + 1.5], color="#4D4D4D", lw=1.3)
            _mark(ax.text(lx + 7, ly + 1.5, legend_txt["data"], fontsize=font_size - 1.5,
                          va="center", color="#4D4D4D"), "legend")
            ax.plot([lx, lx + 6], [ly - 1.5, ly - 1.5], color="#D62728", lw=1.3, ls="--")
            _mark(ax.text(lx + 7, ly - 1.5, legend_txt["feedback"], fontsize=font_size - 1.5,
                          va="center", color="#D62728"), "legend")

        if save:
            outdir, name = save
            _export(fig, outdir, name, lang=lang, labels=labels,
                    narrative_role=narrative_role, takeaway=takeaway)
        if show:
            plt.show()
        else:
            plt.close(fig)
        return fig


def method_figure(
    lanes: list[str],
    nodes: list[ArchNode],
    edges: list[tuple],
    *,
    outdir: str,
    name: str,
    width_mm: float = W_DOUBLE,
    font_size: float = 8.5,
    lang: str = "zh",
    labels: bool = True,
    narrative_role: str = "",
    takeaway: str = "",
    strict_topology: bool = False,
) -> dict[str, str]:
    """一步生成方法总览图（顶会 Figure 1 惯例）。

    参数
    ----
    lanes : 层标题，自上而下
    nodes : 模块（含 lane/order/role）
    edges : (src, dst, label, style) 或 (src, dst, label)，style ∈ {solid, dashed}
    lang : ``'zh'`` / ``'en'``——只影响图内固定文案（底部图例）与台账的语言标记；
           模块名/层名由调用方给出。
    labels : 是否写出文字台账（``<name>.labels.json`` / ``.csv``）。
    narrative_role / takeaway : 该图在论证链里的角色与要读出的一句话结论，
        会写进台账顶层（``narrative_role`` / ``takeaway``），把图与叙事绑起来。
    """
    spec = ArchSpec(lanes=lanes, width_mm=width_mm)
    for nd in nodes:
        spec.add(nd)
    for e in edges:
        if len(e) == 4:
            spec.link(e[0], e[1], e[2], style=e[3])
        else:
            spec.link(e[0], e[1], e[2])
    spec.render(font_size=font_size, save=(outdir, name), lang=lang, labels=labels,
                narrative_role=narrative_role, takeaway=takeaway,
                strict_topology=strict_topology)
    return {fmt: os.path.join(outdir, f"{name}.{fmt}") for fmt in ("pdf", "svg", "png")}


# =========================================================================== #
# 原型二：主结果复合组图（multi-panel result figure）
# =========================================================================== #

def result_panels(
    panels: list[dict],
    *,
    outdir: str,
    name: str,
    ncols: int = 2,
    width_mm: float = W_DOUBLE,
    panel_height_mm: float = 62.0,
    font_size: float = 8.0,
    share_legend: bool = True,
    lang: str = "zh",
    labels: bool = True,
    narrative_role: str = "",
    takeaway: str = "",
) -> dict[str, str]:
    """复合结果组图：每个 panel 是一个"画什么"的声明，不是一段 matplotlib 代码。

    panel 字典字段
    --------------
    kind : 'line' | 'bar' | 'grouped_bar' | 'scatter' | 'heatmap'
    claim : 该面板要读出的结论（会作为面板小标题）
    xlabel, ylabel : 轴标题
    series : list[dict]，每项 {label, role, x, y, yerr?, style?}
              role 决定颜色，必须已在 SEMANTIC 登记 → 跨面板颜色语义一致
    annotate / sig : 可选，显著性星号或文本标注
    xticks, yticks, xlim, ylim : 可选

    自动保证：面板标签 a/b/c、统一字体与线宽、误差棒、网格轻微、图例无边框且
    只在**第一个**面板出现（共享图例），避免每面板重复图例造成的视觉噪声。
    """
    pal = SemanticPalette()
    n = len(panels)
    nrows = int(math.ceil(n / ncols))
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(width_mm * MM_TO_INCH, (panel_height_mm * nrows + 6) * MM_TO_INCH),
        dpi=300,
    )
    axes = np.atleast_1d(axes).ravel()

    legend_done = False
    for i, p in enumerate(panels):
        ax = axes[i]
        kind = p.get("kind", "line")
        handles = []

        if kind in ("line", "scatter"):
            for s in p.get("series", []):
                c = pal(s["role"])
                if kind == "line":
                    ln, = ax.plot(s["x"], s["y"], color=c, lw=1.6,
                                  ls=s.get("style", "-"), marker=s.get("marker", ""),
                                  ms=3.2, label=s["label"], zorder=3)
                else:
                    ln = ax.scatter(s["x"], s["y"], s=14, color=c, alpha=0.75,
                                    edgecolors="white", linewidths=0.3, label=s["label"], zorder=3)
                handles.append(ln)
                if s.get("yerr") is not None:
                    ax.errorbar(s["x"], s["y"], yerr=s["yerr"], fmt="none",
                                ecolor=c, elinewidth=0.9, capsize=2, alpha=0.8, zorder=2)
                if s.get("band") is not None:
                    lo, hi = s["band"]
                    ax.fill_between(s["x"], lo, hi, color=c, alpha=0.16, lw=0, zorder=1)

        elif kind in ("bar", "grouped_bar"):
            series = p.get("series", [])
            labels = p.get("xticks", [s["label"] for s in series])
            if kind == "bar":
                for s in series:
                    vals = np.atleast_1d(s["y"])
                    xs = np.arange(len(vals))
                    b = ax.bar(xs, vals, color=pal(s["role"]), width=0.62,
                               edgecolor="black", linewidth=0.5, label=s["label"], zorder=3)
                    handles.append(b)
                    yerr = s.get("yerr")
                    # 误差棒只在 std 非零时画：std=0 时 errorbar 会画出一条**与柱顶
                    # 重合的横线，直接把柱顶数值穿掉**（实测缺陷："483.9̶4̶"）。
                    if yerr is not None:
                        ye = np.atleast_1d(np.asarray(yerr, dtype=float))
                        if np.any(ye > 0):
                            ax.errorbar(xs, vals, yerr=ye, fmt="none", ecolor="#333333",
                                        elinewidth=0.9, capsize=2.5, zorder=4)
                    # 数值标在"柱顶 + 误差棒上端 + 间隙"之上，避免任何重叠
                    top = vals.copy()
                    if yerr is not None:
                        ye = np.atleast_1d(np.asarray(yerr, dtype=float))
                        top = vals + np.where(np.isfinite(ye), ye, 0.0)
                    span = (ax.get_ylim()[1] - ax.get_ylim()[0]) or (vals.max() or 1.0)
                    for xxi, vv, tt in zip(xs, vals, top):
                        _mark(ax.text(xxi, tt + span * 0.018, f"{vv:g}", ha="center",
                                      va="bottom", fontsize=font_size - 1.6, zorder=6),
                              "data-label")
                ax.set_xticks(np.arange(len(labels)))
                ax.set_xticklabels(labels)
            else:
                m = len(series)
                w = 0.78 / max(m, 1)
                base = np.arange(len(labels))
                for j, s in enumerate(series):
                    vals = np.atleast_1d(s["y"])
                    b = ax.bar(base + (j - (m - 1) / 2) * w, vals, width=w * 0.92,
                               color=pal(s["role"]), edgecolor="black", linewidth=0.5,
                               label=s["label"], zorder=3)
                    handles.append(b)
                    if s.get("yerr") is not None:
                        ax.errorbar(base + (j - (m - 1) / 2) * w, vals, yerr=s["yerr"],
                                    fmt="none", ecolor="#333333", elinewidth=0.9, capsize=2.2, zorder=4)
                ax.set_xticks(base)
                ax.set_xticklabels(labels)

            # 柱子顶部的数值标注必须**留出上方余量**，否则最高那根柱子的标注会被
            # 坐标区上沿裁掉一半——实测在开源示例图上肉眼可见（"426.7" 被削顶）。
            # 原因：标注写在 vals+yerr 之上，而 matplotlib 自动缩放只保证**数据**
            # 不越界，不保证**标注**不越界。这里显式按"最高的柱顶 + 误差棒 + 12% 余量"
            # 设 ylim，与 label 的摆放规则保持一致。
            _tops = []
            for s in series:
                v = np.atleast_1d(np.asarray(s["y"], dtype=float))
                yerr_s = s.get("yerr")
                if yerr_s is not None:
                    ye = np.atleast_1d(np.asarray(yerr_s, dtype=float))
                    v = v + np.where(np.isfinite(ye), ye, 0.0)
                _tops.append(float(np.max(v)))
            if _tops:
                hi = max(_tops)
                lo = min(0.0, hi)
                ax.set_ylim(lo, hi + (hi - lo) * 0.14 if hi > lo else hi + 1.0)
            if p.get("xticks"):
                ax.set_xticks(np.arange(len(p["xticks"])))
                ax.set_xticklabels(p["xticks"])

        elif kind == "heatmap":
            M = np.asarray(p["matrix"], dtype=float)
            im = ax.imshow(M, aspect="auto", cmap=p.get("cmap", "viridis"),
                           vmin=p.get("vmin"), vmax=p.get("vmax"))
            cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
            cb.ax.tick_params(labelsize=font_size - 1.5)
            if p.get("colorbar_label"):
                cb.set_label(p["colorbar_label"], fontsize=font_size - 1)
            ax.set_xticks(np.arange(M.shape[1]))
            ax.set_yticks(np.arange(M.shape[0]))
            if p.get("xticks"):
                ax.set_xticklabels(p["xticks"])
            if p.get("yticks"):
                ax.set_yticklabels(p["yticks"])
            if p.get("annotate_cells", True):
                for r in range(M.shape[0]):
                    for c_ in range(M.shape[1]):
                        v = M[r, c_]
                        _mark(ax.text(c_, r, f"{v:g}", ha="center", va="center",
                                      fontsize=font_size - 2.0,
                                      color="white" if v > (np.nanmax(M) + np.nanmin(M)) / 2
                                      else "black"), "data-label")

        # 轴与标注
        if p.get("xlabel"):
            ax.set_xlabel(p["xlabel"], fontsize=font_size)
        if p.get("ylabel"):
            ax.set_ylabel(p["ylabel"], fontsize=font_size)
        if p.get("xlim"):
            ax.set_xlim(*p["xlim"])
        if p.get("ylim"):
            ax.set_ylim(*p["ylim"])
        ax.tick_params(labelsize=font_size - 0.5, direction="in", top=True, right=True)
        ax.grid(alpha=0.18, lw=0.5, zorder=0)
        ax.set_axisbelow(True)

        # 面板标签（顶会惯例：左上角外，粗体）
        _mark(ax.text(-0.16, 1.06, "abcdefgh"[i], transform=ax.transAxes,
                      fontsize=font_size + 2.2, fontweight="bold", va="bottom", ha="left"),
              "panel-tag")

        # 面板结论（claim）放在面板上方，小字、灰色，避免与轴标题冲突
        if p.get("claim"):
            _mark(ax.set_title(p["claim"], fontsize=font_size - 0.8, color="#333333", pad=4),
                  "title")

        # 显著性标注
        for ann in p.get("annotate", []) or []:
            _mark(ax.text(ann["x"], ann["y"], ann["text"], fontsize=font_size - 1.4,
                          ha=ann.get("ha", "center"), va=ann.get("va", "bottom"),
                          color="#1A1A1A"), "annotation")

        if handles and share_legend and not legend_done:
            ax.legend(handles=handles, frameon=False, fontsize=font_size - 1.0,
                      loc="best", handlelength=1.6, borderaxespad=0.3)
            legend_done = True
        elif handles and not share_legend:
            ax.legend(frameon=False, fontsize=font_size - 1.0, loc="best")

    for j in range(n, len(axes)):
        axes[j].axis("off")

    fig.tight_layout(pad=0.6, h_pad=1.4, w_pad=1.2)
    _export(fig, outdir, name, lang=lang, labels=labels,
            narrative_role=narrative_role, takeaway=takeaway)
    plt.close(fig)
    return {fmt: os.path.join(outdir, f"{name}.{fmt}") for fmt in ("pdf", "svg", "png")}


# =========================================================================== #
# 原型三：主实验大表（comparison table）
# =========================================================================== #

def comparison_table(
    rows: list[dict],
    columns: list[str],
    *,
    outdir: str,
    name: str,
    caption_key: str = "method",
    highlight: str = "min",          # 'min' 或 'max'：哪个方向的数值算"最好"
    bold_best: bool = True,
    italic_second: bool = True,
    group_rows: dict[str, list[str]] | None = None,
    lang: str = "zh",
    labels: bool = True,
    narrative_role: str = "",
    takeaway: str = "",
) -> dict[str, str]:
    """主实验大表：行=方法，列=指标，自动 mean±std 排版与最优加粗。

    row 字典字段
    ------------
    method : 行名（方法名）
    <col>  : 该列的值。支持三种形态：
               - 数值  → 直接显示
               - (mean, std) 元组 → 显示为 `mean±std`，并按 mean 参与最优判定
               - 字符串 → 原样显示（如 'N/A'、'—'），不参与最优判定
    sig : 可选，显著性角标，如 '***'，会附在第一个指标列后
    note : 可选，行注

    自动保证：三线表、数值右对齐、最优加粗、次优斜体、单位写进表头。
    """
    import csv
    import io as _io

    pal = SemanticPalette()
    # 数值解析
    def parse(v):
        if isinstance(v, (tuple, list)) and len(v) == 2:
            return float(v[0]), float(v[1]), f"{v[0]:g}$\\pm${v[1]:g}"
        if isinstance(v, (int, float)):
            return float(v), None, f"{v:g}"
        return None, None, str(v)

    parsed = []
    for r in rows:
        pr = {"_method": r[caption_key], "_sig": r.get("sig", ""), "_note": r.get("note", "")}
        for c in columns:
            pr[c] = parse(r.get(c))
        parsed.append(pr)

    # 每个数值列**统一小数位数**，位数取"作者在该列里已经给出的最细精度"。
    #
    # 实测缺陷：原来用 `%g` 格式化，它把末尾的 0 丢掉，同一列会出现
    # `426.7±6` 与 `223.2±15.6` —— 同一个量、同一种精度，一个一位小数一个没有。
    #
    # 第一版修法按**数量级**取位数（≥10 取 1 位、≥1 取 2 位…），结果**改坏了**三处：
    #   * 计数列（re-decision 的 0）被写成 `0.000` —— 计数不该有小数；
    #   * 比值列 1.467/2.803 被压成 1.47/2.80 —— 丢掉作者给的精度；
    #   * 下界 152.21 被压成 152.2。
    # 按数量级猜位数是错的：**精度是作者的意图，不是由数值大小推出来的**。
    # 现在改为读入参自己的小数位（`repr` 里小数点后的位数）取列内最大值，
    # 于是计数列保持整数、比值列保持 3 位、时间列按作者给的位数统一。
    def _input_decimals(v: float) -> int:
        s = repr(float(v))
        if "e" in s or "E" in s:      # 科学计数法：按有效位保守给 3 位
            return 3
        return len(s.split(".")[1]) if "." in s else 0

    col_dec: dict[str, int] = {}
    for c in columns:
        ds = []
        for p in parsed:
            mean, std, _txt = p[c]
            if mean is None:
                continue
            ds.append(_input_decimals(mean))
            if std is not None:
                ds.append(_input_decimals(std))
        col_dec[c] = max(ds) if ds else 0

    for p in parsed:
        for c in columns:
            mean, std, txt = p[c]
            if mean is None:
                continue
            d = col_dec[c]
            if std is None:
                p[c] = (mean, None, f"{mean:.{d}f}")
            else:
                p[c] = (mean, std, f"{mean:.{d}f}$\\pm${std:.{d}f}")

    best_second: dict[str, tuple] = {}
    for c in columns:
        vals = sorted({p[c][0] for p in parsed if p[c][0] is not None},
                      reverse=(highlight == "max"))
        # 补齐到两个元素：某列可能全是 'N/A' 这类非数值，此时没有任何"最优"可判
        best_second[c] = (vals[0] if len(vals) > 0 else None,
                          vals[1] if len(vals) > 1 else None)

    # 生成 LaTeX 三线表（交付到正文）+ PDF 预览（给人看）
    # 英文模式换英文 caption 说明；中文模式的字符串逐字节不变。
    caption_note = ("（最优加粗，次优斜体）" if lang != "en"
                    else " (best in bold, second best in italics)")
    lines = [
        r"\begin{table}[H]", r"  \centering",
        rf"  \caption{{{name.replace('_', ' ')}{caption_note}}}",
        # 去掉冗余前缀：name="tab_main" 原来会生成 `\label{tab:tab_main}`，
        # 引用时得写 \Cref{tab:tab_main}——重复的 tab 前缀是明显的笔误级 papercut。
        # 现在 name 已带前缀就不再叠加，文件仍叫 tab_main.tex（文件名保持可读）。
        rf"  \label{{tab:{name[4:] if name.startswith('tab_') else name}}}",
        r"  \begin{tabular}{l" + "c" * len(columns) + "}",
        r"    \toprule",
        "    " + " & ".join([caption_key] + columns) + r" \\",
        r"    \midrule",
    ]
    for p in parsed:
        cells = []
        for c in columns:
            mean, std, txt = p[c]
            if mean is None:
                cells.append(txt)
                continue
            b, s = best_second[c]
            if bold_best and mean == b:
                cells.append(r"\textbf{" + txt + "}")
            elif italic_second and s is not None and mean == s and s != b:
                cells.append(r"\textit{" + txt + "}")
            else:
                cells.append(txt)
        if p["_sig"]:
            cells[-1] = cells[-1] + "$^{" + p["_sig"] + "}$"
        lines.append("    " + " & ".join([p["_method"]] + cells) + r" \\")
    lines += [r"    \bottomrule", r"  \end{tabular}", r"\end{table}", ""]

    os.makedirs(outdir, exist_ok=True)
    tex_path = os.path.join(outdir, f"{name}.tex")
    with open(tex_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))

    # CSV：便于核对与复现
    csv_path = os.path.join(outdir, f"{name}.csv")
    buf = _io.StringIO()
    w = csv.writer(buf)
    w.writerow([caption_key] + columns)
    for p in parsed:
        w.writerow([p["_method"]] + [p[c][2] for c in columns])
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())

    # PDF/PNG 预览：把表格渲染成图，便于"逐图读图"验收
    ncol = len(columns) + 1
    fig_w = max(W_DOUBLE, 16 + ncol * 24)
    fig_h = 18 + len(parsed) * 7.5
    fig = plt.figure(figsize=(fig_w * MM_TO_INCH, fig_h * MM_TO_INCH), dpi=300)
    ax = fig.add_axes((0.01, 0.01, 0.98, 0.98)); ax.axis("off")
    ax.set_xlim(0, 100); ax.set_ylim(0, fig_h)

    col_x = np.linspace(4, 94, ncol)
    y0 = fig_h - 8
    _mark(ax.text(col_x[0], y0, caption_key, fontsize=7.6, fontweight="bold",
                  ha="left", va="center"), "table-header")
    for j, c in enumerate(columns):
        _mark(ax.text(col_x[j + 1], y0, c, fontsize=7.6, fontweight="bold",
                      ha="center", va="center"), "table-header")
    ax.plot([3, 97], [y0 - 2.2, y0 - 2.2], color="black", lw=1.1)
    for i, p in enumerate(parsed):
        y = y0 - 6.2 - i * 6.2
        _mark(ax.text(col_x[0], y, p["_method"], fontsize=7.2, ha="left", va="center"),
              "table-cell")
        for j, c in enumerate(columns):
            mean, std, txt = p[c]
            weight = "normal"
            style = "normal"
            b, s = best_second[c]
            if mean is not None:
                if bold_best and mean == b:
                    weight = "bold"
                elif italic_second and s is not None and mean == s and s != b:
                    style = "italic"
            lab = txt.replace(r"$\pm$", "±")
            if j == len(columns) - 1 and p["_sig"]:
                lab += p["_sig"]
            _mark(ax.text(col_x[j + 1], y, lab, fontsize=7.0, ha="center", va="center",
                          fontweight=weight, fontstyle=style), "table-cell")
    ax.plot([3, 97], [y0 - 6.2 - len(parsed) * 6.2 + 2.6] * 2, color="black", lw=1.1)

    written = _export(fig, outdir, name, lang=lang, labels=labels,
                      narrative_role=narrative_role, takeaway=takeaway)
    plt.close(fig)
    out = {"tex": tex_path, "csv": csv_path,
           "pdf": os.path.join(outdir, f"{name}.pdf"),
           "svg": os.path.join(outdir, f"{name}.svg"),
           "png": os.path.join(outdir, f"{name}.png")}
    if written.get("labels.json"):
        out["labels_json"] = written["labels.json"]
        out["labels_csv"] = written.get("labels.csv", "")
    return out


# =========================================================================== #
# 原型四：消融 / 排列组合矩阵
# =========================================================================== #

def ablation_matrix(
    matrix: np.ndarray,
    row_labels: list[str],
    col_labels: list[str],
    *,
    outdir: str,
    name: str,
    metric: str = "T / s",
    lower_is_better: bool = True,
    baseline: tuple[int, int] | None = None,
    width_mm: float = W_1_5,
    lang: str = "zh",
    labels: bool = True,
    narrative_role: str = "",
    takeaway: str = "",
) -> dict[str, str]:
    """消融/排列组合矩阵：行=组件或配置轴，列=超参或环境轴，格内为指标值。

    顶会惯例：矩阵右上角或下方给"贡献差值列"——相对完整模型的退化幅度。
    本函数自动计算每行相对基准格（`baseline`，默认 [0,0]）的退化百分比，
    以文本形式标在格内第二行。
    """
    M = np.asarray(matrix, dtype=float)
    base = baseline or (0, 0)
    b = M[base]
    dev = (M - b) / b * 100.0 if b != 0 else np.zeros_like(M)

    fig, ax = plt.subplots(figsize=(width_mm * MM_TO_INCH, (len(row_labels) * 9 + 22) * MM_TO_INCH), dpi=300)
    cmap = "RdYlGn_r" if lower_is_better else "RdYlGn"
    im = ax.imshow(M, aspect="auto", cmap=cmap)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label(metric, fontsize=7.5)
    cb.ax.tick_params(labelsize=6.8)

    ax.set_xticks(np.arange(len(col_labels))); ax.set_xticklabels(col_labels, fontsize=7.5)
    ax.set_yticks(np.arange(len(row_labels))); ax.set_yticklabels(row_labels, fontsize=7.5)
    ax.tick_params(direction="in", top=True, right=True)

    lo, hi = np.nanmin(M), np.nanmax(M)
    for r in range(M.shape[0]):
        for c in range(M.shape[1]):
            v, d = M[r, c], dev[r, c]
            dark = (v - lo) / (hi - lo + 1e-12) > 0.62
            _mark(ax.text(c, r - 0.16, f"{v:g}", ha="center", va="center", fontsize=7.6,
                          color="white" if dark else "black", fontweight="bold"), "data-label")
            _mark(ax.text(c, r + 0.24, f"{d:+.1f}%", ha="center", va="center", fontsize=6.6,
                          color="white" if dark else "#333333"), "data-label")

    # 标注基准格
    ax.add_patch(mpl.patches.Rectangle(
        (base[1] - 0.5, base[0] - 0.5), 1, 1, fill=False, edgecolor="#0F4D92", lw=1.8, zorder=5))
    _mark(ax.text(base[1], base[0] - 0.44, "基准" if lang != "en" else "baseline",
                  ha="center", va="top", fontsize=6.4, color="#0F4D92", zorder=6), "annotation")

    fig.tight_layout(pad=0.5)
    _export(fig, outdir, name, lang=lang, labels=labels,
            narrative_role=narrative_role, takeaway=takeaway)
    plt.close(fig)
    return {fmt: os.path.join(outdir, f"{name}.{fmt}") for fmt in ("pdf", "svg", "png")}


# =========================================================================== #
# 公共导出（含文字台账）
# =========================================================================== #

def _export(
    fig: plt.Figure,
    outdir: str,
    name: str,
    *,
    formats: tuple[str, ...] = ("pdf", "svg", "png"),
    lang: str = "zh",
    labels: bool = True,
    narrative_role: str = "",
    takeaway: str = "",
    reproducible: bool = False,
) -> dict[str, str]:
    """统一导出：PDF（矢量）+ SVG（可编辑）+ PNG（300 dpi）+ 文字台账。

    ``labels=True`` 时额外写出 ``<name>.labels.json`` / ``<name>.labels.csv``
    （并把内容合并进 outdir 下的 ``labels.json`` / ``labels.csv``）。
    台账在 savefig **之前**建立——它同时负责给 SVG 元素打 ``id``，
    这样用户在矢量软件里可以直接按 id 搜索元素。
    """
    os.makedirs(outdir, exist_ok=True)
    written: dict[str, str] = {}
    ledger: dict[str, str] = {}
    if labels:
        try:
            ledger = export_label_ledger(
                fig, outdir, name, fig_id=name, lang=lang,
                narrative_role=narrative_role, takeaway=takeaway, verbose=False,
                reproducible=reproducible,
            )
        except Exception as exc:  # noqa: BLE001
            if reproducible:
                raise
            # 图本身是主交付物，台账失败不该拖死它；但必须**大声**报出来
            print(f"[archetype] ⚠ 文字台账写出失败（{name}）："
                  f"{type(exc).__name__}: {exc}")
    for fmt in formats:
        p = os.path.join(outdir, f"{name}.{fmt}")
        kw = dict(bbox_inches="tight", facecolor="white")
        if fmt == "png":
            kw["dpi"] = 300
        if reproducible:
            if fmt == "pdf":
                kw["metadata"] = {"CreationDate": None, "ModDate": None}
            elif fmt == "svg":
                kw["metadata"] = {"Date": None}
        with mpl.rc_context({"svg.hashsalt": name} if reproducible else {}):
            fig.savefig(p, format=fmt, **kw)
        if reproducible and fmt == "svg":
            # Matplotlib path serialization appends spaces; keep repository diffs clean.
            with open(p, encoding="utf-8") as fh:
                svg = fh.read()
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(line.rstrip() for line in svg.splitlines()) + "\n")
        written[fmt] = p
    print(f"[archetype] {name}: " + ", ".join(
        f"{f}={os.path.getsize(p):,}B" for f, p in written.items()))
    if ledger:
        print(f"[archetype] {name}: 文字台账 " + ", ".join(
            f"{os.path.basename(p)}={os.path.getsize(p):,}B" for p in ledger.values()))
    written.update(ledger)
    return written


# =========================================================================== #
# 文字台账（labels.json / labels.csv）—— 交付给"人工重绘矢量图"的一侧
# =========================================================================== #
#
# 为什么要有它：图最终会被人在专业矢量软件里重画，图内文字会被**重新打字**。
# 于是"图里的字"与"正文里的字"极易漂移：同一个量在图里叫 Queue length、
# 在正文里叫 queueing backlog；首字母大小写、单复数、连字符也各不相同。
# 台账把每张图的每一段文字变成一行数据（角色 + 坐标 + 字体属性），
# 让"照抄术语"变成一次 diff，而不是靠眼睛。

#: 台账 role 列的取值域（语义见 :data:`LABEL_ROLE_DOC`）
LABEL_ROLES: tuple[str, ...] = (
    "title",          # 面板/图内标题行
    "panel-tag",      # 面板编号 a / b / c
    "axis-x",         # x 轴标题
    "axis-y",         # y 轴标题
    "tick",           # 刻度标签 / 轴偏移量（机器生成的数字）
    "legend",         # 图例条目
    "legend-title",   # 图例标题
    "node",           # 方法图里的模块框文字
    "lane-label",     # 方法图左侧竖排层标题
    "data-label",     # 由代码算出来的数值标注（别手抄，会抄错）
    "colorbar-label",  # 色标轴标题
    "annotation",     # 编辑性文字：箭头标签、显著性星号、引出说明
    "table-header",   # 表格表头
    "table-cell",     # 表格单元
    "text",           # 以上都不是
)

#: role → 人话解释（写进 labels.json 的 role_vocabulary，供用户核对）
LABEL_ROLE_DOC: dict[str, str] = {
    "title": "axes/panel title line printed inside the figure",
    "panel-tag": "panel letter a/b/c",
    "axis-x": "x-axis label",
    "axis-y": "y-axis label",
    "tick": "tick label or axis offset text (machine-generated numbers)",
    "legend": "legend entry",
    "legend-title": "legend title",
    "node": "module/box text in a method figure",
    "lane-label": "rotated layer/lane label in the left gutter",
    "data-label": "numeric value printed by the code (never retype by hand)",
    "colorbar-label": "colorbar axis label",
    "annotation": "editorial text: arrow labels, callouts, significance marks",
    "table-header": "table header cell",
    "table-cell": "table body cell",
    "text": "anything not classified above",
}

#: CSV 列序；JSON 里每个 label 对象用同一组键（两处一一对应）
LABEL_COLUMNS: tuple[str, ...] = (
    "fig_id", "lang", "narrative_role", "takeaway",
    "label_id", "svg_id", "role", "text",
    "pos_system", "page_w_pt", "page_h_pt",
    "center_x_pt", "center_y_pt", "anchor_x_pt", "anchor_y_pt",
    "width_pt", "height_pt", "x_frac", "y_frac",
    "axes_id", "axes_frac_x", "axes_frac_y", "data_x", "data_y",
    "fontsize", "fontfamily", "fontweight", "fontstyle",
    "rotation", "ha", "va", "color", "math", "n_lines", "font_file",
)


def _pos_system_text(pad: float) -> str:
    return (
        "page-points, origin = BOTTOM-LEFT of the exported page; "
        f"page = matplotlib tight bbox of the figure + savefig.pad_inches ({pad:g} in) per side "
        "(the page matplotlib actually writes for bbox_inches='tight'). "
        "center_x_pt/center_y_pt = centre of the rendered text bbox; "
        "anchor_x_pt/anchor_y_pt = matplotlib text anchor (equals the SVG/PDF text x/y only "
        "for va='baseline', otherwise it differs by the ascent/descent, a few pt); "
        "x_frac/y_frac = the centre as a 0-1 fraction of that page."
    )


def _r(v, nd: int = 3):
    if v is None:
        return None
    try:
        return round(float(v), nd)
    except Exception:  # noqa: BLE001
        return None


def collect_labels(
    fig: plt.Figure,
    *,
    fig_id: str = "",
    lang: str = "zh",
    stamp_ids: bool = False,
    pad: float | None = None,
) -> list[dict]:
    """遍历图内**所有**文字，产出文字台账行（角色 + 位置 + 字体属性）。

    位置统一是"导出页面的 points"（见 :func:`_pos_system_text`），与
    ``savefig(bbox_inches='tight')`` 实际写出的 PDF/SVG 页面坐标系一致，
    因此可以直接在 Illustrator / Inkscape 里按 pt 定位，或按 ``svg_id`` 搜索元素。

    ``stamp_ids=True`` 时给每个 Text 挂上唯一的 ``gid``（导出 SVG 后该 id 出现在
    包住 ``<text>`` 的 ``<g>`` 上），并把同一个 id 写进台账的 ``svg_id`` 列。
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    if pad is None:
        pad = float(mpl.rcParams.get("savefig.pad_inches", 0.1))
    tb = fig.get_tightbbox(renderer)
    page_w_pt = (tb.width + 2 * pad) * 72.0
    page_h_pt = (tb.height + 2 * pad) * 72.0
    pos_system = _pos_system_text(pad)

    font_file = ""
    try:
        font_file = resolved_font_path()
    except Exception:  # noqa: BLE001
        font_file = ""

    role_by_id: dict[int, str] = {}
    tick_ids: set[int] = set()
    axes_id: dict[int, str] = {}
    for ai, ax in enumerate(fig.axes):
        axes_id[id(ax)] = f"ax{ai}"
        is_cb = (getattr(ax, "_colorbar", None) is not None
                 or ax.get_label() == "<colorbar>")
        try:
            for t in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
                tick_ids.add(id(t))
        except Exception:  # noqa: BLE001
            pass
        for axis in (ax.xaxis, ax.yaxis):
            try:
                tick_ids.add(id(axis.get_offset_text()))
            except Exception:  # noqa: BLE001
                pass
        for t in (getattr(ax, "title", None), getattr(ax, "_left_title", None),
                  getattr(ax, "_right_title", None)):
            if t is not None and t.get_text().strip():
                role_by_id[id(t)] = "title"
        try:
            if ax.xaxis.get_label().get_text().strip():
                role_by_id[id(ax.xaxis.get_label())] = "colorbar-label" if is_cb else "axis-x"
            if ax.yaxis.get_label().get_text().strip():
                role_by_id[id(ax.yaxis.get_label())] = "colorbar-label" if is_cb else "axis-y"
        except Exception:  # noqa: BLE001
            pass
        leg = ax.get_legend()
        if leg is not None:
            for t in leg.get_texts():
                role_by_id[id(t)] = "legend"
            lt = leg.get_title()
            if lt is not None and lt.get_text().strip():
                role_by_id[id(lt)] = "legend-title"

    raw: list[dict] = []
    for t in fig.findobj(mpl.text.Text):
        try:
            s = t.get_text()
        except Exception:  # noqa: BLE001
            continue
        if not s or not s.strip():
            continue
        try:
            if not t.get_visible():
                continue
        except Exception:  # noqa: BLE001
            pass
        ax = getattr(t, "axes", None)
        if ax is not None:
            try:
                if not ax.get_visible():
                    continue
            except Exception:  # noqa: BLE001
                pass

        role = getattr(t, "_csf_role", None)
        if role not in LABEL_ROLES:
            role = role_by_id.get(id(t))
        if role is None and id(t) in tick_ids:
            if ax is not None and not getattr(ax, "axison", True):
                continue
            role = "tick"
        if role is None:
            role = "annotation" if ax is not None else "text"

        bb = None
        try:
            bb = t.get_window_extent(renderer=renderer)
        except Exception:  # noqa: BLE001
            bb = None
        disp = None
        try:
            disp = t.get_transform().transform(t.get_position())
        except Exception:  # noqa: BLE001
            disp = None

        def to_pt(xd: float, yd: float) -> tuple[float, float]:
            return ((xd / fig.dpi - tb.x0 + pad) * 72.0,
                    (yd / fig.dpi - tb.y0 + pad) * 72.0)

        if bb is not None:
            cx_pt, cy_pt = to_pt(bb.x0 + bb.width / 2.0, bb.y0 + bb.height / 2.0)
            w_pt = bb.width / fig.dpi * 72.0
            h_pt = bb.height / fig.dpi * 72.0
        else:
            cx_pt = cy_pt = w_pt = h_pt = None
        if disp is not None:
            an_pt = to_pt(disp[0], disp[1])
        else:
            an_pt = (None, None)

        af: tuple = (None, None)
        dc: tuple = (None, None)
        if ax is not None and disp is not None:
            try:
                p = ax.transAxes.inverted().transform(disp)
                af = (_r(p[0], 4), _r(p[1], 4))
            except Exception:  # noqa: BLE001
                pass
            try:
                if t.get_transform() is ax.transData:
                    p = ax.transData.inverted().transform(disp)
                    dc = (_r(p[0], 5), _r(p[1], 5))
            except Exception:  # noqa: BLE001
                pass

        try:
            fam = ",".join(t.get_fontfamily())
        except Exception:  # noqa: BLE001
            fam = ""
        row = {
            "fig_id": fig_id,
            "lang": lang,
            "narrative_role": "",
            "takeaway": "",
            "label_id": "",
            "svg_id": "",
            "role": role,
            "text": s,
            "pos_system": pos_system,
            "page_w_pt": _r(page_w_pt),
            "page_h_pt": _r(page_h_pt),
            "center_x_pt": _r(cx_pt),
            "center_y_pt": _r(cy_pt),
            "anchor_x_pt": _r(an_pt[0]),
            "anchor_y_pt": _r(an_pt[1]),
            "width_pt": _r(w_pt),
            "height_pt": _r(h_pt),
            "x_frac": _r((cx_pt / page_w_pt) if (cx_pt is not None and page_w_pt) else None, 4),
            "y_frac": _r((cy_pt / page_h_pt) if (cy_pt is not None and page_h_pt) else None, 4),
            "axes_id": axes_id.get(id(ax), "") if ax is not None else "",
            "axes_frac_x": af[0],
            "axes_frac_y": af[1],
            "data_x": dc[0],
            "data_y": dc[1],
            "fontsize": _r(t.get_fontsize(), 2),
            "fontfamily": fam,
            "fontweight": str(t.get_fontweight()),
            "fontstyle": str(t.get_fontstyle()),
            "rotation": _r(t.get_rotation(), 2),
            "ha": str(t.get_ha()),
            "va": str(t.get_va()),
            "color": str(t.get_color()),
            "math": bool("$" in s),
            "n_lines": s.count("\n") + 1,
            "font_file": font_file,
        }
        row["_artist"] = t
        raw.append(row)

    order = {r: i for i, r in enumerate(LABEL_ROLES)}
    raw.sort(key=lambda r: (order.get(r["role"], 99),
                            -(r["center_y_pt"] if r["center_y_pt"] is not None else 0.0),
                            (r["center_x_pt"] if r["center_x_pt"] is not None else 0.0)))
    import re as _re
    slug = _re.sub(r"[^0-9A-Za-z_-]+", "-", fig_id or "fig").strip("-") or "fig"
    for i, row in enumerate(raw, start=1):
        row["label_id"] = f"{fig_id or slug}:{i:03d}"
        row["svg_id"] = f"csf-{slug}-{row['role']}-{i:03d}"
        artist = row.pop("_artist", None)
        if stamp_ids and artist is not None:
            try:
                artist.set_gid(row["svg_id"])
            except Exception:  # noqa: BLE001
                pass
    return raw


def _write_csv(path: str, rows: list[dict]) -> None:
    # utf-8-sig：中文标签用 Excel 直接打开不乱码
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(LABEL_COLUMNS), extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _read_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            return [dict(r) for r in csv.DictReader(fh)]
    except Exception:  # noqa: BLE001
        return []


def _read_json(path: str):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


def export_label_ledger(
    fig: plt.Figure,
    outdir: str,
    name: str,
    *,
    fig_id: str | None = None,
    lang: str = "zh",
    narrative_role: str = "",
    takeaway: str = "",
    stamp_ids: bool = True,
    aggregate: bool = True,
    verbose: bool = True,
    reproducible: bool = False,
) -> dict[str, str]:
    """写出"图内文字台账"：``<name>.labels.json`` + ``<name>.labels.csv``。

    参数
    ----
    fig : 已画好的 Figure（本函数会 ``canvas.draw()`` 取渲染后的坐标）。
    outdir / name : 与图同目录、同前缀。
    fig_id : 台账里用哪张图的 id（默认用 ``name``）。
    lang : ``'zh'`` / ``'en'``，写进台账便于按语言筛选。
    narrative_role / takeaway : 该图在论证链里的角色与要读出的一句话结论
        （取自 ``csf_narrative`` 的 Claim / figure_ledger 字段，但由调用方传入，
        本模块不 import 该模块，避免与其门禁逻辑耦合）。
    stamp_ids : 是否把每段文字的 id 写进 SVG（``<g id="csf-...">``），
        便于在矢量软件里按 id 搜索元素。
    aggregate : 是否把本次结果合并进 outdir 的 ``labels.json`` / ``labels.csv``
        （同一 fig_id 的旧行会被替换），便于全篇术语一次性核对。

    返回 ``{"labels.json": ..., "labels.csv": ...}`` 路径表。
    """
    fid = fig_id or name
    rows = collect_labels(fig, fig_id=fid, lang=lang, stamp_ids=stamp_ids)
    for row in rows:
        row["narrative_role"] = narrative_role
        row["takeaway"] = takeaway

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["role"]] = counts.get(row["role"], 0) + 1

    os.makedirs(outdir, exist_ok=True)
    json_path = os.path.join(outdir, f"{name}.labels.json")
    csv_path = os.path.join(outdir, f"{name}.labels.csv")
    payload = {
        "figure_id": fid,
        "name": name,
        "lang": lang,
        "narrative_role": narrative_role,
        "takeaway": takeaway,
        "generated": None if reproducible else datetime.now().astimezone().isoformat(timespec="seconds"),
        "n_labels": len(rows),
        "role_counts": counts,
        "pos_system": rows[0]["pos_system"] if rows else _pos_system_text(
            float(mpl.rcParams.get("savefig.pad_inches", 0.1))),
        "font_file": rows[0]["font_file"] if rows else "",
        "svg_fonttype": str(mpl.rcParams.get("svg.fonttype", "")),
        "pdf_fonttype": int(mpl.rcParams.get("pdf.fonttype", 0) or 0),
        "label_columns": list(LABEL_COLUMNS),
        "role_vocabulary": LABEL_ROLE_DOC,
        "labels": rows,
    }
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    _write_csv(csv_path, rows)
    written = {"labels.json": json_path, "labels.csv": csv_path}

    if aggregate:
        agg_json = os.path.join(outdir, "labels.json")
        agg_csv = os.path.join(outdir, "labels.csv")
        prev = _read_json(agg_json)
        figures = dict(prev.get("figures", {})) if isinstance(prev, dict) else {}
        figures[fid] = payload
        total = sum(int(v.get("n_labels", len(v.get("labels", []))))
                    for v in figures.values() if isinstance(v, dict))
        agg = {
            "ledger": "aggregate",
            "generated": None if reproducible else datetime.now().astimezone().isoformat(timespec="seconds"),
            "n_figures": len(figures),
            "n_labels": total,
            "role_vocabulary": LABEL_ROLE_DOC,
            "label_columns": list(LABEL_COLUMNS),
            "figures": figures,
        }
        with open(agg_json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(agg, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        old_rows = [r for r in _read_csv(agg_csv) if r.get("fig_id") != fid]
        _write_csv(agg_csv, old_rows + rows)
        written["aggregate_labels.json"] = agg_json
        written["aggregate_labels.csv"] = agg_csv

    if verbose:
        print(f"[ledger] {name}: {len(rows)} 条文字 → {os.path.basename(json_path)}"
              f" / {os.path.basename(csv_path)}  roles={counts}")
    return written


# =========================================================================== #
# 标注自动避让（根治"标签互相压住"）
# =========================================================================== #

def place_labels(
    ax,
    anchors: list[tuple[float, float]],
    texts: list[str],
    *,
    fontsize: float = 7.5,
    box_w_units: float | None = None,
    box_h_units: float | None = None,
    data_points: np.ndarray | None = None,
    density_radius: float | None = None,
    avoid_radius: float = 0.0,
    color: str = "#1A1A1A",
    marker_color: str = "#0F4D92",
    zorder: int = 7,
) -> list[tuple[float, float]]:
    """在坐标区内为每个锚点自动挑选不冲突的标签位置。

    为什么需要它：实测中手工指定偏移连续三轮都失败——第一轮 S3/S4 重叠，
    第二轮标签跑到轴外把画布撑宽，第三轮 S2/S1、S3/S4 又互相压住。
    **"手摆标签"是结构性错误**：标签冲突是全局约束满足问题，
    必须由算法在候选位里做碰撞检测。

    策略
    ----
    对每个锚点按"由近及远、由右上到左下"的固定顺序枚举候选位，
    选第一个满足以下全部条件的位置：
      1) 标签框整体落在坐标区内部（不撑宽画布）；
      2) 与已放置的标签框不相交；
      3) 不与数据点密集区相交（若给了 `data_points`，用格点占用近似）；
      4) 与锚点本身距离不超过 `avoid_radius` 的上限（避免离得太远看不出归属）。

    返回实际使用的位置列表（与 `anchors` 同序）。
    """
    import numpy as _np

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    span_x, span_y = x1 - x0, y1 - y0

    # 估算一个标签框在数据坐标下的尺寸（按最长行、两行计）
    if box_w_units is None:
        maxlen = max((sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in t.split("\n")[0])
                      for t in texts), default=12.0)
        box_w_units = maxlen * fontsize * span_x / (72.0 * 3.2)
    if box_h_units is None:
        box_h_units = 2.3 * fontsize * span_y / (72.0 * 3.2)

    # 数据点占用网格（把点云粗粒化成占位集合）
    occupied: set[tuple[int, int]] = set()
    GNX, GNY = 48, 48
    if data_points is not None and len(data_points):
        r = density_radius if density_radius is not None else min(span_x, span_y) * 0.02
        gi = _np.clip(((data_points[:, 0] - x0) / span_x * GNX).astype(int), 0, GNX - 1)
        gj = _np.clip(((data_points[:, 1] - y0) / span_y * GNY).astype(int), 0, GNY - 1)
        cell = _np.zeros((GNX, GNY), dtype=int)
        for a, b in zip(gi, gj):
            cell[a, b] = 1
        # 膨胀一格，使标签不贴点
        for a in range(GNX):
            for b in range(GNY):
                if cell[a, b]:
                    for da in (-1, 0, 1):
                        for db in (-1, 0, 1):
                            ia, ib = a + da, b + db
                            if 0 <= ia < GNX and 0 <= ib < GNY:
                                occupied.add((ia, ib))

    def box_rect(cx: float, cy: float) -> tuple[float, float, float, float]:
        return (cx - box_w_units / 2, cy - box_h_units / 2,
                cx + box_w_units / 2, cy + box_h_units / 2)

    def rect_free(rect) -> bool:
        ax0, ay0, ax1, ay1 = rect
        if ax0 < x0 + 0.01 * span_x or ax1 > x1 - 0.01 * span_x:
            return False
        if ay0 < y0 + 0.01 * span_y or ay1 > y1 - 0.01 * span_y:
            return False
        ia0 = int((ax0 - x0) / span_x * GNX); ia1 = int((ax1 - x0) / span_x * GNX)
        ib0 = int((ay0 - y0) / span_y * GNY); ib1 = int((ay1 - y0) / span_y * GNY)
        for a in range(max(ia0, 0), min(ia1 + 1, GNX)):
            for b in range(max(ib0, 0), min(ib1 + 1, GNY)):
                if (a, b) in occupied:
                    return False
        return True

    def overlap(r1, r2) -> bool:
        return not (r1[2] <= r2[0] or r2[2] <= r1[0] or r1[3] <= r2[1] or r2[3] <= r1[1])

    placed: list[tuple[float, float, float, float]] = []
    out: list[tuple[float, float]] = []

    # 候选方向：单位偏移 × 由近及远的距离
    directions = [(1, 0), (0, 1), (1, 1), (-1, 1), (1, -1), (-1, 0), (0, -1), (-1, -1)]
    dists = [0.055, 0.10, 0.16, 0.24, 0.34, 0.46, 0.60]

    for (ax_, ay_), t in zip(anchors, texts):
        chosen = None
        for d in dists:
            for ux, uy in directions:
                # 水平/垂直对齐由方向决定：标签框整体放在锚点外侧
                cx = ax_ + ux * (d * span_x + box_w_units / 2)
                cy = ay_ + uy * (d * span_y + box_h_units / 2)
                rect = box_rect(cx, cy)
                if not rect_free(rect):
                    continue
                if any(overlap(rect, p) for p in placed):
                    continue
                if avoid_radius and math.hypot(cx - ax_, cy - ay_) > avoid_radius:
                    continue
                chosen = (cx, cy, rect)
                break
            if chosen:
                break
        if chosen is None:                        # 全部候选都冲突则退回锚点上方
            cx, cy = ax_, ay_ + box_h_units
            chosen = (cx, cy, box_rect(cx, cy))
        placed.append(chosen[2])
        out.append((chosen[0], chosen[1]))

        ax.plot([ax_, chosen[0]], [ay_, chosen[1]], color=marker_color,
                lw=0.6, ls="-", alpha=0.55, zorder=zorder - 1)
        _mark(ax.text(chosen[0], chosen[1], t, fontsize=fontsize, color=color,
                      ha="center", va="center", zorder=zorder, linespacing=1.45,
                      bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="#CFCECE",
                                lw=0.6, alpha=0.93)), "annotation")
    return out
