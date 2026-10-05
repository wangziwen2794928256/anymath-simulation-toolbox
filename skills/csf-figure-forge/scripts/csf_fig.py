"""csf_fig —— 顶刊/顶会风格出图底座（A 赛道多智能体仿真论文专用）

设计目标（针对已实测的四类成图缺陷）：
  1. 中文字体被样式表锁死 → 全图豆腐块 □
     → `use_style()` 封装 SciencePlots + 强制接管字体族 + 缺字即报错
  2. 同一张图里颜色语义自相矛盾（红=基线 又 红=静态）
     → `SemanticPalette` 单一事实来源，一个角色一个颜色，越界即报错
  3. 手摆坐标导致文字溢出框外、箭头斜穿文字
     → `draw_box()` 自动按文本长度撑开盒子；`draw_arrow()` 默认锚点吸附到盒边
  4. 矢量/300dpi 双份导出不落地
     → `finalize()` 一次导出 PDF + SVG + PNG(300dpi)

用法见本目录 ../README.md 与 ../references/。
"""

from __future__ import annotations

import glob
import os
import warnings
from dataclasses import dataclass, field

import matplotlib

matplotlib.use("Agg")

import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

__all__ = [
    "SemanticPalette",
    "SEMANTIC",
    "use_style",
    "draw_box",
    "draw_arrow",
    "panel_label",
    "figure_contract_check",
    "finalize",
    "FigSpec",
    "PanelSpec",
    "CJK_FONTS",
    "LATIN_FONTS",
    "LATIN_PREFERRED",
    "register_bundled_latin_fonts",
    "resolved_font_path",
    "verify_font_family",
    "missing_glyph_probe",
    "missing_glyph_report",
    "verify_mathtext",
]

# --------------------------------------------------------------------------- #
# 1. 语义配色：单一事实来源
# --------------------------------------------------------------------------- #

#: 角色 → 颜色。**全篇所有图共用这一张表**，禁止某张图临时换色。
SEMANTIC: dict[str, str] = {
    "ours": "#0F4D92",        # 本文方法（深蓝，主色，最高视觉权重）
    "ours_alt": "#3775BA",    # 本文方法的次要变体
    "baseline": "#7F7F7F",    # 基线/对照（中性灰，不抢戏）
    "baseline_2": "#B0B0B0",  # 第二基线
    "bottleneck": "#D62728",  # 瓶颈/告警/最差
    "improve": "#009E73",     # 改善/有利方向
    "ablation": "#9A4D8E",    # 消融变体
    "reference": "#E69F00",   # 参考值/上界/理论值
    "highlight": "#FFD700",   # 唯一强调点
    "fill_light": "#A6C8E8",  # 低饱和填充
    "grid": "#CFCECE",
    "text": "#1A1A1A",
}


class SemanticPalette:
    """把角色名映射到颜色，并**在越界时报错**，防止各图各配色。

    这是修掉 ``AI图2_复合组图`` 那种"面板 b 红=最近出口、面板 c 红=静态"
    自相矛盾的核心机制：任何角色都必须先在此登记。
    """

    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        self.mapping = dict(mapping or SEMANTIC)
        self._used: dict[str, str] = {}

    def __call__(self, role: str) -> str:
        if role not in self.mapping:
            raise KeyError(
                f"未登记的语义角色 {role!r}。已登记：{sorted(self.mapping)}\n"
                "禁止临时指定颜色——先在此登记角色，保证全篇颜色语义一致。"
            )
        color = self.mapping[role]
        if role in self._used and self._used[role] != color:
            raise ValueError(f"角色 {role!r} 颜色被改动过：{self._used[role]} → {color}")
        self._used[role] = color
        return color

    def series(self, roles: list[str]) -> list[str]:
        return [self(role) for role in roles]

    def conflict_report(self) -> list[str]:
        """同一颜色被多个角色占用的报告（同色=同义才允许）。"""
        by_color: dict[str, list[str]] = {}
        for role, color in self.mapping.items():
            by_color.setdefault(color, []).append(role)
        return [
            f"{color}: {roles}" for color, roles in by_color.items() if len(roles) > 1
        ]


# --------------------------------------------------------------------------- #
# 2. 样式：把 SciencePlots 接进中文论文（已实测的三个坑一次绕开）
# --------------------------------------------------------------------------- #

#: 本机实测齐全的 CJK 字体，按优先级排列
CJK_FONTS: list[str] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans SC",
    "SimSun",
    "DejaVu Sans",
]

