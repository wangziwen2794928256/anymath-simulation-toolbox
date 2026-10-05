# =============================================================================
# run_anymath.jl —— AnyMath 侧驱动脚本（多 seed 循环 + 结果落盘）
#
# 职责边界：只做"调用 core_agents → 落盘 CSV/JSON → 出图"，
# **不含任何算法逻辑**（算法改只改 core_agents.jl）。
#
# 本文件分两段，**必须区分清楚**：
#   【A 段】平台无关：多 seed 循环 + 指标汇总 + 写文件
#           —— 已在本地 Julia 1.11.5 实测通过（见文件末尾自检）
#   【B 段】AnyMath 专属：engee.load/run/set_param!/get_results/simout/Plots
#           —— **仅在 AnyMath 平台可用**，本地 Julia 会因缺 engee 模块而报错，
#              故用 `if isdefined(Main, :engee)` 守卫，本地自动跳过
#
# AnyMath API 依据（均摘自官方文档，见 references/anymath-quickref.md）
# -----------------------------------------------------------------------------
#   engee.run(; verbose=false)
#   engee.run(model; verbose=false)   where model <: Union{Model, System, AbstractString}
#   engee.load(file_path; name=nothing, force=false)::Model
#   engee.set_param!(model, param::Pair...)
#   engee.get_results(model)::Dict{String,DataFrame}
#   engee.set_log(system_path, port_path)     # **不记录就没有数据**
#   engee.screenshot(to_print, save_path; position_mode="auto")   # 仅 PNG/SVG
#   simout（工作区变量，需在设置里勾选"保存到工作区"）→ collect(simout["模型/块.端口"])
#   ⚠ 文档自相矛盾：engee.run 的返回类型在不同页分别是
#     Dict{String,DataFrame} 与 SimulationResult+WorkspaceArray —— 落地前必须实测
# =============================================================================

include(joinpath(@__DIR__, "core_agents.jl"))

using Printf
using Statistics

# --------------------------------------------------------------------------- #
# 【A 段】平台无关：多 seed 循环 + 汇总 + 落盘
# --------------------------------------------------------------------------- #

const SEEDS = collect(2026:2030)

#: 跨语言对拍用的**同一份实例**。留空则按 seed 自行生成（仅本地冒烟）。
#: 设为 Python 侧 gen_instance.py 的输出路径即可做真正的等价性检验。
const INSTANCE_PATH = get(ENV, "CSF_INSTANCE", "")

"""
跑一组 seed × 策略，返回与 Python 侧 `results/*.json` **同构**的字典，
以便 `csf_parity.py` 直接对拍。
"""
function run_suite(; seeds::Vector{Int}=SEEDS, policies=(:nearest, :random, :waterfill),
                     instance_path::String=INSTANCE_PATH)
    out = Dict{String,Any}(
        "meta" => Dict{String,Any}("seeds" => seeds, "lang" => "julia",
                                   "instance" => isempty(instance_path) ? "self-generated" : instance_path),
        "policies" => Dict{String,Any}(),
    )
    for pol in policies
        Ts = Float64[]
        Os = Float64[]
        Gs = Float64[]
        Rs = Float64[]
        served_ref = Int[]
        for s in seeds
            r = run(Params(seed=s), policy=pol, instance_path=instance_path)
            push!(Ts, r["T"]); push!(Os, r["on_time_rate"])
            push!(Gs, r["gini_load"]); push!(Rs, r["ratio_lb"])
            isempty(served_ref) && (served_ref = Int.(r["served"]))
        end
        out["policies"][String(pol)] = Dict{String,Any}(
            "T_mean"       => round(mean(Ts), digits=2),
            "T_std"        => round(length(Ts) > 1 ? std(Ts) : 0.0, digits=2),
            "T_seeds"      => round.(Ts, digits=2),
            "on_time_mean" => round(mean(Os), digits=4),
            "gini_mean"    => round(mean(Gs), digits=4),
            "ratio_lb_mean" => round(mean(Rs), digits=3),
            "served"       => served_ref,
        )
    end
    out
end

"""把汇总结果写成 JSON（手写序列化，避免依赖 JSON.jl 之外的包）。"""
function write_json(path::String, d::Dict)
    open(path, "w") do io
        _write_json(io, d)
    end
end

