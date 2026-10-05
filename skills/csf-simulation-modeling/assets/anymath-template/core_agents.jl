# =============================================================================
# core_agents.jl —— 多智能体仿真核心（**平台无关的纯 Julia**）
#
# 设计原则（与 Python 版 core/ 一一对应，便于逐段互查与数值对拍）
# -----------------------------------------------------------------------------
#   1. 本文件**不引用任何 AnyMath API**（不出现 engee.*）。
#      这样它既能在本地 Julia 直接跑并验证，也能原样上传到 AnyMath。
#   2. 平台相关的东西（engee.run / simout / Plots / CSV）全部隔离在
#      `run_anymath.jl` 里。
#   3. 所有随机性由显式 seed 控制，两平台用**同一组 seed**，便于逐位/容差对拍。
#
# 为什么用抽象类型 + 可变结构体（照抄官方范式）
# -----------------------------------------------------------------------------
# AnyMath 官方在多智能体上**没有任何专用库**（Agents.jl / Mesa / gym / PettingZoo
# 在 150 页文档中零命中）。官方给出的手写范式是：
#     abstract type Agent end
#     mutable struct XxxAgent <: Agent ... end
#     mutable struct Model ... end
#     step!(model)
# 参考实例：Wolves_and_sheep（生态 ABM）、Drone_swarm（无人机群协同）。
#
# Julia 与 numpy 的三处语义差异（会**静默算错**，转写时逐处核对）
# -----------------------------------------------------------------------------
#   * 数组**列优先**（column-major）：reshape/vec 与 numpy 的 C 序结果不同
#   * 索引 **1-based**，且切片**含尾**：a[1:3] 取 3 个元素
#   * `*` 是**矩阵乘法**；逐元素用 `.*`
# =============================================================================

using Random
using Statistics
using LinearAlgebra
using Printf

# --------------------------------------------------------------------------- #
# 参数
# --------------------------------------------------------------------------- #

"""
全部可调参数集中在一处。命名与论文公式里的符号一致，减少转写时的语义漂移。
"""
Base.@kwdef mutable struct Params
    seed::Int          = 2026
    N::Int             = 400        # 需求点数量（个）
    v0::Float64        = 25.0       # 配送速度（km/h）
    q_per_station::Float64 = 12.0   # 每工位吞吐（人/小时）
    service_min::Float64   = 2.0    # 每次交接耗时（分钟）
    window_min::Float64    = 60.0   # 时间窗宽度（分钟）
    cap::Int               = 12     # 单趟载量（份）
    n_teams::Int           = 30     # 配送队数
    lam::Float64           = 1.0    # 名额柔化参数（0 = 纯就近；1 = 严格按容量比例）
end

# --------------------------------------------------------------------------- #
# 智能体与模型
# --------------------------------------------------------------------------- #

"""需求点（老人）。位置用两个 Float64 存，避免 Vector 带来的分配开销。"""
mutable struct DemandAgent <: Any
    id::Int
    x::Float64
    y::Float64
    earliest::Float64      # 期望送达时刻（分钟）
    latest::Float64        # 最迟送达时刻（分钟）
    station::Int           # 被分配的站点（0 = 未分配）
    arrive_t::Float64      # 实际送达时刻（分钟）
end

"""服务站（食堂）。"""
mutable struct Station
    name::String
    x::Float64
    y::Float64
    workstations::Int
    mu_per_min::Float64    # 服务率（人/分钟）
end

"""模型容器。对应 Python 侧的 State + 环境。"""
mutable struct DeliveryModel
    p::Params
    stations::Vector{Station}
    demands::Vector{DemandAgent}
    dist::Matrix{Float64}       # (N × K) 分钟，缓存后的行驶时间
    assign::Vector{Int}         # 当前分配
    load::Vector{Int}           # 各站已分配人数
    step::Int
end

# --------------------------------------------------------------------------- #
# 构造
# --------------------------------------------------------------------------- #

