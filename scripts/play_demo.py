# SPDX-FileCopyrightText: Copyright (c) 2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# Copyright (c) 2021 ETH Zurich, Nikita Rudin
# Modified by 川山甲战队考核项目 (2026) — 添加固定速度命令的评估/演示功能
#
# 用法:
#   python play_demo.py --task=a1 [--mode stand|walk] [--vx 1.0] [--steps 1000] [--num_envs 1] [--headless]
#   --mode stand: 命令速度 = 0（演示稳定站立）
#   --mode walk : 命令速度 = (vx, 0, 0)，直线行走
#   输出: 速度跟踪误差、行走距离、摔倒次数等定量指标（写入 stdout）

import os
import sys
import argparse
import numpy as np

import isaacgym  # 必须在 torch 之前导入（Isaac Gym 检查）
import torch

from legged_gym.envs import *
from legged_gym.utils import get_args, task_registry


def main():
    # 先解析自定义演示参数，再从 sys.argv 中剔除，避免干扰 legged_gym 的 get_args
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode", type=str, default="stand", choices=["stand", "walk"])
    parser.add_argument("--vx", type=float, default=1.0, help="walk 模式下的目标线速度 [m/s]")
    parser.add_argument("--steps", type=int, default=1000, help="运行的仿真步数（policy 步）")
    parser.add_argument("--flat", action="store_true", help="使用纯平地地形（演示用，避免粗糙地形摔倒）")
    demo_args, remaining = parser.parse_known_args(sys.argv[1:])
    sys.argv = [sys.argv[0]] + remaining
    args = get_args()

    env_cfg, train_cfg = task_registry.get_cfgs(name=args.task)
    # 覆盖部分参数用于测试/演示
    env_cfg.env.num_envs = min(env_cfg.env.num_envs, 50)
    if demo_args.flat:
        env_cfg.terrain.mesh_type = 'plane'   # 纯平地
    env_cfg.terrain.num_rows = 5
    env_cfg.terrain.num_cols = 5
    env_cfg.terrain.curriculum = False
    env_cfg.noise.add_noise = False
    env_cfg.domain_rand.randomize_friction = False
    env_cfg.domain_rand.push_robots = False

    env, _ = task_registry.make_env(name=args.task, args=args, env_cfg=env_cfg)
    obs = env.get_observations()

    train_cfg.runner.resume = True
    ppo_runner, train_cfg = task_registry.make_alg_runner(env=env, name=args.task, args=args, train_cfg=train_cfg)
    policy = ppo_runner.get_inference_policy(device=env.device)

    # ---- 固定命令设置 ----
    mode = demo_args.mode
    vx_cmd = demo_args.vx if mode == "walk" else 0.0
    print(f"[play_demo] mode={mode}, vx_cmd={vx_cmd:.2f} m/s, num_envs={env_cfg.env.num_envs}, headless={args.headless}")

    # 清除命令随机重采样（固定命令，不随 episode 重采样）
    env.commands[:] = torch.tensor([vx_cmd, 0.0, 0.0, 0.0], device=env.device)

    sim_dt = env.dt  # policy 步长（decimation 之后）
    n_steps = demo_args.steps
    n_robots = env_cfg.env.num_envs

    # 统计量
    vx_actual = torch.zeros(n_steps, n_robots, device=env.device)
    pos_x = torch.zeros(n_steps, n_robots, device=env.device)
    pos_y = torch.zeros(n_steps, n_robots, device=env.device)
    falls = torch.zeros(n_robots, device=env.device)
    ep_lens = torch.zeros(n_robots, device=env.device)
    dead_robots = torch.zeros(n_robots, dtype=torch.bool, device=env.device)

    for i in range(n_steps):
        actions = policy(obs.detach())
        obs, _, rews, dones, infos = env.step(actions.detach())
        # 每步重新固定命令（防止 env 内部重采样覆盖）
        env.commands[:] = torch.tensor([vx_cmd, 0.0, 0.0, 0.0], device=env.device)
        vx_actual[i] = env.base_lin_vel[:, 0]
        pos_x[i] = env.root_states[:, 0]
        pos_y[i] = env.root_states[:, 1]
        # 记录摔倒（新 episode 意味着该机器人掉线/超时，记录一下）
        if torch.any(dones):
            new_eps = dones & ~dead_robots
            falls[new_eps] += 1
            dead_robots |= dones

    # ---- 结果统计 ----
    vx_actual_mean = vx_actual.mean(dim=0)
    vx_error = torch.abs(vx_actual_mean - vx_cmd)
    # 距离：episode 内相对位移（按速度累计，不受重置/初始位置影响）
    dist = (vx_actual.abs() * sim_dt).sum(dim=0)  # 沿 x 轴的累计行进距离
    ep_len_mean = env.episode_length_buf.float().mean().item()

    print("=" * 60)
    print(f"[play_demo] 结果（{n_steps} policy 步 ≈ {n_steps * sim_dt:.1f} s 仿真时间）")
    print(f"  机器人数量: {n_robots}")
    print(f"  实际平均线速度 vx: {vx_actual_mean.mean().item():.3f} m/s")
    print(f"  速度跟踪误差 |vx_cmd - vx|: {vx_error.mean().item():.4f} m/s")
    print(f"  平均行走距离: {dist.mean().item():.2f} m")
    print(f"  平均 episode 长度: {ep_len_mean:.0f} 步（20s 上限 = {env.max_episode_length} 步）")
    print(f"  摔倒/重置次数: {falls.sum().item()} / {n_robots}")
    print(f"  vx 达标的机器人占比（误差<0.2）: {(vx_error < 0.2).float().mean().item() * 100:.0f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
