#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 TensorBoard events 提取训练曲线并保存为 PNG（考核交付物：训练奖励曲线）。

用法:
    python scripts/plot_curves.py <run_log_dir> [--out results/curves/xxx.png] [--title 名称]

指标说明:
    Train/mean_reward             总奖励
    Train/mean_episode_length     平均 episode 长度（上限 1001 步 = 20s）
    Episode/rew_tracking_lin_vel  速度跟踪奖励（学会走路的核心指标）
    Episode/rew_tracking_ang_vel  角速度跟踪奖励
    Episode/terrain_level         地形难度等级（课程学习进度）
    Policy/mean_noise_std         动作噪声标准差（收敛时下降）
"""
import argparse
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


def load_scalar(ea, tag):
    events = ea.Scalars(tag)
    return [e.step for e in events], [e.value for e in events]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logdir", help="TensorBoard 事件目录")
    ap.add_argument("--out", default=None, help="输出 PNG 路径")
    ap.add_argument("--title", default="", help="图标题（建议用英文，避免无中文字体）")
    ap.add_argument("--smooth", type=float, default=0.9, help="指数平滑系数")
    args = ap.parse_args()

    ea = EventAccumulator(args.logdir)
    ea.Reload()
    tags = ea.Tags()["scalars"]

    def plot(tag, subplot, ylabel, color="C0"):
        if tag not in tags:
            return
        x, y = load_scalar(ea, tag)
        ax = subplot
        ax.plot(x, y, alpha=0.25, color=color, linewidth=0.8)
        # 指数平滑
        ys, last = [], None
        for v in y:
            last = v if last is None else args.smooth * last + (1 - args.smooth) * v
            ys.append(last)
        ax.plot(x, ys, color=color, linewidth=1.6)
        ax.set_xlabel("Iteration")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.set_title(tag.split("/")[-1])

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()
    plot("Train/mean_reward", axes[0], "reward", "C0")
    plot("Train/mean_episode_length", axes[1], "steps", "C1")
    plot("Episode/rew_tracking_lin_vel", axes[2], "reward", "C2")
    plot("Episode/rew_tracking_ang_vel", axes[3], "reward", "C3")
    plot("Episode/terrain_level", axes[4], "level", "C4")
    plot("Policy/mean_noise_std", axes[5], "std", "C5")
    if args.title:
        fig.suptitle(args.title, fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    out = args.out or "curves.png"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"曲线已保存: {out}")


if __name__ == "__main__":
    main()