"""
从 Windows 风格 JSON 中抽取站点与需求点（不依赖 JSON.jl，避免额外安装）。

为什么手写解析：AnyMath 免费许可有 20 小时/月配额，不应把时间花在装包上；
且本解析器只处理本模板自己产出的、结构固定的 JSON，风险可控。

返回 `(stations, demands)`；解析失败返回 `nothing`。
"""
function load_instance_json(path::String)
    isfile(path) || return nothing
    txt = read(path, String)

    # --- 站点：{"name":"S1 老城中心","x":2.0,"y":7.5,"workstations":4,"mu_per_min":0.8} ---
    stations = Station[]
    for m in eachmatch(r"\{[^{}]*\"name\"\s*:\s*\"([^\"]*)\"[^{}]*\"x\"\s*:\s*([-\d.eE+]+)[^{}]*\"y\"\s*:\s*([-\d.eE+]+)[^{}]*\"workstations\"\s*:\s*(\d+)[^{}]*\"mu_per_min\"\s*:\s*([-\d.eE+]+)[^{}]*\}", txt)
        push!(stations, Station(m.captures[1], parse(Float64, m.captures[2]),
                                parse(Float64, m.captures[3]), parse(Int, m.captures[4]),
                                parse(Float64, m.captures[5])))
    end

    # --- 需求点：eleven 数组 {"id":[..],"x":[..],"y":[..],"earliest_min":[..],"latest_min":[..]} ---
    ex = match(r"\"x\"\s*:\s*\[([^\]]*)\]", txt)
    ey = match(r"\"y\"\s*:\s*\[([^\]]*)\]", txt)
    ee = match(r"\"earliest_min\"\s*:\s*\[([^\]]*)\]", txt)
    el = match(r"\"latest_min\"\s*:\s*\[([^\]]*)\]", txt)
    (ex === nothing || ey === nothing) && return nothing

    tofloats(s) = [parse(Float64, strip(v)) for v in split(s, ",") if !isempty(strip(v))]
    xs, ys = tofloats(ex.captures[1]), tofloats(ey.captures[1])
    n = min(length(xs), length(ys))
    es = ee === nothing ? zeros(n) : tofloats(ee.captures[1])
    ls = el === nothing ? zeros(n) : tofloats(el.captures[1])
    length(es) < n && (es = vcat(es, zeros(n - length(es))))
    length(ls) < n && (ls = es .+ 60.0)

    isempty(stations) && return nothing
    demands = [DemandAgent(i, xs[i], ys[i], es[i], ls[i], 0, 0.0) for i in 1:n]
    (stations, demands)
end

"""
构造实例。

`instance_path` 非空且文件存在时，**直接加载该实例**——这是跨语言对拍的**前提**：
Python 的 `default_rng(seed)` 与 Julia 的 `MersenneTwister(seed)` 会产生不同的点位，
不共用同一份实例就无法做等价性检验（实测教训）。
文件不存在时退回"按 seed 自行生成"，仅用于本地冒烟。
"""
function build_model(p::Params; instance_path::String="")::DeliveryModel
    loaded = isempty(instance_path) ? nothing : load_instance_json(instance_path)

    local stations::Vector{Station}
    local demands::Vector{DemandAgent}

    if loaded !== nothing
        stations, demands = loaded
    else
        rng = MersenneTwister(p.seed)

        # 站点：(name, x_km, y_km, 工位数)
        raw = [("S1 老城中心", 2.0, 7.5, 4),
               ("S2 河东",     7.5, 8.0, 3),
               ("S3 南苑",     5.0, 2.0, 2),
               ("S4 西关",     1.5, 2.5, 2),
               ("S5 北新",     8.0, 4.0, 3)]
        stations = [Station(n, x, y, w, w * p.q_per_station / 60.0) for (n, x, y, w) in raw]

        # 需求点：三个簇（60% / 25% / 15%），各向异性高斯，截断到场地内
        area = 10.0
        clusters = [(4.0, 2.5, 0.60, 0.9, 0.8),
                    (7.6, 7.8, 0.25, 0.9, 0.8),
                    (2.2, 7.4, 0.15, 0.8, 0.7)]
        demands = DemandAgent[]
        id = 0
        for (cx, cy, frac, sx, sy) in clusters
            m = round(Int, p.N * frac)
            for _ in 1:m
                id += 1
                x = clamp(cx + sx * randn(rng), 0.2, area - 0.2)
                y = clamp(cy + sy * randn(rng), 0.2, area - 0.2)
                base = 90.0 * rand(rng)          # 期望送达相对时刻
                push!(demands, DemandAgent(id, x, y, round(base, digits=1),
                                           round(base + p.window_min, digits=1), 0, 0.0))
            end
        end
        while length(demands) < p.N
            id += 1
            x = 0.2 + (area - 0.4) * rand(rng)
            y = 0.2 + (area - 0.4) * rand(rng)
            base = 90.0 * rand(rng)
            push!(demands, DemandAgent(id, x, y, round(base, digits=1),
                                       round(base + p.window_min, digits=1), 0, 0.0))
        end
        resize!(demands, p.N)
    end

    N = length(demands)
    K = length(stations)

    # 行驶时间矩阵（分钟）。Julia 列优先，但 dist[i, k] 与 numpy 的 dist[i,k] 语义一致
    dist = Matrix{Float64}(undef, N, K)
    v_km_per_min = p.v0 / 60.0
    for i in 1:N, k in 1:K
        dist[i, k] = hypot(demands[i].x - stations[k].x,
                           demands[i].y - stations[k].y) / v_km_per_min
    end

    DeliveryModel(p, stations, demands, dist, zeros(Int, N), zeros(Int, K), 0)