#: 英文（Latin）无衬线字体族优先级链。
#:
#: 首选 **Libertinus Sans**：论文 shell
#: ``skills/csf-paper-polish/assets/latex-en/csfstyle-en.sty`` 里四个 fontset
#: （stix / times / libertinus / charter）**都用它做 ``\setsansfont``**，
#: 所以图内英文与正文的 sans 同族。它由 MiKTeX 以"文件名"方式安装、没有被登记进
#: 系统字体库（shell 注释里已经写明 family-name 查找不可靠），因此必须由
#: :func:`register_bundled_latin_fonts` 显式 ``addfont``。
#: 次选 Arial（Windows 系统字体，任何机器都有；TTF，PDF 可嵌 Type 42）。
#: 末位 DejaVu Sans 只是 matplotlib 自带兜底，**解析到它即视为失败**
#: （见 :func:`verify_font_family`）。
LATIN_FONTS: list[str] = [
    "Libertinus Sans",
    "Arial",
    "Helvetica",
    "DejaVu Sans",
]

#: 上表中"必须至少解析成功一个"的候选。DejaVu Sans 是 matplotlib 自带字体，
#: 它解析成功不算数——静默换字是本仓库反复踩过的缺陷类。
LATIN_PREFERRED: tuple[str, ...] = ("Libertinus Sans", "Arial", "Helvetica")

#: 需要显式注册的字体文件（按文件名安装、未进系统字体库）。
#: 先试定向 pattern（快），命中就不再遍历整棵 TeX 树。
BUNDLED_FONT_GLOBS: tuple[str, ...] = (
    "fonts/opentype/**/libertinussans-*.otf",
    "fonts/opentype/**/LibertinusSans-*.otf",
    "fonts/truetype/**/libertinussans-*.ttf",
    "**/libertinussans-regular.otf",
    "**/LibertinusSans-Regular.otf",
)

#: 追加字体搜索根（``os.pathsep`` 分隔）。默认再探 MiKTeX / TeX Live 的常见位置。
FONT_ROOTS_ENV = "CSF_FONT_ROOTS"

_REGISTERED_FONTS: list[str] = []


def _font_roots() -> list[str]:
    """可能存放"按文件名安装"字体的根目录，按优先级排列。"""
    roots: list[str] = []
    for p in os.environ.get(FONT_ROOTS_ENV, "").split(os.pathsep):
        if p.strip():
            roots.append(p.strip())
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    if local:
        roots += [os.path.join(local, "Programs", "MiKTeX"), os.path.join(local, "MiKTeX")]
    if appdata:
        roots.append(os.path.join(appdata, "MiKTeX"))
    for var in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(var, "")
        if base:
            roots.append(os.path.join(base, "MiKTeX"))
    roots += [r"C:\texlive", "/usr/local/texlive", "/usr/share/texlive", "/usr/share/texmf"]
    seen: set[str] = set()
    out: list[str] = []
    for r in roots:
        if r and r not in seen:
            seen.add(r)
            out.append(r)
    return out


def register_bundled_latin_fonts(verbose: bool = False) -> list[str]:
    """把未进系统字体库的 Latin 字体文件注册进 matplotlib，返回注册到的文件。

    幂等：同一个文件只 ``addfont`` 一次。注册失败会**打印**而不是吞掉。
    """
    from matplotlib import font_manager

    found: list[str] = []
    for root in _font_roots():
        if not os.path.isdir(root):
            continue
        hits: list[str] = []
        for pat in BUNDLED_FONT_GLOBS:
            try:
                hits = sorted(glob.glob(os.path.join(root, pat), recursive=True))
            except Exception:  # noqa: BLE001
                hits = []
            if hits:
                break
        if hits:
            found = hits
            break
    for path in found:
        if path in _REGISTERED_FONTS:
            continue
        try:
            font_manager.fontManager.addfont(path)
            _REGISTERED_FONTS.append(path)
            if verbose:
                print(f"[csf_fig] 已注册字体文件：{path}")
        except Exception as exc:  # noqa: BLE001
            print(f"[csf_fig] ⚠ 字体文件注册失败：{path} ({type(exc).__name__}: {exc})")
    if verbose and not found:
        print(f"[csf_fig] 未在 {_font_roots()} 下找到可注册的 Latin 字体文件（改用系统字体）")
    return found