"""把字符串转义成**严格合法**的 JSON（非 ASCII 一律转 \\uXXXX）。

实现教训（自拟题实测）：初版直接 `print(io, "\\"", v, "\\"")`，多字节 UTF-8
字符（中文站名）未转义，导致 Python 侧 `json.load` 报
`Invalid \escape`。JSON 规范允许原始 UTF-8，但**跨语言交换要迁就最严格的
解析器**；最稳的做法是把所有非 ASCII 码点转义成 \\uXXXX。
"""
function _json_escape(s::AbstractString)::String
    buf = IOBuffer()
    for c in s
        if c == '"'
            print(buf, "\\\"")
        elseif c == '\\'
            print(buf, "\\\\")
        elseif c == '\n'
            print(buf, "\\n")
        elseif c == '\r'
            print(buf, "\\r")
        elseif c == '\t'
            print(buf, "\\t")
        elseif Int(c) < 0x20 || Int(c) > 0x7E
            cp = Int(c)
            if cp <= 0xFFFF
                print(buf, "\\u", uppercase(string(cp, base=16, pad=4)))
            else
                # 补充平面字符：用 UTF-16 代理对表示
                cp2 = cp - 0x10000
                hi = 0xD800 + (cp2 >> 10)
                lo = 0xDC00 + (cp2 & 0x3FF)
                print(buf, "\\u", uppercase(string(hi, base=16, pad=4)))
                print(buf, "\\u", uppercase(string(lo, base=16, pad=4)))
            end
        else
            print(buf, c)
        end
    end
    String(take!(buf))
end

function _write_json(io::IO, v)
    if v isa Dict
        print(io, "{")
        ks = collect(keys(v))
        for (i, k) in enumerate(ks)
            print(io, "\"", _json_escape(string(k)), "\":")
            _write_json(io, v[k])
            i < length(ks) && print(io, ",")
        end
        print(io, "}")
    elseif v isa AbstractVector
        print(io, "[")
        for (i, x) in enumerate(v)
            _write_json(io, x)
            i < length(v) && print(io, ",")
        end
        print(io, "]")
    elseif v isa AbstractString
        print(io, "\"", _json_escape(v), "\"")
    elseif v isa Bool
        print(io, v ? "true" : "false")
    elseif v isa Integer
        print(io, v)
    elseif v isa Real
        print(io, isfinite(v) ? string(Float64(v)) : "null")
    else
        print(io, "\"", _json_escape(string(v)), "\"")
    end
end

# --------------------------------------------------------------------------- #
# 【B 段】AnyMath 专属（本地 Julia 自动跳过）
# --------------------------------------------------------------------------- #

"""
在 AnyMath 平台上运行**块图模型**并取回被记录信号的标准骨架。

为什么单独写这一段：赛题作品通常是"脚本层（智能体）+ 块图层（动力学/状态机）"
的混合范式，块图部分必须用 engee.* 驱动；而脚本层的算法逻辑不该混进来。
"""
function run_block_model_on_anymath(; model_path::String="", model_name::String="")
    if !isdefined(Main, :engee)
        @warn "当前环境没有 engee 模块（说明不在 AnyMath 平台）——本段跳过"
        return nothing
    end
    engee = Main.engee

    # 1) 加载或打开模型（官方文档推荐的惯用法）
    if !isempty(model_name) && model_name in [m.name for m in engee.get_all_models()]
        model = engee.open(model_name)
    elseif !isempty(model_path)
        model = engee.load(model_path; force=true)
    else
        error("需要 model_path 或 model_name 之一")
    end

    # 2) 必须先把要输出的信号**打开记录**，否则 get_results 里没有它
    #    （GUI 也可：点信号线 → 记录；此处用程序化方式）
    # engee.set_log("<system_path>", "<port_path>")

    # 3) 参数与求解器（变步长示例；固定步长改 SolverType）
    engee.set_param!(model, "SolverName" => "Tsit5", "SolverType" => "variable-step")

    # 4) 跑
    res = engee.run(model; verbose=true)

    # 5) 取结果：文档给两种形态，运行时**判断**而不是假设
    if res isa AbstractDict
        @info "engee.run 返回 Dict（形态 1）" keys=collect(keys(res))
        return res
    else
        @info "engee.run 返回非 Dict（形态 2，通常是 SimulationResult）"
        return res
    end
end

# --------------------------------------------------------------------------- #
# 自检 / 入口
# --------------------------------------------------------------------------- #

if abspath(PROGRAM_FILE) == @__FILE__
    println("="^70)
    println("run_anymath.jl · 多 seed 汇总自检（平台无关段）")
    println("="^70)

    suite = run_suite()
    for (name, d) in sort(collect(suite["policies"]), by=x -> x[2]["T_mean"])
        @printf("  %-10s T=%7.2f±%-5.2f  T/T_lb=%5.3f  准时率=%.3f  Gini=%.3f\n",
                name, d["T_mean"], d["T_std"], d["ratio_lb_mean"],
                d["on_time_mean"], d["gini_mean"])
    end

    resdir = joinpath(@__DIR__, "results")
    mkpath(resdir)
    outpath = joinpath(resdir, "julia_results.json")
    write_json(outpath, suite)
    println("\n→ 已写出 $outpath")
    println("  下一步：用 csf_parity.py 与 Python 侧 results/*.json 对拍")
    println("    python skills/csf-simulation-modeling/scripts/csf_parity.py \\")
    println("        --py examples/<题目>/results/py.json --jl $outpath")
end
