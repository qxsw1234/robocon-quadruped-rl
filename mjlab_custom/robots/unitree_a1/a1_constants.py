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
# Actuator config.
#
# 与 mjlab 自带 Go1 相同的推导方案（转子惯量 × 减速比 → 10Hz 自然频率 → PD 增益）。
# 之前用 legged_gym 的 kp=20/kd=0.5 阻尼过低（Go1 为 1.0~2.3），关节振荡导致
# 走路失控、策略退化为"站着不动"的局部最优。
##

NATURAL_FREQ = 10 * 2.0 * 3.1415926535  # 10Hz（与 Go1 一致）
DAMPING_RATIO = 2.0

# Unitree A1 电机参数（公开资料近似值）
ROTOR_INERTIA = 0.000111842  # 与 Go1 相同（对照实验 v4）
HIP_GEAR_RATIO = 6.0  # 与 Go1 相同（对照实验 v4）
KNEE_GEAR_RATIO = 9.0  # 与 Go1 相同（对照实验 v4）


def _reflected_inertia(inertia: float, gear: float) -> float:
  return inertia * gear * gear


HIP_REFLECTED = _reflected_inertia(ROTOR_INERTIA, HIP_GEAR_RATIO)
KNEE_REFLECTED = _reflected_inertia(ROTOR_INERTIA, KNEE_GEAR_RATIO)

A1_HIP_ACTUATOR_CFG = BuiltinPositionActuatorCfg(
  target_names_expr=(r".*_hip_joint", r".*_thigh_joint"),
  stiffness=HIP_REFLECTED * NATURAL_FREQ**2,
  damping=2 * DAMPING_RATIO * HIP_REFLECTED * NATURAL_FREQ,
  effort_limit=33.5,  # [Nm] Unitree A1 电机峰值力矩
  armature=HIP_REFLECTED,
)
A1_KNEE_ACTUATOR_CFG = BuiltinPositionActuatorCfg(
  target_names_expr=(r".*_calf_joint",),
  stiffness=KNEE_REFLECTED * NATURAL_FREQ**2,
  damping=2 * DAMPING_RATIO * KNEE_REFLECTED * NATURAL_FREQ,
  effort_limit=33.5,
  armature=KNEE_REFLECTED,
)

##
# Keyframes.
#
# 注意：init_state.pos 是 free joint（trunk body 原点）的世界位置。
# menagerie a1.xml 的 trunk body 自带 pos="0 0 0.43" 偏移，其 home keyframe
# 的 free joint z=0.27（脚着地的站姿）。之前误用 legged_gym 的 0.42 导致
# 机器人悬空 ~0.57m 自由落体（能站稳但学不会走）。
##

INIT_STATE = EntityCfg.InitialStateCfg(
  pos=(0.0, 0.0, 0.27),  # menagerie home keyframe 站姿高度
  joint_pos={
    r".*thigh_joint": 0.9,
    r".*calf_joint": -1.8,
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
