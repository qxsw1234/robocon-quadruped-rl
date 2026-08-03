#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mjlab 训练策略的 headless 行为评估（对应 legged_gym 的 play_demo.py）。

用法:
    python mjlab_custom/eval_mjlab.py <task_id> <checkpoint.pt> [--vx 1.0] [--num-envs 16] [--steps 1000]

输出: 实际平均速度、速度跟踪误差、达标率、摔倒次数等。
"""
import argparse
import sys
import torch

import mjlab.tasks  # noqa: F401  (注册任务)
from dataclasses import asdict

from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.rl.runner import MjlabOnPolicyRunner
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", help="mjlab 任务 ID，如 Mjlab-Velocity-Rough-Unitree-A1")
    ap.add_argument("checkpoint", help="checkpoint .pt 文件路径")
    ap.add_argument("--vx", type=float, default=1.0, help="目标线速度 [m/s]（固定命令）")
    ap.add_argument("--num-envs", type=int, default=16)
    ap.add_argument("--steps", type=int, default=1000)
    args = ap.parse_args()

    device = "cuda:0"
    env_cfg = load_env_cfg(args.task, play=True)
    env_cfg.scene.num_envs = args.num_envs
    # play 模式接触对更多，扩大接触容量避免 nconmax overflow
    env_cfg.sim.nconmax = 500

    # 固定命令（把 twist 的采样范围改为单值）
    twist = env_cfg.commands["twist"]
    twist.ranges.lin_vel_x = (args.vx, args.vx)
    twist.ranges.lin_vel_y = (0.0, 0.0)
    twist.ranges.ang_vel_z = (0.0, 0.0)

    env = ManagerBasedRlEnv(cfg=env_cfg, device=device, render_mode=None)
    agent_cfg = load_rl_cfg(args.task)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    runner_cls = load_runner_cls(args.task) or MjlabOnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device=device)
    runner.load(args.checkpoint, load_cfg={"actor": True}, strict=True, map_location=device)
    policy = runner.get_inference_policy(device=device)

    obs = env.get_observations()
    robot = env.unwrapped.scene.entities["robot"]
    sim_dt = env.unwrapped.step_dt

    vx_records = torch.zeros(args.steps, args.num_envs, device=device)
    n_steps_alive = torch.zeros(args.num_envs, device=device)

    for i in range(args.steps):
        actions = policy(obs.detach())
        obs, rew, done, extras = env.step(actions.detach())
        vel = robot.data.root_link_vel_w[:, 0]  # 世界系线速度 x
        vx_records[i] = vel
        n_steps_alive += (1.0 - done.float())

    vx_mean = vx_records.mean(dim=0)
    vx_err = torch.abs(vx_mean - args.vx)
    dist = (vx_records.abs() * sim_dt).sum(dim=0)
    alive_frac = n_steps_alive / args.steps

    print("=" * 60)
    print(f"[eval_mjlab] task={args.task}")
    print(f"  checkpoint={args.checkpoint.split('/')[-1]}")
    print(f"  机器人数量: {args.num_envs}，{args.steps} policy 步 ≈ {args.steps*sim_dt:.1f}s")
    print(f"  实际平均线速度 vx: {vx_mean.mean().item():.3f} m/s")
    print(f"  速度跟踪误差 |vx_cmd-vx|: {vx_err.mean().item():.4f} m/s")
    print(f"  平均行进距离: {dist.mean().item():.2f} m")
    print(f"  全程存活比例: {alive_frac.mean().item()*100:.0f}%")
    print(f"  达标率（误差<0.2）: {(vx_err<0.2).float().mean().item()*100:.0f}%")
    print("=" * 60)
    env.close()


if __name__ == "__main__":
    main()
