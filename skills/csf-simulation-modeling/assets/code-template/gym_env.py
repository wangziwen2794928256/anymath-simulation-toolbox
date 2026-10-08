"""Gymnasium 环境包装骨架：把自建仿真环境接进 stable-baselines3。

用法：
    from gym_env import SimulationEnv
    env = SimulationEnv(cfg)
    model = PPO("MlpPolicy", env, seed=cfg.seed, verbose=1)
    model.learn(total_timesteps=cfg.total_timesteps)
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces


class SimulationEnv(gym.Env):
    """把 RuleEnvironment（或你的 ABM/DES 模型）包装成 Gym 接口。

    - observation: 智能体可观测状态（展平为 float 向量）
    - action: 离散或连续决策
    - reward: 每步标量奖励（与赛题 KPI 对齐）
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, cfg) -> None:
        super().__init__()
        self.cfg = cfg
        # TODO: 按题目设定维度
        obs_dim = 10
        n_actions = 4
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)
        self.action_space = spaces.Discrete(n_actions)
        self.reset(seed=cfg.seed)

    def reset(self, *, seed: int | None = None, options: Dict[str, Any] | None = None):
        super().reset(seed=seed)
        # TODO: 重置底层仿真
        raise NotImplementedError("先实现底层 reset、初始观测与随机数流；模板不生成虚假全零轨迹")

    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        # TODO: 把 action 翻译成底层模型的决策，推进一个时间步
        raise NotImplementedError("实现状态转移、动作合法性、KPI 奖励与 terminated/truncated 后再训练")

    def _obs(self) -> np.ndarray:
        return self.state.astype(np.float32)

    def _reward(self) -> float:
        # 奖励要与 KPI 单调一致，且避免稀疏到无法学习
        raise NotImplementedError("按赛题 KPI 实现奖励，并分别记录原始 KPI")

    def _terminal(self) -> bool:
        raise NotImplementedError("定义任务终止；时间预算耗尽应返回 truncated=True")

    def render(self):
        # matplotlib/plotly 动画；训练时关掉
        raise NotImplementedError
