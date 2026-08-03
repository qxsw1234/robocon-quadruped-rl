# 四足机器人强化学习考核任务执行计划（3.1 普通题 + 3.2 拓展题）

## 背景与决策（已确认）
- **任务**：3.1 用强化学习训练四足机器人稳定站立 + 直线行走，提供训练曲线、步数/时间记录、奖励项修改对比分析、训练原理说明；3.2 加分项用 mjlab/UniLab 训练 12 自由度机器人。
- **硬件**：RTX 4060 Laptop 8GB 显存、驱动 580.173.02（很新）、Ubuntu 22.04、31GB 内存、磁盘剩余 59GB、miniconda 可用。
- **已确认决策**：3.1 用 **A1**（legged_gym 原生支持、社区验证充分）；3.2 无战队模型文件 → 用**开源 12 自由度模型（A1/Go1/Go2）**演示框架接入；Isaac Gym 若在驱动 580 上失败 → **切换 mjlab** 完成 3.1（题目允许自选环境，"推荐"非强制）。
- **截止**：2026-08-30 23:59，压缩包 `视觉组正式队员考核-年级-专业-姓名.zip` 发至 1102350166@qq.com。
- **红线**：必须真训练（或公开模型上继续训练），禁止只跑预训练模型；代码必须能解释。

## 关键技术方案
- **主力路径**：conda Python 3.8 + torch 2.3.1+cu121 + Isaac Gym Preview 4 + 原版 legged_gym（`--task=a1`）。
  - 依据：Isaac Gym 二进制只支持 Python ≤3.8 ABI；官方 README 的 torch 1.10+cu113 在 40 系显卡必报 nvrtc 错误，社区验证组合即 python 3.8 + torch 2.3.x+cu121，4060/4060Ti 上有成功案例；驱动 570+ 有 Vulkan/coredump 报告 → 一律用 `--headless` 训练规避渲染问题。
  - HIMLoco（题目首个参考仓库）同样基于 legged_gym，作为进阶/备选（其 `a1/go1` 配置可直接用，但 HIMPPO 训练量更大）。
- **备选路径**：mjlab（MuJoCo Warp，无 Isaac Gym 兼容问题、安装一条命令、内置 Go1 速度跟踪任务），同时服务于 3.2。
- **显存约束**：8GB → `--num_envs=1024~2048`（默认 4096 需 ~12GB），训练时间相应拉长，夜间挂机训练。

## 执行阶段（今天 8/3，共 4 周）

### Phase 0：准备工作（半天，第1天）
- 创建 GitHub 仓库（提交物要求完整源码仓库），初始化 README 与目录结构
- 建立开发记录（markdown 开发日志：报错、截图、决策、AI 工具使用说明——考核明确要求）
- 获取 Isaac Gym Preview 4 安装包：需要 **NVIDIA 开发者账号**下载，请提前注册或提供安装包；若 2 天内拿不到 → 直接切 mjlab 主路径
- 补齐全局要求：个人情况调查表、ROS2 学习笔记（若未完成，安排碎片时间补）

### Phase 1：环境搭建 + 冒烟测试（第1-2天）
- `conda create -n leg python=3.8`；安装 torch 2.3.1+cu121、numpy<1.24、tensorboard；Isaac Gym Preview 4 `pip install -e`；clone legged_gym + rsl_rl 并 `pip install -e`
- **冒烟测试（风险门控点）**：`train.py --task=a1 --num_envs=512 --max_iterations=100 --headless`，检查：不崩溃、GPU 正常、tensorboard 曲线出现、显存占用
- 测试 play.py 回放流程（站立 + 速度命令）
- **门控决策**：Isaac Gym 失败 → 按已确认决策切换 mjlab（安装 + 跑通 Velocity-Go1-v0 demo），3.1 全程用 mjlab 完成，计划后续阶段不变
- 记录所有报错与解决方案进开发日志

### Phase 2：基础训练（3.1 核心，第2-6天，含挂机时间）
- 正式训练：`train.py --task=a1 --num_envs=1024~2048 --max_iterations=3000~5000 --headless`
- 记录**训练步数**（iterations × num_steps_per_env × num_envs 换算总环境步数）与**训练耗时**
- 采集训练曲线：tensorboard 的 total reward 与分项（tracking_lin_vel、lin_vel_z、feet_air_time、torques、action_rate 等）截图存档
- 收敛后验证演示（录屏素材）：
  - **稳定站立**：play.py 加载 checkpoint，命令速度 = 0（配合 stand_still 奖励项），录制 10-20 秒
  - **直线行走**：脚本设置 vx ≈ 1.0 m/s 直线前进（小改 play.py 的 command 逻辑并记录），录制 10-20 秒