def _resolve_first(chain: list[str]) -> tuple[str | None, str | None]:
    """返回字体链里第一个**真的能解析**的 (family, file)，全都解析不到则 (None, None)。"""
    from matplotlib import font_manager

    for fam in chain:
        try:
            path = font_manager.findfont(
                font_manager.FontProperties(family=fam), fallback_to_default=False
            )
        except Exception:  # noqa: BLE001
            continue
        if path:
            return fam, path
    return None, None


def resolved_font_path(family: str | list[str] | None = None) -> str:
    """解析字体族 → 实际字体文件路径；解析不到就报错（绝不静默换字）。"""
    if family is None:
        chain = [f for f in mpl.rcParams.get("font.sans-serif", []) if f != "sans-serif"]
    elif isinstance(family, str):
        chain = [family]
    else:
        chain = list(family)
    _fam, path = _resolve_first(chain)
    if path is None:
        raise RuntimeError(
            f"[csf_fig] 字体族一个都解析不到：{chain}。拒绝静默退回 DejaVu Sans；"
            "请安装字体、设置 CSF_FONT_ROOTS，或用 latin_fonts= 指定可用字体。"
        )
    return path


def verify_font_family(
    chain: list[str] | None = None,
    *,
    require_preferred: bool = True,
    verbose: bool = True,
) -> tuple[str, str]:
    """确认字体链**真的**解析到某个文件，并返回 ``(family, path)``。

    这是本仓库最贵的一课：matplotlib 在字体缺失时会**静默**换成 DejaVu Sans，
    图看起来"能出"，但字形、字宽、字重全错且无人报警。所以这里：
      1. 走一遍字体链，找到第一个用 ``fallback_to_default=False`` 能解析的族；
      2. 首选候选（:data:`LATIN_PREFERRED`）**全军覆没**时直接抛异常；
      3. 解析成功时把**文件路径**打印出来，让人一眼能核对。
    """
    chain = list(chain if chain is not None else mpl.rcParams.get("font.sans-serif", []))
    prefer = [f for f in chain if f in LATIN_PREFERRED] if require_preferred else []
    fam, path = _resolve_first(chain)
    if path is None:
        raise RuntimeError(
            f"[csf_fig] 英文模式：字体链 {chain} 一个都解析不到。"
            "拒绝静默退回 DejaVu Sans——请安装字体或用 latin_fonts= 指定。"
        )
    if require_preferred and not prefer:
        raise RuntimeError(
            f"[csf_fig] 英文模式：字体链 {chain} 里没有任何首选 Latin 字体"
            f"（{list(LATIN_PREFERRED)}）。若确实要用 DejaVu Sans，"
            "请显式传 latin_fonts=['DejaVu Sans']。"
        )
    if fam == "DejaVu Sans" and prefer:
        raise RuntimeError(
            f"[csf_fig] 英文模式：首选字体 {prefer} 全部解析失败，只剩 matplotlib 自带的 "
            "DejaVu Sans。静默换字是本仓库反复踩过的缺陷，故在此报错。"
            "请安装/注册字体（见 register_bundled_latin_fonts），"
            "或显式传 latin_fonts=['DejaVu Sans'] 表示你接受该降级。"
        )
    if verbose:
        print(f"[csf_fig] lang=en 字体已解析：{fam} → {path}")
    return fam, path


