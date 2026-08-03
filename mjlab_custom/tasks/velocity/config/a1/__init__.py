"""Unitree A1 velocity task registration (mjlab 自定义机器人接入, 考核 3.2)。"""

from mjlab.tasks.registry import register_mjlab_task
from mjlab.tasks.velocity.rl import VelocityOnPolicyRunner

from .env_cfgs import (
  unitree_a1_flat_env_cfg,
  unitree_a1_rough_env_cfg,
)
from .rl_cfg import unitree_a1_ppo_runner_cfg

register_mjlab_task(
  task_id="Mjlab-Velocity-Rough-Unitree-A1",
  env_cfg=unitree_a1_rough_env_cfg(),
  play_env_cfg=unitree_a1_rough_env_cfg(play=True),
  rl_cfg=unitree_a1_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Mjlab-Velocity-Flat-Unitree-A1",
  env_cfg=unitree_a1_flat_env_cfg(),
  play_env_cfg=unitree_a1_flat_env_cfg(play=True),
  rl_cfg=unitree_a1_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)
