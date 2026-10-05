"""MARL 训练与评估骨架（IPPO：SB3 PPO + 参数共享；合作任务首选最稳方案）。

- 更复杂的 QMIX/MAPPO/VDN 用 EPyMARL / PyMARLzoo+，不要手写轮子。
- 本骨架演示：多 seed 训练 → 评估 → 指标统计 → 结果落盘（与工作站规范一致）。

用法：
    python train_marl.py --run-id ippo_v1 --seeds 3 --total-timesteps 200000
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
    eval_env = DummyVecEnv([make_env(seed)])
    model = PPO("MlpPolicy", env, seed=seed, verbose=0,
                n_steps=2048, batch_size=64, learning_rate=3e-4)
    eval_cb = EvalCallback(eval_env, best_model_save_path=str(out_dir),
                           log_path=str(out_dir), eval_freq=20000,
                           n_eval_episodes=5, deterministic=True)
    model.learn(total_timesteps=total_timesteps, callback=eval_cb)
    model.save(str(out_dir / "final_model"))
    return model, eval_cb


def evaluate(model, env_factory, n_episodes: int = 20):
    env = DummyVecEnv([env_factory(0)])
    returns, lens = [], []
    obs = env.reset()
    for _ in range(n_episodes):
        ep_r, ep_l = 0.0, 0
        while True:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            ep_r += float(reward[0]); ep_l += 1
            if done[0]:
                obs = env.reset()
                break
        returns.append(ep_r); lens.append(ep_l)
    return float(np.mean(returns)), float(np.std(returns)), float(np.mean(lens))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="ippo_v1")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--total-timesteps", type=int, default=200_000)
    ap.add_argument("--n-eval", type=int, default=20)
    args = ap.parse_args()

    out_root = Path("02-实验与结果/outputs") / args.run_id
    out_root.mkdir(parents=True, exist_ok=True)

    summary = {"run_id": args.run_id, "seeds": args.seeds,
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