def use_style(
    journal: str = "nature",
    *,
    cjk: bool = True,
    font_size: float | None = None,
    strict_glyphs: bool = True,
    lang: str = "zh",
    latin_fonts: list[str] | None = None,
    verify_fonts: bool = True,
    svg_fonttype: str | None = None,
    pdf_fonttype: int | None = None,
) -> None:
    """应用顶刊样式；中文（``lang='zh'``，默认）与英文（``lang='en'``）两套字体策略。

    参数
    ----
    journal : SciencePlots 期刊样式名（``nature`` / ``ieee``）。
    cjk : 中文模式是否强制接管字体族以支持中文（``lang='en'`` 时忽略）。
    font_size : 图内基准字号（pt）。嵌论文建议 8–9，单独成图 14–16。
    strict_glyphs : 缺字时**报错**而非静默输出豆腐块。
    lang : ``'zh'``（默认，行为与本函数历史版本逐字节一致）或 ``'en'``。
    latin_fonts : 英文模式的字体链；默认 :data:`LATIN_FONTS`。
    verify_fonts : 英文模式下是否强制解析验证字体文件与 mathtext。
    svg_fonttype : ``'none'`` 让 SVG 保留**真 ``<text>``**（可编辑）；默认英文为
        ``'none'``，中文维持 matplotlib 原状以保持向后兼容。
    pdf_fonttype : ``42`` 把 TrueType 真嵌进 PDF；默认英文为 42，中文维持原状。

    说明（三个已实测的坑）
    ----------------------
    * 坑 3：``import scienceplots`` 必须在 ``plt.style.use`` 之前，否则样式未注册。
    * 坑 2：``nature`` 样式默认 ``text.usetex=True``，本机若无 LaTeX 会直接崩，
      故始终叠加 ``no-latex``。
    * 坑 1：``science``/``nature`` 把字体锁成 STIXGeneral，中文必成豆腐块，
      故样式**之后**必须重置 ``font.family`` / ``font.sans-serif``。

    英文模式额外做四件事（都是实测结论，不是偏好）：
      1. 叠加 SciencePlots 自带的 ``sans`` 样式（``font.family=sans-serif``、
         ``mathtext.fontset=dejavusans``）——它不设 ``font.sans-serif``，
         所以**必须**再由我们钉死字体链，否则默认链会静静落到 DejaVu Sans；
      2. 显式注册 MiKTeX 里按文件名安装的 Libertinus Sans，再**验证**解析结果，
         解析不到就报错（见 :func:`verify_font_family`）；
      3. ``axes.unicode_minus=False``：U+2212 在多数图内字体里是缺字方块；
      4. ``svg.fonttype='none'`` + ``pdf.fonttype=42``：矢量文字必须是真文字
         （matplotlib 默认把 SVG 文字转成路径、把 PDF 字体降级成 Type 3）。
    """
    import scienceplots  # noqa: F401  坑 3：先 import 注册样式

    lang = (lang or "zh").strip().lower()
    if lang not in ("zh", "en"):
        raise ValueError(f"use_style(lang=...) 只支持 'zh' / 'en'，收到 {lang!r}")

    styles = ["science", "no-latex"]
    if journal and journal not in ("", "none"):
        styles.insert(1, journal)
    if lang == "en" and "sans" in plt.style.available:
        # SciencePlots 自带的 sans 选项：先吃它的 font.family / mathtext.fontset
        styles.append("sans")
    plt.style.use(styles)

    if lang == "zh":
        if cjk:
            mpl.rcParams["font.family"] = ["sans-serif"]
            mpl.rcParams["font.sans-serif"] = list(CJK_FONTS)
            mpl.rcParams["axes.unicode_minus"] = False
            mpl.rcParams["mathtext.fontset"] = "dejavusans"
    else:
        chain = list(latin_fonts) if latin_fonts else list(LATIN_FONTS)
        if any(f not in ("DejaVu Sans",) for f in chain):
            register_bundled_latin_fonts()
        mpl.rcParams["font.family"] = ["sans-serif"]
        mpl.rcParams["font.sans-serif"] = chain
        mpl.rcParams["axes.unicode_minus"] = False
        mpl.rcParams["mathtext.fontset"] = "dejavusans"
        if svg_fonttype is None:
            svg_fonttype = "none"
        if pdf_fonttype is None:
            pdf_fonttype = 42
        if verify_fonts:
            verify_font_family(chain)

    if svg_fonttype:
        mpl.rcParams["svg.fonttype"] = str(svg_fonttype)
    if pdf_fonttype:
        mpl.rcParams["pdf.fonttype"] = int(pdf_fonttype)
        mpl.rcParams["ps.fonttype"] = int(pdf_fonttype)

    if font_size is not None:
        mpl.rcParams["font.size"] = font_size
        mpl.rcParams["axes.labelsize"] = font_size
        mpl.rcParams["axes.titlesize"] = font_size
        mpl.rcParams["xtick.labelsize"] = font_size - 0.5
        mpl.rcParams["ytick.labelsize"] = font_size - 0.5
        mpl.rcParams["legend.fontsize"] = font_size - 0.5

    if strict_glyphs:
        # 缺字 → UserWarning → 直接异常，不让豆腐块流到交付物里
        warnings.simplefilter("error", UserWarning)

    if lang == "en" and verify_fonts:
        # strict_glyphs 已生效：mathtext 里只要缺一个字，这里就会抛异常
        verify_mathtext(verbose=True)


# --------------------------------------------------------------------------- #
# 2b. 字形覆盖：离线探测 + 图级核对 + mathtext 自检
# --------------------------------------------------------------------------- #

