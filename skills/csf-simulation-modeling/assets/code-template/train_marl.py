"""单环境 PPO 训练骨架；不是已实现的 IPPO、参数共享或 CTDE。

- 更复杂的 QMIX/MAPPO/VDN 用 EPyMARL / PyMARLzoo+，不要手写轮子。
- 多智能体任务需另外实现逐智能体观测/动作、联合推进与数据收集接口。
- 本骨架演示多 seed 训练与回报汇总，回报不等于赛题 KPI。

用法：
    python train_marl.py --run-id ppo_v1 --seeds 3 --total-timesteps 200000
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv

# 换成你包装好的环境（见 gym_env.py）
# from gym_env import SimulationEnv


def make_env(seed: int):
    # return lambda: SimulationEnv(cfg)
    raise NotImplementedError("接入你的 SimulationEnv")


def train_one_seed(seed: int, total_timesteps: int, out_dir: Path):
    env = DummyVecEnv([make_env(seed)])
    eval_env = DummyVecEnv([make_env(seed + 10_000)])  # 验证流与训练流分开
    model = PPO("MlpPolicy", env, seed=seed, verbose=0,
                n_steps=2048, batch_size=64, learning_rate=3e-4)
    eval_cb = EvalCallback(eval_env, best_model_save_path=str(out_dir),
                           log_path=str(out_dir), eval_freq=20000,
                           n_eval_episodes=5, deterministic=True)
    model.learn(total_timesteps=total_timesteps, callback=eval_cb)
    model.save(str(out_dir / "final_model"))
    env.close()
    eval_env.close()
    return model, eval_cb


def evaluate(model, env_factory, n_episodes: int = 20, max_steps: int = 100_000):
    """env_factory(seed) 返回构造环境的 callable；测试 seed 不用于选模型。"""
    if n_episodes < 1 or max_steps < 1:
        raise ValueError("n_episodes 和 max_steps 必须为正")
    returns, lens = [], []
    for episode in range(n_episodes):
        seed = 20_000 + episode
        env = env_factory(seed)()
        try:
            obs, _ = env.reset(seed=seed)
            ep_r = 0.0
            for ep_l in range(1, max_steps + 1):
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, _ = env.step(action)
                ep_r += float(reward)
                if terminated or truncated:
                    break
            else:
                raise RuntimeError("评估超过 max_steps；请实现任务终止/时间截断，不能当成功运行")
            returns.append(ep_r); lens.append(ep_l)
        finally:
            env.close()
    std = float(np.std(returns, ddof=1)) if n_episodes > 1 else None
    return float(np.mean(returns)), std, float(np.mean(lens))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="ppo_v1")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--total-timesteps", type=int, default=200_000)
    ap.add_argument("--n-eval", type=int, default=20)
    args = ap.parse_args()
    if args.seeds < 1 or args.total_timesteps < 1 or args.n_eval < 2:
        ap.error("seeds/timesteps 必须为正，n-eval 至少为 2")

    out_root = Path("02-实验与结果/outputs") / args.run_id
    out_root.mkdir(parents=True, exist_ok=True)

    summary = {"run_id": args.run_id, "algorithm": "single-environment PPO skeleton",
               "reported_quantity": "episode_return, not task KPI", "seeds": args.seeds,
               "total_timesteps": args.total_timesteps, "results": []}
    for seed in range(args.seeds):
        out_dir = out_root / f"seed{seed}"
        out_dir.mkdir(parents=True, exist_ok=True)
        model, _ = train_one_seed(seed, args.total_timesteps, out_dir)
        mean_r, std_r, mean_l = evaluate(model, lambda s: make_env(s), args.n_eval)
        summary["results"].append({"seed": seed, "mean_return": mean_r,
                                   "std_return": std_r, "mean_length": mean_l})
        print(f"[seed {seed}] return={mean_r:.3f}±{std_r:.3f} len={mean_l:.1f}")

    (out_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("summary saved ->", out_root / "summary.json")


if __name__ == "__main__":
    main()
