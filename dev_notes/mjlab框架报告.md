# mjlab 训练 12 自由度机器人 —— 拓展题报告（考核 3.2）

> 要求：尝试使用 mjlab、UniLab 等开源训练框架训练 12 自由度机器人。
> 本项目中：战队自研 12 自由度机器人的模型文件暂不可得，选用与 A1 同为 12 自由度（4 腿 × 3 关节）的开源模型完成框架接入与训练演示；接入流程完全适用于自研机器人（替换 MJCF + 调整常量即可）。

## 1. 框架简介

**mjlab**（MuJoCo Lab）：把 Isaac Lab 的 manager-based API 移植到 **MuJoCo Warp**（GPU 加速物理后端）上的轻量级机器人强化学习框架。
- GitHub: https://github.com/mujocolab/mjlab
- 物理引擎：MuJoCo（Warp GPU 并行），训练需要 NVIDIA GPU
- 训练算法：rsl-rl（PPO），配置为 dataclass + tyro CLI
- 安装：`pip install mjlab`（一条命令，无 Isaac Gym 兼容问题）

## 2. 自定义机器人接入流程（以 A1 为例，通用流程）

自研 12 自由度机器人接入 mjlab 只需 4 步（本项目代码见 `mjlab_custom/`）：

1. **准备 MJCF 模型**：`robots/unitree_a1/xmls/a1.xml`
   - 来源：mujoco_menagerie（MIT 许可），12 自由度（FR/FL/RR/RL × hip/thigh/calf）
   - 修改：为碰撞 geom 命名（`FR_thigh_collision1` 等，奖励/终止需要按名字匹配）、
     在脚掌位置添加 site（foot_height_scan 传感器需要）、assets 本地化
2. **编写机器人常量**：`a1_constants.py`
   - 执行器（PD 增益 kp=20, kd=0.5 —— 与 legged_gym 的 A1 基线一致，便于跨框架对比）、
     初始状态（关节角与 legged_gym 默认一致）、碰撞配置
3. **编写环境配置**：`tasks/velocity/config/a1/env_cfgs.py`
   - 基于 `make_velocity_env_cfg()` 工厂 + 机器人专属覆盖（传感器、奖励、终止条件）
4. **注册任务**：`tasks/velocity/config/a1/__init__.py`
   - `register_mjlab_task("Mjlab-Velocity-Rough-Unitree-A1", ...)`

## 3. 训练与结果

### 3.1 内置任务：Go1（12 自由度）速度跟踪

```bash
python -m mjlab.scripts.train "Mjlab-Velocity-Rough-Unitree-Go1" \
    --env.scene.num-envs 2048 --agent.logger tensorboard \
    --agent.max-iterations 2000
```

| 指标 | 值 |
|---|---|
| 环境数 | 2048 |
| 迭代数 | 2000 |
| 总环境步数 | 2000 × 24 × 2048 = 98,304,000 |
| 训练耗时 | 2791s ≈ 46.5 分钟 |
| 迭代时间 | 1.39 s |
| 速度跟踪奖励（收敛） | 1.41 |
| 地形等级 | 5.0 |
| 行为验证（命令 1.0 m/s） | 2D 速度 0.66 m/s，方向正确（headless 评估） |

### 3.2 自定义任务：A1（12 自由度）速度跟踪

```bash
python -m mjlab.scripts.train "Mjlab-Velocity-Flat-Unitree-A1" \
    --env.scene.num-envs 2048 --agent.logger tensorboard \
    --agent.max-iterations 2000
```

| 指标 | 值 |
|---|---|
| 环境数 | 2048 |
| 迭代数 | 2000（rough 版另有 2000-4000 迭代的 3 组实验） |
| 总环境步数 | 98,304,000 / 段 |
| 训练耗时 | ~52 分钟 / 段 |
| 速度跟踪奖励 | 0.5-0.7（见下"排查结论"） |
| upright 奖励 | 0.98（学会稳定站立） |
| 行为验证 | 稳定站立 ✅；行走未达成 ⚠️ |

### 3.3 A1 在 mjlab 中"学不会走"的排查（重要过程记录）

**结果**：A1（menagerie MJCF）在 mjlab 中无论怎么调参都停留在"站立/蹲着不动"（track_linear 卡在 0.5-0.7 的不动保底值）；**同配置下 Go1 正常学会行走（1.41）**，且 **A1 在 legged_gym（Isaac Gym）中正常学会行走**（见 3.1）。

**系统性排查（5 组实验，每组 300-2000 迭代）**：