def _font_cmap(path: str | None) -> set[int]:
    """读一个字体文件的 cmap（覆盖到的码位集合）；读不到返回空集。"""
    if not path:
        return set()
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return set()
    try:
        cmap: set[int] = set()
        font = TTFont(path, fontNumber=0, lazy=True)
        for table in font["cmap"].tables:
            cmap.update(table.cmap.keys())
        font.close()
        return cmap
    except Exception:  # noqa: BLE001
        return set()


def _split_math(text: str) -> tuple[str, list[str]]:
    """把 ``a $x$ b`` 拆成（非数学部分, [数学段, ...]）。"""
    parts = text.split("$")
    return "".join(parts[0::2]), parts[1::2]


def missing_glyph_probe(
    text: str,
    *,
    all_chars: bool = False,
    font_path: str | None = None,
) -> list[str]:
    """离线探测一段文本中当前字体渲染不了的字符（不依赖渲染）。

    ``all_chars=True`` 时连 ASCII 一起核对（英文模式用；中文模式默认只看非 ASCII，
    保持历史行为逐字节不变）。``font_path`` 可显式指定字体文件。
    """
    from matplotlib import font_manager

    if font_path is None:
        path = None
        for fam in mpl.rcParams.get("font.sans-serif", []):
            try:
                path = font_manager.findfont(
                    font_manager.FontProperties(family=fam), fallback_to_default=False
                )
                break
            except Exception:  # noqa: BLE001
                continue
    else:
        path = font_path
    cmap = _font_cmap(path)
    if not cmap:
        return []
    return [
        ch
        for ch in dict.fromkeys(text)
        if ch not in ("\n", "\t") and (all_chars or ord(ch) > 0x7F) and ord(ch) not in cmap
    ]


