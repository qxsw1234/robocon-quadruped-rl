# 四足机器人强化学习训练 —— 视觉组正式队员考核（方向三）

> 考核题目 3.1：四足机器人站立与速度跟踪（Unitree A1，legged_gym 框架）
> 考核题目 3.2：mjlab / UniLab 框架训练 12 自由度机器人（拓展）

## 项目简介

使用强化学习（PPO）在 Isaac Gym 中训练 Unitree A1 四足机器人完成：
- **稳定站立**（命令速度 = 0）
- **直线行走**（命令速度 vx = 1.0 m/s）

训练基于 ETH RSL 的 [legged_gym](https://github.com/leggedrobotics/legged_gym) + [rsl_rl](https://github.com/leggedrobotics/rsl_rl)（v1.0.2）框架，4096 并行环境、GPU 物理仿真。

## 环境要求

| 组件 | 版本 |
|---|---|
| 操作系统 | Ubuntu 22.04 |
| GPU | NVIDIA RTX 4060 Laptop（8GB 显存，sm_89） |
| 驱动 | 580.173.02（CUDA 13.0 驱动，向前兼容） |
| Python | 3.8（Isaac Gym 二进制硬性要求 ≤3.8 ABI） |
| PyTorch | 2.3.1+cu121（40 系显卡必需 ≥2.x，官方 README 的 1.10+cu113 会报 nvrtc 错误） |
| Isaac Gym | Preview 4 (2022.2.1) |
| legged_gym | 1.0.0 |
| rsl_rl | v1.0.2（注意：main 分支 5.x 新版 API 不兼容） |

## 安装步骤

```bash
# 1. conda 环境（Isaac Gym 需要 python ≤3.8）
conda create -n leg python=3.8 -y
conda activate leg

# 2. PyTorch（国内用阿里云镜像，官方源极慢）
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cu121
# 或: pip install ./pkg/torch-2.3.1+cu121-cp38-cp38-linux_x86_64.whl

# 3. Isaac Gym Preview 4（官方需 NVIDIA 账号，见 https://developer.nvidia.com/isaac-gym）
pip install -e ./isaacgym/python --no-deps
pip install "numpy==1.23.5" scipy pyyaml pillow imageio ninja matplotlib tensorboard

# 4. rsl_rl v1.0.2（旧版 API）
cd rsl_rl && git checkout v1.0.2 && pip install -e . --no-deps --no-build-isolation

# 5. legged_gym
pip install -e ./legged_gym --no-deps

# 6. 每次运行前设置（libpython 找不到的修复）
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
# 已封装: source scripts/leg_env.sh
```

## 训练

```bash
# 基线训练（A1，粗糙地形，4096 环境，1500 迭代，headless）
cd legged_gym/legged_gym/scripts
source ../../scripts/leg_env.sh
python train.py --task=a1 --num_envs=4096 --max_iterations=1500 --headless

# 查看训练曲线
tensorboard --logdir ../../logs/rough_a1
```

## 演示 / 评估

```bash
# 稳定站立（命令速度 0，1000 步）
python scripts/play_demo.py --task=a1 --mode=stand --steps=1000 --num_envs=16

# 直线行走（命令 vx=1.0 m/s，1000 步），输出速度跟踪误差/距离/摔倒统计
python scripts/play_demo.py --task=a1 --mode=walk --vx=1.0 --steps=1000 --num_envs=16

# 带画面回放（录屏用）
python legged_gym/legged_gym/scripts/play.py --task=a1
```

## 训练结果

| 指标 | 值 |
|---|---|
| 总环境步数 | 基线 294,912,000（3000 迭代 × 24 步 × 4096 环境）；实验各 147,456,000 |
| 训练耗时 | 基线 70 分钟（两段）；实验各 35-47 分钟（RTX 4060 Laptop） |
| 吞吐 | ~61k steps/s（4096 并行环境） |
| 站立 | 命令 0 时零摔倒，速度误差 0.003 m/s |
| 平地行走（vx=1.0） | **0.999 m/s，误差 0.35%，100% 达标** |
| 粗糙地形行走（vx=1.0） | 0.88-0.95 m/s，84% 达标（32 机器人统计） |
| 演示视频 | results/videos/（站立 / 平地行走 / 粗糙地形行走） |

训练曲线见 [results/curves/](results/curves/)，奖励实验见 [dev_notes/奖励实验分析.md](dev_notes/奖励实验分析.md)，训练原理见 [dev_notes/训练原理说明.md](dev_notes/训练原理说明.md)。

## 演示视频

| 视频 | 内容 | 命令 |
|---|---|---|
| `results/videos/demo_stand.mp4` | 稳定站立（平地，4 机器人，12s） | vx=0 |
| `results/videos/demo_walk.mp4` | 直线行走（平地，4 机器人，12s） | vx=1.0 m/s |
| `results/videos/demo_walk_rough.mp4` | 粗糙地形行走（含坡道/台阶） | vx=1.0 m/s |

录制方式：`python scripts/play_demo.py --task=a1 --mode=walk --vx=1.0 --flat`（viewer 回放）+ ffmpeg 录屏，见 `scripts/record_demo.sh`。

## 奖励实验（考核要求 5）

见 [dev_notes/奖励实验分析.md](dev_notes/奖励实验分析.md)：
- 实验 A：移除 tracking_lin_vel 奖励 → 机器人不前进
- 实验 B：移除 feet_air_time 奖励 → 步态拖脚僵化
- 实验 C：增大 torques 惩罚 → 动作幅度减小、速度下降

## 目录结构

```
├── legged_gym/        # 训练主框架（含 A1 配置与修改）
├── rsl_rl/            # PPO 算法库（v1.0.2）
├── scripts/           # 自定义脚本（演示/评估、环境激活）
├── dev_notes/         # 开发记录、训练原理、奖励实验分析
├── results/           # 训练曲线、截图、演示视频
└── pkg/               # Isaac Gym Preview 4 安装包
```

## 致谢

- [legged_gym](https://github.com/leggedrobotics/legged_gym)（ETH RSL）
- [rsl_rl](https://github.com/leggedrobotics/rsl_rl)（ETH RSL）
- [Isaac Gym](https://developer.nvidia.com/isaac-gym)（NVIDIA）
- 题目参考仓库：HIMLoco、elmap-rl-controller、extreme-parkour
