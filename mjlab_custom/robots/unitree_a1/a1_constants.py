"""Unitree A1 constants for mjlab (custom robot integration, 川山甲战队考核项目).

模仿 mjlab 自带的 unitree_go1/go1_constants.py 结构，接入 Unitree A1（12 自由度四足）。
模型来源: mujoco_menagerie 的 unitree_a1（MIT 许可），已修改：为碰撞 geom 命名、
meshdir/texturedir 指向本地 assets。
PD 增益与 legged_gym 的 A1RoughCfg 一致（kp=20 N·m/rad, kd=0.5），便于两个框架结果对比。
"""

from pathlib import Path

import mujoco

from mjlab.actuator import BuiltinPositionActuatorCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.utils.spec_config import CollisionCfg

##
# MJCF and assets.
##

A1_XML: Path = Path(__file__).resolve().parent / "xmls" / "a1.xml"
assert A1_XML.exists(), f"A1 MJCF not found: {A1_XML}"


def get_spec() -> mujoco.MjSpec:
  return mujoco.MjSpec.from_file(str(A1_XML))


##
# Actuator config (与 legged_gym A1RoughCfg 一致: stiffness=20, damping=0.5).
##

A1_STIFFNESS = 20.0   # [N*m/rad]
A1_DAMPING = 0.5      # [N*m*s/rad]
A1_EFFORT_LIMIT = 33.5  # [Nm] (Unitree A1 电机峰值力矩)

# 转子惯量/减速比（Unitree A1 公开资料，近似值，仅用于 armature）
ROTOR_INERTIA = 0.000046
HIP_GEAR_RATIO = 6.33
KNEE_GEAR_RATIO = 9.5


def _reflected_inertia(inertia: float, gear: float) -> float:
  return inertia * gear * gear


A1_HIP_ACTUATOR_CFG = BuiltinPositionActuatorCfg(
  target_names_expr=(r".*_hip_joint", r".*_thigh_joint"),
  stiffness=A1_STIFFNESS,
  damping=A1_DAMPING,
  effort_limit=A1_EFFORT_LIMIT,
  armature=_reflected_inertia(ROTOR_INERTIA, HIP_GEAR_RATIO),
)
A1_KNEE_ACTUATOR_CFG = BuiltinPositionActuatorCfg(
  target_names_expr=(r".*_calf_joint",),
  stiffness=A1_STIFFNESS,
  damping=A1_DAMPING,
  effort_limit=A1_EFFORT_LIMIT,
  armature=_reflected_inertia(ROTOR_INERTIA, KNEE_GEAR_RATIO),
)

##
# Keyframes（与 legged_gym A1 默认关节角一致）。
##

INIT_STATE = EntityCfg.InitialStateCfg(
  pos=(0.0, 0.0, 0.42),
  joint_pos={
    r".*thigh_joint": 0.9,
    r".*calf_joint": -1.5,
    r".*R_hip_joint": -0.1,
    r".*L_hip_joint": 0.1,
  },
  joint_vel={r".*": 0.0},
)

##
# Collision config.
##

_foot_regex = r"^[FR][LR]_foot$"

# 除脚以外禁用所有碰撞；脚之间自碰撞禁用。
FEET_ONLY_COLLISION = CollisionCfg(
  geom_names_expr=(_foot_regex,),
  contype=0,
  conaffinity=1,
  condim=3,
  priority=1,
  friction=(0.6,),
  solimp=(0.9, 0.95, 0.023),
)

# 启用所有碰撞，脚给自定义 condim/friction。
FULL_COLLISION = CollisionCfg(
  geom_names_expr=(r".*_collision",),
  solref=(0.01, 1),
  condim={_foot_regex: 6, r".*_collision": 1},
  priority={_foot_regex: 1},
  friction={_foot_regex: (1, 5e-3, 5e-4)},
)

##
# Final config.
##

A1_ARTICULATION = EntityArticulationInfoCfg(
  actuators=(
    A1_HIP_ACTUATOR_CFG,
    A1_KNEE_ACTUATOR_CFG,
  ),
  soft_joint_pos_limit_factor=0.9,
)


def get_a1_robot_cfg() -> EntityCfg:
  """Get a fresh A1 robot configuration instance."""
  return EntityCfg(
    init_state=INIT_STATE,
    collisions=(FULL_COLLISION,),
    spec_fn=get_spec,
    articulation=A1_ARTICULATION,
  )


A1_ACTION_SCALE: dict[str, float] = {}
for a in A1_ARTICULATION.actuators:
  assert isinstance(a, BuiltinPositionActuatorCfg)
  e = a.effort_limit
  s = a.stiffness
  names = a.target_names_expr
  assert e is not None
  for n in names:
    A1_ACTION_SCALE[n] = 0.25 * e / s