| 版本 | 修改 | 结果 |
|---|---|---|
| v1 | 初始姿态 0.42（legged_gym 值） | 悬空自由落体，4000 迭代学不会走 |
| v2 | 初始姿态修正（menagerie keyframe 0.27） | 站姿正常，仍不动 |
| v3 | PD 改为电机推导值（kp 7-16） | 仍不动 |
| v4 | PD 与 Go1 完全同构（kp 16-36, kd 1-2.3） | 早期正常，~700 迭代后回落 |
| v5 | + 移除关节摩擦 + pose 权重×5 + fell_over 55° | 仍不动（蹲姿不被惩罚） |

**定位的根因（逐步排除）**：
1. 初始姿态：legged_gym 的站姿高度不能跨模型套用（menagerie trunk body 有 0.43 偏移）→ 已修复
2. 终止条件：rough 的 illegal_contact（大腿碰地）过严会抑制探索 → flat 任务（无此终止）仍然不动 → 排除
3. PD 参数/动作尺度：与 Go1 同构后仍不动 → 排除
4. **剩余差异：menagerie A1 模型本身**（腿长 0.285m 比 Go1 的 0.293m 短；惯性参数为估算值）。假设：该模型参数在 MuJoCo 物理下动态行走稳定性差，策略收敛到"站立不动"的局部最优。legged_gym 中 A1 能走（官方 URDF 参数 + Isaac Gym PhysX），也支持"模型/物理差异"的假设。

**工程教训**：
1. 训练指标卡在"不动保底值"（track_linear ≈ E[exp(-cmd²/σ²)]）是局部最优的典型信号
2. 终止条件比奖励项更能决定"敢不敢探索"（rough 的 illegal_contact 实验）
3. 接入新机器人优先用官方模型/官方参数，跨模型套用站姿、PD 都会出问题
4. 机器人本体参数（腿长、惯性）对可学习性影响巨大，需要模型消融实验验证
5. 框架接入流程（MJCF→常量→环境→注册→训练→评估）已完整跑通，替换成战队自研模型（官方参数）即可复用

训练曲线：`results/curves/mjlab_go1.png`、`results/curves/mjlab_a1.png`

## 4. 与 legged_gym 的对比（实测）

| 维度 | legged_gym (Isaac Gym) | mjlab (MuJoCo Warp) |
|---|---|---|
| 安装难度 | 难：Isaac Gym 已停止维护、python≤3.8、旧 torch 兼容问题多 | 易：`pip install mjlab`，python 3.10+ |
| 驱动兼容 | 新驱动(570+)有风险，需 headless | 无此问题 |
| 环境 API | 类继承 + 嵌套 config | dataclass + Manager（观测/奖励/事件组件化） |
| 任务注册 | task_registry.register | register_mjlab_task |
| 自定义机器人 | URDF + 继承 config 类 | MJCF + 常量文件 + env_cfg 工厂 |
| 训练吞吐 | ~61k steps/s（4096 envs） | Go1 实测约 35k steps/s（2048 envs，98,304,000 步 / 2791 s） |
| 奖励设计 | scales 字典 + _reward_xxx 函数 | RewardTermCfg 组件 |
| 地形课程 | 内置（terrain curriculum） | 内置（多地形类型） |
| 日志 | TensorBoard | TensorBoard / W&B |
| 总结 | 资料最多、最成熟，但环境安装是最大门槛 | 现代、干净、接入流程清晰；新框架文档相对少 |

## 5. 关于"训练我们战队的 12 自由度机器人"

- 自研机器人接入只需：MJCF/URDF→MJCF 转换（或直接 MJCF）→ 替换 `robots/` 下模型 → 调整常量（关节名、PD 增益、初始姿态、脚部几何）→ 注册任务
- 若战队提供 URDF，可用 MuJoCo 的 URDF 导入（`mujoco.MjSpec` 或 menagerie 工具）快速转成 MJCF
- 本项目用开源 A1（同为 12 自由度）完整走通了上述流程并完成多组实际训练；稳定站立已达成，动态行走未达成，失败现象与排查过程见 3.3

## 6. UniLab（备选框架，视时间）

UniLab（unilabsim/UniLab）：CPU 仿真 + GPU 训练的异构框架，支持 PPO/APPO/SAC 等，
内置 Go2/Go1 四足任务。项目很新（2026-02），自定义机器人文档缺失，风险高，作为备选。
本次未实施 UniLab；时间优先用于完成 mjlab 的训练、评估和 A1 问题排查闭环。