end

# --------------------------------------------------------------------------- #
# 策略：容量比例水填（本文方法）
# --------------------------------------------------------------------------- #

"""
按各站服务率比例分配名额（"水填"），再在名额内就近指派。

与 Python 侧 `policy_dynamic`（水填版）语义一致：
  1. 目标名额 target[k] = floor(μ_k / Σμ × N)，余数给容量最大的站；
  2. `lam` 作为名额柔化：lam=0 → 纯就近（名额不约束）；lam=1 → 严格按名额。
  3. 按"离各站最近距离"升序处理需求点，把最无处可去的点先安排。

返回分配数组 assign（长度 N，取值 1..K）。
"""
function policy_waterfill(m::DeliveryModel)::Vector{Int}
    N = length(m.demands)
    K = length(m.stations)
    p = m.p
    mu = [s.mu_per_min for s in m.stations]
    target = floor.(Int, mu ./ sum(mu) .* N)
    target[argmax(mu)] += N - sum(target)          # 余数给容量最大的站

    # 名额柔化：lam=0 时目标变为均分（即"不按容量比例"，退化为纯就近优先）
    if p.lam <= 0
        soft = fill(N, K)                          # 无实质性名额约束
    else
        soft = max.(round.(Int, target .* p.lam .+ (N / K) .* (1 - p.lam)), 0)
        soft[argmax(mu)] += N - sum(soft)
    end
    soft = max.(soft, 0)

    remain = copy(soft)
    assign = zeros(Int, N)
    # 处理顺序：离最近站的距离**降序**（最无处可去的点先安排）
    nearest = [minimum(@view m.dist[i, :]) for i in 1:N]
    order = sortperm(nearest, rev=true)
    for i in order
        # 在还有名额的站里选最近的
        best_k = 0
        best_d = Inf
        for k in 1:K
            if remain[k] > 0 && m.dist[i, k] < best_d
                best_d = m.dist[i, k]
                best_k = k
            end
        end
        if best_k == 0                            # 名额用尽 → 全局最近
            best_k = argmin(@view m.dist[i, :])
        else
            remain[best_k] -= 1
        end
        assign[i] = best_k
    end
    assign
end

"""就近分配（基线 S1：仅初始决策一次）。"""
function policy_nearest(m::DeliveryModel)::Vector{Int}
    N = length(m.demands)
    [argmin(@view m.dist[i, :]) for i in 1:N]
end

"""随机分配（基线 S2：无信息）。"""
function policy_random(m::DeliveryModel)::Vector{Int}
    rng = MersenneTwister(m.p.seed + 991)
    rand(rng, 1:length(m.stations), length(m.demands))
end

# --------------------------------------------------------------------------- #
# 服务与配送：趟次池 + 队号轮转
# --------------------------------------------------------------------------- #

