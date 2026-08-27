#!/usr/bin/env bash
# 生成包含三个考核方向的最终邮件提交 ZIP。

set -euo pipefail

QUADRUPED_ROOT="/home/czm/桌面/robocon"
APRILTAG_ROOT="/home/czm/apriltag_pose_ws"
NAV_ROOT="/home/czm/ros2_ws"
ARCHIVE_NAME="视觉组正式队员考核-2024级-测控技术与仪器-曹哲明"
FINAL_ZIP="$QUADRUPED_ROOT/$ARCHIVE_NAME.zip"
PREVIOUS_ZIP="$QUADRUPED_ROOT/$ARCHIVE_NAME.previous.zip"
STAGING_ROOT="$(mktemp -d /tmp/robocon_submission.XXXXXX)"
SUBMISSION_ROOT="$STAGING_ROOT/$ARCHIVE_NAME"

cleanup() {
  rm -rf "$STAGING_ROOT"
}
trap cleanup EXIT

mkdir -p \
  "$SUBMISSION_ROOT/00-提交说明" \
  "$SUBMISSION_ROOT/01-方向一-三维视觉与AR" \
  "$SUBMISSION_ROOT/02-方向二-自主导航" \
  "$SUBMISSION_ROOT/03-方向三-四足强化学习"

# 0. 私人提交说明（包含联系方式，仅进入邮件 ZIP）。
rsync -a "$QUADRUPED_ROOT/submission_docs/" "$SUBMISSION_ROOT/00-提交说明/"
cp "$NAV_ROOT/docs/ros2_learning_notes.md" \
  "$SUBMISSION_ROOT/00-提交说明/ROS2学习笔记.md"

# 1. AprilTag 位姿估计与 AR：源码、打印物料、离线验证和开发记录。
rsync -a \
  --exclude '.git/' --exclude 'build/' --exclude 'install/' --exclude 'log/' \
  --exclude '__pycache__/' --exclude '.pytest_cache/' --exclude '*.pyc' \
  --exclude '*.tar.gz' \
  "$APRILTAG_ROOT/" "$SUBMISSION_ROOT/01-方向一-三维视觉与AR/"

# 2. 自主导航：源码、文档、地图、实验数据、关键截图和最终演示视频。
rsync -a \
  --exclude '.git/' --exclude 'build/' --exclude 'install/' --exclude 'log/' \
  --exclude '__pycache__/' --exclude '*.pyc' --exclude '*.db3' --exclude '*.mcap' \
  --exclude 'results/videos/demo_navigation_rviz.mp4' \
  --exclude 'results/videos/demo_navigation_rviz_labeled.mp4' \
  "$NAV_ROOT/" "$SUBMISSION_ROOT/02-方向二-自主导航/"
cp "$NAV_ROOT/results/videos/demo_navigation_rviz_labeled.mp4" \
  "$SUBMISSION_ROOT/02-方向二-自主导航/results/videos/demo_navigation_rviz.mp4"

# 3. 四足强化学习：完整源码、文档、曲线和演示视频；省略本地安装包与大体积训练中间日志。
Q_DEST="$SUBMISSION_ROOT/03-方向三-四足强化学习"
cp "$QUADRUPED_ROOT/README.md" "$QUADRUPED_ROOT/.gitignore" "$Q_DEST/"
rsync -a \
  --exclude '.git/' --exclude 'logs/' --exclude '__pycache__/' \
  --exclude '*.egg-info/' --exclude '*.pyc' \
  "$QUADRUPED_ROOT/legged_gym/" "$Q_DEST/legged_gym/"
rsync -a \
  --exclude '.git/' --exclude '__pycache__/' --exclude '*.egg-info/' --exclude '*.pyc' \
  "$QUADRUPED_ROOT/rsl_rl/" "$Q_DEST/rsl_rl/"
rsync -a --exclude '__pycache__/' --exclude '*.pyc' \
  "$QUADRUPED_ROOT/mjlab_custom/" "$Q_DEST/mjlab_custom/"
rsync -a "$QUADRUPED_ROOT/scripts/" "$Q_DEST/scripts/"
rsync -a "$QUADRUPED_ROOT/dev_notes/" "$Q_DEST/dev_notes/"
mkdir -p "$Q_DEST/results"
rsync -a "$QUADRUPED_ROOT/results/curves/" "$Q_DEST/results/curves/"
mkdir -p "$Q_DEST/results/videos"
cp "$QUADRUPED_ROOT/results/videos/demo_assessment_stand_walk.mp4" \
  "$Q_DEST/results/videos/demo_assessment_stand_walk.mp4"

# 清理所有方向中不应提交的缓存和空构建产物。
find "$SUBMISSION_ROOT" -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '*.egg-info' \) \
  -prune -exec rm -rf {} + 2>/dev/null || true
find "$SUBMISSION_ROOT" -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.swp' \) \
  -delete 2>/dev/null || true

if [ -f "$FINAL_ZIP" ]; then
  mv -f "$FINAL_ZIP" "$PREVIOUS_ZIP"
fi

(
  cd "$STAGING_ROOT"
  zip -rq "$FINAL_ZIP" "$ARCHIVE_NAME"
)

zip -T "$FINAL_ZIP"
printf 'Final ZIP: %s\n' "$FINAL_ZIP"
du -h "$FINAL_ZIP"