def missing_glyph_report(fig) -> list[dict]:
    """一次性核对图内**所有**文字的字形覆盖，返回缺字清单。

    与"渲染时 UserWarning"互补：警告只在真的画到那个字形时才出现，
    本函数把全图 Text 都核对一遍（含 ASCII）。数学段用 mathtext 的
    DejaVu 字体核对（``mathtext.fontset='dejavusans'``）。
    """
    path = None
    try:
        path = resolved_font_path()
    except Exception:  # noqa: BLE001
        path = None
    cmap = _font_cmap(path)
    mpath = os.path.join(mpl.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf")
    mcmap = _font_cmap(mpath)
    out: list[dict] = []
    for t in fig.findobj(mpl.text.Text):
        s = t.get_text()
        if not s or not s.strip():
            continue
        plain, math = _split_math(s)
        miss = [ch for ch in dict.fromkeys(plain) if ch not in ("\n", "\t") and ord(ch) not in cmap]
        mmiss = [
            ch
            for ch in dict.fromkeys("".join(math))
            if ch.isalpha() and mcmap and ord(ch) not in mcmap
        ]
        if miss or mmiss:
            out.append(dict(text=s, missing=miss, missing_math=mmiss))
    return out


def verify_mathtext(sample: str | None = None, *, verbose: bool = True) -> dict:
    """英文模式自检：mathtext 在不依赖 CJK 字体的情况下能渲染出墨迹。

    与 :func:`use_style` 的 ``strict_glyphs`` 配合：缺字会直接抛异常，
    所以"没抛异常 + 有墨迹"即证明 mathtext 通路可用。
    """
    sample = sample or (
        r"$\lambda^*$ "
        r"$c_i(k)=d_i(k)+\lambda Q_k$ "
        r"$\pi_\theta(a_i\,|\,o_i)$ "
        r"$R_0=\beta/\gamma$ "
        r"$(\boldsymbol{o},\boldsymbol{a},r,s')$"
    )
    fig = plt.figure(figsize=(2.0, 0.6), dpi=200)
    fig.text(0.02, 0.45, sample, fontsize=9, color="#1A1A1A")
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    ink = int((buf[..., :3] < 250).any(axis=-1).sum())
    plt.close(fig)
    if ink <= 0:
        raise RuntimeError("[csf_fig] mathtext 自检失败：样张渲染后没有任何墨迹")
    if verbose:
        print(f"[csf_fig] lang=en mathtext 自检通过（ink={ink} px）")
    return {"sample": sample, "ink_px": ink}


# --------------------------------------------------------------------------- #
# 3. 组件库：终止文字溢出与箭头斜穿
# --------------------------------------------------------------------------- #

def _stamp_role(text_artist, role: str):
    """给一个 Text 打上语义角色，供文字台账（labels.json / labels.csv）使用。

    角色名以 ``_csf_role`` 属性挂在 artist 上（不覆盖 matplotlib 自己的属性），
    导出时由 :func:`csf_archetypes.collect_labels` 读走；读不到时按上下文启发式分类。
    """
    try:
        text_artist._csf_role = role
    except Exception:  # noqa: BLE001
        pass
    return text_artist


@dataclass
class _Box:
    """记录已绘制的盒子，供箭头锚点吸附与重叠检测使用。"""

    x: float
    y: float
    w: float
    h: float
    label: str = ""

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def anchor(self, side: str) -> tuple[float, float]:
        return {
            "left": (self.x, self.cy),
            "right": (self.x + self.w, self.cy),
            "top": (self.cx, self.y + self.h),
            "bottom": (self.cx, self.y),
            "center": (self.cx, self.cy),
        }[side]

    def overlaps(self, other: "_Box", pad: float = 0.0) -> bool:
        return not (
            self.x + self.w + pad <= other.x
            or other.x + other.w + pad <= self.x
            or self.y + self.h + pad <= other.y
            or other.y + other.h + pad <= self.y
        )


class FigSpec:
    """一张图的构建器：盒子自动撑开、箭头自动吸附、导出一次到位。

    坐标用数据坐标系（推荐 0–100 的画布单位），避免不同 DPI 下错位。
    """

    def __init__(
        self,
        title: str = "",
        *,
        width_mm: float = 183.0,
        height_mm: float | None = None,
        aspect: float = 0.62,
        dpi: int = 300,
        palette: SemanticPalette | None = None,
        canvas: tuple[float, float] = (100.0, 100.0),
    ) -> None:
        self.title = title
        self.width_mm = width_mm
        self.height_mm = height_mm or width_mm * aspect
        self.dpi = dpi
        self.palette = palette or SemanticPalette()
        self.canvas = canvas
        self.boxes: list[_Box] = []

        self.fig = plt.figure(
            figsize=(self.width_mm / 25.4, self.height_mm / 25.4), dpi=dpi
        )
        self.ax = self.fig.add_axes((0.01, 0.01, 0.98, 0.94 if title else 0.98))
        self.ax.set_xlim(0, canvas[0])
        self.ax.set_ylim(0, canvas[1])
        self.ax.axis("off")
        if title:
            _stamp_role(self.ax.set_title(title, fontweight="bold", pad=6), "title")

    # -- 组件 --------------------------------------------------------------- #

    def draw_box(
        self,
        x: float,
        y: float,
        text: str,
        *,
        role: str | None = None,
        facecolor: str = "#FFFFFF",
        edgecolor: str | None = None,
        min_w: float = 14.0,
        h: float = 12.0,
        fontsize: float | None = None,
        pad_units: float = 3.0,
        lw: float = 1.2,
        zorder: int = 3,
    ) -> _Box:
        """画一个模块框。**宽度按文字长度自动撑开**，从根上避免文字溢出框外。"""
        fontsize = fontsize or mpl.rcParams["font.size"]
        edge = edgecolor or (self.palette(role) if role else "#4D4D4D")
        face = facecolor
        if role == "ours" and facecolor == "#FFFFFF":
            face = "#EAF1F8"
        elif role in ("bottleneck",) and facecolor == "#FFFFFF":
            face = "#FBEDED"

        # 估算：一个全角字符 ≈ 1.0 em，半角 ≈ 0.55 em；em 换算到画布单位
        em_units = fontsize * (self.canvas[0] / (self.width_mm * 72 / 25.4))
        longest = 0.0
        for line in text.split("\n"):
            w_est = sum(1.0 if ord(ch) > 0x2E80 else 0.55 for ch in line)
            longest = max(longest, w_est)
        w = max(min_w, longest * em_units + 2 * pad_units)

        rounded = mpl.patches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle=f"round,pad=0,rounding_size={min(2.0, h * 0.18)}",
            linewidth=lw,
            edgecolor=edge,
            facecolor=face,
            zorder=zorder,
        )
        self.ax.add_patch(rounded)
        txt = self.ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            fontsize=fontsize,
            color=SEMANTIC["text"],
            zorder=zorder + 1,
            linespacing=1.5,
        )
        _stamp_role(txt, "node")
        box = _Box(x, y, w, h, label=text)
        self.boxes.append(box)
        return box

    def draw_arrow(
        self,
        src: _Box | tuple[float, float],
        dst: _Box | tuple[float, float],
        *,
        src_side: str = "right",
        dst_side: str = "left",
        label: str = "",
        role: str = "text",
        style: str = "-",
        rad: float = 0.0,
        lw: float = 1.3,
        fontsize: float | None = None,
        label_offset: float = 2.5,
        color: str | None = None,
    ) -> None:
        """画箭头。传 ``_Box`` 时**自动吸附到框边**，不再出现悬空起点。"""
        p0 = src.anchor(src_side) if isinstance(src, _Box) else src
        p1 = dst.anchor(dst_side) if isinstance(dst, _Box) else dst
        c = color or (self.palette(role) if role in self.palette.mapping else SEMANTIC["text"])

        self.ax.annotate(
            "",
            xy=p1,
            xytext=p0,
            arrowprops=dict(
                arrowstyle="-|>",
                color=c,
                linewidth=lw,
                linestyle=style,
                shrinkA=0,
                shrinkB=0,
                connectionstyle=f"arc3,rad={rad}",
            ),
            zorder=2,
        )
        if label:
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            nx, ny = -(p1[1] - p0[1]), (p1[0] - p0[0])
            norm = (nx * nx + ny * ny) ** 0.5 or 1.0
            _stamp_role(self.ax.text(
                mx + nx / norm * label_offset,
                my + ny / norm * label_offset,
                label,
                ha="center",
                va="center",
                fontsize=(fontsize or mpl.rcParams["font.size"]) - 0.5,
                color=c,
                zorder=4,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92),
            ), "annotation")

    def panel_label(self, letter: str, *, x: float = 0.5, y: float | None = None) -> None:
        """面板编号 a/b/c，放左上角外侧（顶会铁律）。"""
        _stamp_role(self.ax.text(
            x,
            y if y is not None else self.canvas[1] - 2.0,
            letter,
            ha="left",
            va="top",
            fontsize=mpl.rcParams["font.size"] + 2,
            fontweight="bold",
            color=SEMANTIC["text"],
        ), "panel-tag")

    def add_figure(self, fig, rect: tuple[float, float, float, float]) -> None:
        """把子图（matplotlib Figure）以 axes 形式嵌入指定矩形区（画布单位）。"""
        x0, y0, w, h = rect
        sub = self.fig.add_axes(
            (
                (0.01 + 0.98 * x0 / self.canvas[0]),
                (0.01 + 0.98 * y0 / self.canvas[1]),
                0.98 * w / self.canvas[0],
                0.98 * h / self.canvas[1],
            )
        )
        for ax in fig.axes:
            data = []
            for line in ax.get_lines():
                data.append(("line", line.get_xdata(), line.get_ydata(), line.get_label(),
                             line.get_linestyle(), line.get_linewidth()))
            for patch in ax.patches:
                data.append(("patch", patch, None, "", "", 0))
            for kind, a, b, lbl, ls, lw in data:
                if kind == "line":
                    sub.plot(a, b, label=lbl, linestyle=ls, linewidth=lw)
                else:
                    sub.add_patch(a)
            sub.set_xlabel(ax.get_xlabel())
            sub.set_ylabel(ax.get_ylabel())
            leg = ax.get_legend()
            if leg is not None:
                sub.legend(frameon=False, loc="best")
        plt.close(fig)

    # -- 校验与导出 ---------------------------------------------------------- #

    def check_overlaps(self, pad: float = 0.0) -> list[str]:
        """返回互相重叠的盒子描述——对应实测中"图例压边框""文字叠星标"。"""
        problems: list[str] = []
        for i in range(len(self.boxes)):
            for j in range(i + 1, len(self.boxes)):
                a, b = self.boxes[i], self.boxes[j]
                if a.overlaps(b, pad=pad):
                    problems.append(f"盒子重叠: {a.label!r} ↔ {b.label!r}")
        return problems

    def check_bounds(self) -> list[str]:
        """盒子是否越出画布。"""
        W, H = self.canvas
        return [
            f"越界: {b.label!r} @ ({b.x:.1f},{b.y:.1f}) {b.w:.1f}×{b.h:.1f}"
            for b in self.boxes
            if b.x < 0 or b.y < 0 or b.x + b.w > W or b.y + b.h > H
        ]

    def finalize(
        self,
        outdir: str,
        name: str,
        *,
        formats: tuple[str, ...] = ("pdf", "svg", "png"),
        transparent: bool = False,
        tight: bool = True,
        report: bool = True,
        labels: bool = True,
        lang: str = "zh",
        narrative_role: str = "",
        takeaway: str = "",
    ) -> dict[str, str]:
        """导出矢量+栅格双份，并返回路径表。矢量优先、PNG 固定 300dpi。

        ``labels=True`` 时同时写出 ``<name>.labels.json`` / ``<name>.labels.csv``
        （逐条文字的角色与坐标台账，见 ``csf_archetypes.export_label_ledger``），
        并把台账合并进 outdir 下的 ``labels.json`` / ``labels.csv``。
        """
        os.makedirs(outdir, exist_ok=True)
        written: dict[str, str] = {}
        ledger: dict[str, str] = {}
        if labels:
            # 台账要在 savefig **之前**建立：它同时负责给 SVG 元素打 id
            ledger = _try_label_ledger(
                self.fig, outdir, name, lang=lang,
                narrative_role=narrative_role, takeaway=takeaway,
            )
        for fmt in formats:
            path = os.path.join(outdir, f"{name}.{fmt}")
            kwargs: dict = dict(bbox_inches="tight" if tight else None,
                                transparent=transparent, facecolor="white")
            if fmt == "png":
                kwargs["dpi"] = self.dpi
            self.fig.savefig(path, format=fmt, **kwargs)
            written[fmt] = path

        if report:
            issues = self.check_overlaps() + self.check_bounds()
            conflicts = self.palette.conflict_report()
            print(f"[csf_fig] {name}: 导出 {len(written)} 份 → {outdir}")
            for fmt, p in written.items():
                print(f"          {fmt}: {os.path.basename(p)} ({os.path.getsize(p):,} B)")
            for fmt, p in ledger.items():
                print(f"          labels: {os.path.basename(p)} ({os.path.getsize(p):,} B)")
            if issues:
                print("[csf_fig] ⚠ 几何问题:")
                for it in issues:
                    print("          -", it)
            if conflicts:
                print("[csf_fig] ⚠ 配色复用（同色=同义才允许）:")
                for c in conflicts:
                    print("          -", c)
        plt.close(self.fig)
        written.update(ledger)
        return written


