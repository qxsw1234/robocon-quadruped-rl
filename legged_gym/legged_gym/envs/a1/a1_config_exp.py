# SPDX-FileCopyrightText: Copyright (c) 2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# Copyright (c) 2021 ETH Zurich, Nikita Rudin
# 川山甲战队考核项目 (2026)：奖励项修改实验配置
#
# 三个实验（均为单变量修改，其余与基线 A1RoughCfg 完全一致）：
#   实验A a1_no_vel_tracking : 移除速度跟踪奖励（tracking_lin_vel: 1.0 -> 0.0）
#   实验B a1_no_feet_air     : 移除抬脚时间奖励（feet_air_time: 1.0 -> 0.0）
#   实验C a1_high_torque_pen : 放大关节力矩惩罚（torques: -0.0002 -> -0.002，10 倍）

from legged_gym.envs.a1.a1_config import A1RoughCfg, A1RoughCfgPPO


# ---------------- 实验A：移除速度跟踪奖励 ----------------
class A1NoVelTrackingCfg(A1RoughCfg):
    class rewards(A1RoughCfg.rewards):
        class scales(A1RoughCfg.rewards.scales):
            tracking_lin_vel = 0.0   # 基线为 1.0


class A1NoVelTrackingCfgPPO(A1RoughCfgPPO):
    class runner(A1RoughCfgPPO.runner):
        experiment_name = 'rough_a1_no_vel_tracking'


# ---------------- 实验B：移除抬脚时间奖励 ----------------
class A1NoFeetAirCfg(A1RoughCfg):
    class rewards(A1RoughCfg.rewards):
        class scales(A1RoughCfg.rewards.scales):
            feet_air_time = 0.0      # 基线为 1.0


class A1NoFeetAirCfgPPO(A1RoughCfgPPO):
    class runner(A1RoughCfgPPO.runner):
        experiment_name = 'rough_a1_no_feet_air'


# ---------------- 实验C：放大关节力矩惩罚（10 倍） ----------------
class A1HighTorquePenCfg(A1RoughCfg):
    class rewards(A1RoughCfg.rewards):
        class scales(A1RoughCfg.rewards.scales):
            torques = -0.002         # A1 基线为 -0.0002


class A1HighTorquePenCfgPPO(A1RoughCfgPPO):
    class runner(A1RoughCfgPPO.runner):
        experiment_name = 'rough_a1_high_torque_pen'
