#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""多 run 训练曲线叠加对比（奖励实验分析用）。

用法:
    python scripts/plot_compare.py <run1_dir> <run2_dir> ... --labels 基线 实验A 实验B --out out.png [--tags Train/mean_reward Episode/rew_tracking_lin_vel]
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
    ap.add_argument("logdirs", nargs="+")
    ap.add_argument("--labels", nargs="+", default=None)
    ap.add_argument("--out", default="compare.png")
    ap.add_argument("--tags", nargs="+", default=[
        "Train/mean_reward",
        "Train/mean_episode_length",
        "Episode/rew_tracking_lin_vel",
        "Episode/terrain_level",
    ])
    ap.add_argument("--smooth", type=float, default=0.9)
    args = ap.parse_args()

    labels = args.labels or [os.path.basename(d) for d in args.logdirs]
    colors = ["C0", "C1", "C2", "C3", "C4", "C5"]

    eas = []
    for d in args.logdirs:
        ea = EventAccumulator(d)
        ea.Reload()
        eas.append(ea)

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    axes = axes.flatten()

    for ax, tag in zip(axes, args.tags):
        for ea, label, c in zip(eas, labels, colors):
            if tag not in ea.Tags()["scalars"]:
                continue
            x, y = load_scalar(ea, tag)
            ax.plot(x, y, alpha=0.15, color=c, linewidth=0.6)
            ys, last = [], None
            for v in y:
                last = v if last is None else args.smooth * last + (1 - args.smooth) * v
                ys.append(last)
            ax.plot(x, ys, color=c, linewidth=1.6, label=label)
        ax.set_xlabel("Iteration")
        ax.set_ylabel(tag.split("/")[-1])
        ax.set_title(tag.split("/")[-1])
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)

    fig.suptitle("Reward experiment comparison (A1, 1500 iters each)", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(args.out, dpi=150)
    print(f"对比图已保存: {args.out}")


if __name__ == "__main__":
    main()