"""
计算送达时刻。与 Python 侧 simulate 的配送段语义一致：
  * 站点 k 第 j 个人装车完成时刻 = j / μ_k（分钟）
  * 每趟取 cap 人，趟次按"装车齐备时刻"先后竞争配送队
  * 某队第 n 次使用时，可出发时刻 ≥ 前一次返回时刻
  * 送达时刻 = 出发 + 单程行驶 + 交接/2
"""
function deliver!(m::DeliveryModel, assign::Vector{Int})::Vector{Float64}
    N = length(m.demands)
    K = length(m.stations)
    p = m.p
    arrive = zeros(Float64, N)

    trips = Tuple{Int, Vector{Int}, Float64, Float64}[]   # (k, idx, ready, round_trip)
    for k in 1:K
        idx = findall(==(k), assign)
        isempty(idx) && continue
        # 站内按期望送达时刻排序（EDD 类比）
        sort!(idx, by=i -> m.demands[i].earliest)
        for s in 1:p.cap:length(idx)
            sl = idx[s:min(s + p.cap - 1, length(idx))]
            ready = (s + length(sl) - 1) / m.stations[k].mu_per_min
            rt = 2.0 * mean(@view m.dist[sl, k]) + p.service_min
            push!(trips, (k, sl, ready, rt))
        end
    end
    sort!(trips, by=t -> t[3])                            # 先备齐的先派队

    team_free = zeros(Float64, p.n_teams)
    for (k, sl, ready, rt) in trips
        ti = argmin(team_free)
        depart = max(ready, team_free[ti])
        team_free[ti] = depart + rt
        for i in sl
            arrive[i] = depart + m.dist[i, k] + p.service_min / 2.0
        end
    end
    arrive
end

# --------------------------------------------------------------------------- #
# 指标
# --------------------------------------------------------------------------- #

"""标准 Gini 系数：G = ΣΣ|x_i − x_j| / (2 n² μ)。G=0 表示完全均衡。"""
function gini(x::AbstractVector{<:Real})::Float64
    n = length(x)
    mu = mean(x)
    mu <= 0 && return 0.0
    s = 0.0
    for i in 1:n, j in 1:n
        s += abs(x[i] - x[j])
    end
    s / (2 * n * n * mu)
end

"""跑一次完整仿真，返回指标（键名与 Python 侧完全一致，便于对拍）。

`instance_path` 非空时加载该实例，用于跨语言**同实例**对拍。
"""
function run(p::Params; policy::Symbol=:waterfill, instance_path::String="")::Dict{String,Any}
    m = build_model(p; instance_path=instance_path)
    assign = policy === :waterfill ? policy_waterfill(m) :
             policy === :nearest   ? policy_nearest(m)   :
             policy === :random    ? policy_random(m)    :
             error("未知策略 $policy")
    arrive = deliver!(m, assign)

    served = zeros(Int, length(m.stations))
    for k in assign
        served[k] += 1
    end
    on_time = count(i -> arrive[i] >= m.demands[i].earliest &&
                          arrive[i] <= m.demands[i].latest, 1:length(arrive))
    T = maximum(arrive)
    T_lb = length(m.demands) / sum(s.mu_per_min for s in m.stations)

    Dict{String,Any}(
        "policy"        => String(policy),
        "T"             => round(T, digits=2),
        "on_time_rate"  => round(on_time / length(arrive), digits=4),
        "gini_load"     => round(gini(served), digits=4),
        "served"        => served,
        "T_lb"          => round(T_lb, digits=2),
        "ratio_lb"      => round(T / T_lb, digits=3),
        "seed"          => p.seed,
    )
end

# --------------------------------------------------------------------------- #
# 作为脚本直接运行时的自检（本地 Julia 可跑；AnyMath 里也可跑）
# --------------------------------------------------------------------------- #

if abspath(PROGRAM_FILE) == @__FILE__
    println("="^70)
    println("core_agents.jl 自检（纯 Julia，不依赖 AnyMath）")
    println("="^70)
    for pol in (:nearest, :random, :waterfill)
        res = run(Params(seed=2026), policy=pol)
        @printf("  %-10s T=%7.2f  T/T_lb=%5.3f  准时率=%.3f  Gini=%.3f  served=%s\n",
                res["policy"], res["T"], res["ratio_lb"],
                res["on_time_rate"], res["gini_load"], string(res["served"]))
    end
    println("\n提示：跨语言对拍用同一组 seed（2026..2030），")
    println("      并把结果写成 CSV 与 Python 侧 results/*.json 逐项比对。")
end