def figure_contract_check(contract: dict, rendered: dict | None = None) -> list[str]:
    """校验 figure contract 的**必填字段**，缺一项就报问题。

    必填：conclusion / role_in_paper / panels[].role / panels[].source /
          panels[].units / evidence_level / integrity_risks
    """
    problems: list[str] = []
    required_top = ["conclusion", "role_in_paper", "evidence_level", "panels"]
    for key in required_top:
        if not contract.get(key):
            problems.append(f"contract 缺字段: {key}")

    panels = contract.get("panels") or []
    if not panels:
        problems.append("contract 至少需要 1 个 panel")
    for idx, p in enumerate(panels):
        tag = p.get("id") or f"panel[{idx}]"
        for key in ("role", "source", "units", "claim"):
            if not p.get(key):
                problems.append(f"{tag} 缺字段: {key}")

    roles = {p.get("role") for p in panels}
    if not roles & {"hero", "main"}:
        problems.append("没有任何 panel 声明为 hero/main —— 一图必须有主结论面板")

    if not contract.get("integrity_risks"):
        problems.append("缺 integrity_risks：未声明可能被误读的点")

    if rendered is not None:
        for fmt in ("pdf", "png"):
            if fmt not in rendered:
                problems.append(f"未导出 {fmt}（矢量+300dpi 双份是硬要求）")
    return problems


def _try_label_ledger(
    fig,
    outdir: str,
    name: str,
    *,
    lang: str = "zh",
    narrative_role: str = "",
    takeaway: str = "",
) -> dict[str, str]:
    """调用 `csf_archetypes` 的文字台账导出（唯一实现，不另起并行路径）。

    台账失败时**大声打印**并继续出图——图本身是主交付物，不该被台账拖死；
    但绝不静默：任何异常都会带类型与消息打出来。
    """
    try:
        from csf_archetypes import export_label_ledger
    except Exception as exc:  # noqa: BLE001
        print(f"[csf_fig] ⚠ 未写出文字台账（导入 csf_archetypes 失败）："
              f"{type(exc).__name__}: {exc}")
        return {}
    try:
        return export_label_ledger(
            fig, outdir, name, fig_id=name, lang=lang,
            narrative_role=narrative_role, takeaway=takeaway, verbose=False,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[csf_fig] ⚠ 未写出文字台账（{name}）：{type(exc).__name__}: {exc}")
        return {}