- 若 3000-5000 迭代未走稳：增大迭代数/微调参数续训（继续训练同样符合题目要求）

### Phase 3：奖励项修改实验（3.1 要求5，第7-10天）
- 修改位置：`legged_gym/envs/base/legged_robot_config.py` 的 `rewards.scales` + 机器人级 `a1_config.py`；奖励函数在 `legged_robot.py` 的 `_reward_xxx()`
- 设计 3 组对比（同迭代数、同随机种子，控制变量）：
  - 实验A：删除/降低 tracking_lin_vel 权重 → 预期：速度跟踪变差、不前进
  - 实验B：删除 feet_air_time → 预期：步态拖脚、僵化
  - 实验C：加大 torques 惩罚 → 预期：动作省力但变慢/幅度变小
- 每组训练后叠加对比曲线图，写**分析**（奖励 = 行为目标信号，权重失衡 → 行为退化的机理）
- 产出：对比曲线图 + 分析段落（进报告和开发记录）

### Phase 4：训练原理总结（3.1 要求6，与 Phase 2/3 并行）
- 成文内容：PPO 算法（actor-critic、GAE、clip）、观测/动作空间（A1 约 45 维观测、12 关节位置增量动作）、奖励各项含义、域随机化（地形课程、摩擦/质量扰动）、rsl_rl 训练循环（OnPolicyRunner）、HIMLoco 的 HIMPPO 改进（可选了解）
- 产出：报告章节 + 答辩时能讲清楚每个环节

### Phase 5：3.2 拓展题（加分，第11-17天）
- **mjlab 为主**：安装 → 训练内置 Go1 速度跟踪任务（`Velocity-Go1-v0`，12 自由度）→ 出曲线
- **自定义机器人接入演示**：用开源 A1 的 MJCF（mujoco_menagerie 有 unitree_a1）注册自定义环境（MJCF 替换 + config 继承 + 复用 legged_gym 风格奖励），体现"接入自己的 12 自由度机器人"完整流程
- **UniLab 视时间**：跑 `go2_joystick_flat`（Go2 12 自由度摇杆平地任务），对比三种框架差异（仿真器、API、安装、训练速度）写进报告
- 产出：曲线 + 框架对比心得

### Phase 6：交付与提交（第18-24天，留 1 周缓冲）
- 演示视频：站立 + 直线行走录屏（ffmpeg/系统录屏，sim 回放画面 + 命令窗口佐证）
- 整理 GitHub 仓库：源码 + README（环境、训练命令、结果、曲线）+ 开发记录 + 分析文档
- 检查考核要求逐项对照（1-6 条 + 3.2）确认无遗漏
- 打包 `视觉组正式队员考核-年级-专业-姓名.zip` 发送至 1102350166@qq.com
- 缓冲期用于补拍视频、修 bug、补充分析

## 风险与应对
| 风险 | 应对 |
|---|---|
| Isaac Gym 与驱动 580 不兼容 | 门控点提前测试；失败即切 mjlab（已确认） |
| 8GB 显存不足 | num_envs 降至 1024-2048，headless；显存不够再降 |
| 训练不收敛/走不稳 | 加大迭代数、调 num_envs、检查奖励曲线定位问题；备选 HIMLoco |
| Isaac Gym 下载需要 NVIDIA 账号 | 提前注册；拿不到则 mjlab 路径不受影响 |
| 磁盘 59GB | legged_gym 日志 + conda 环境共 ~15-20GB，足够；定期清理旧日志 |
| 时间紧张 | 训练全部夜间挂机；计划预留第4周整周缓冲 |

## 需要你配合的事项
1. 注册/提供 **NVIDIA 开发者账号**（或 Isaac Gym Preview 4 安装包），用于 Isaac Gym 下载
2. 提供 GitHub 账号信息（或授权我用 gh CLI 创建仓库）
3. 提供 年级-专业-姓名（压缩包命名用）
4. 若战队后续拿到自研机器人 URDF，随时可替换 3.2 中的开源模型

## 最终交付物清单
- GitHub 仓库（完整源码 + README + 训练曲线 + 分析文档）
- 训练奖励曲线图（基线 + 3 组奖励对比）
- 训练步数/时间记录表
- 站立 + 直线行走演示视频
- 开发过程记录（含报错、失败案例、AI 使用说明）
- 训练原理说明文档
- 3.2 拓展：mjlab 曲线 + 自定义机器人接入演示（UniLab 视时间）
- 考核压缩包邮件提交