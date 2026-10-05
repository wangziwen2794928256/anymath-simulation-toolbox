p = r"D:\anymath-and-simulation\skills\csf-simulation-modeling\scripts\csf_scaffold.py"
src = open(p, encoding="utf-8").read()
n0 = src.count("{title}")
src = src.replace("{title}", "__TITLE__")
pairs = [
    ("CORE_MODEL.format(title=t)", 'CORE_MODEL.replace("__TITLE__", t)'),
    ("CORE_POLICIES.format(title=t)", 'CORE_POLICIES.replace("__TITLE__", t)'),
    ("CORE_METRICS.format(title=t)", 'CORE_METRICS.replace("__TITLE__", t)'),
    ("ADAPTER_LOCAL.format(title=t)", 'ADAPTER_LOCAL.replace("__TITLE__", t)'),
    ("ADAPTER_JL.format(title=t)", 'ADAPTER_JL.replace("__TITLE__", t)'),
    ('FIG_CONTRACT.format(name="fig1_scene")', 'FIG_CONTRACT.replace("{name}", "fig1_scene")'),
    ('FIG_CONTRACT.format(name="fig2_main")', 'FIG_CONTRACT.replace("{name}", "fig2_main")'),
]
cnt = 0
for a, b in pairs:
    if a in src:
        src = src.replace(a, b)
        cnt += 1
open(p, "w", encoding="utf-8", newline="\n").write(src)
print(f"replaced {{title}} x{n0}; format->replace x{cnt}")
