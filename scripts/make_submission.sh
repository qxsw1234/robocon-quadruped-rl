#!/bin/bash
# 生成考核提交压缩包
# 用法: ./scripts/make_submission.sh
# 输出: /home/czm/桌面/robocon/视觉组正式队员考核-2024级-测控技术与仪器-曹哲明.zip

set -e
cd /home/czm/桌面/robocon

NAME="视觉组正式队员考核-2024级-测控技术与仪器-曹哲明"
TMP="/tmp/submission_$$"
mkdir -p "$TMP/$NAME"

echo "== 整理提交文件 =="

# 1. 源码
cp -r legged_gym "$TMP/$NAME/legged_gym"
cp -r rsl_rl "$TMP/$NAME/rsl_rl"
cp -r mjlab_custom "$TMP/$NAME/mjlab_custom"
cp -r scripts "$TMP/$NAME/scripts"
cp README.md .gitignore "$TMP/$NAME/"

# 2. 文档
cp -r dev_notes "$TMP/$NAME/dev_notes"

# 3. 结果（曲线 + 视频 + 关键 checkpoint）
mkdir -p "$TMP/$NAME/results"
cp -r results/curves "$TMP/$NAME/results/curves"
cp -r results/videos "$TMP/$NAME/results/videos"

# mjlab 训练日志瘦身：每 run 只保留 tensorboard events + params + 最后 1 个 checkpoint
mkdir -p "$TMP/$NAME/results/mjlab_logs"
for run in results/mjlab_logs/*/; do
  exp=$(basename "$run")
  for sub in "$run"*/; do
    [ -d "$sub" ] || continue
    dest="$TMP/$NAME/results/mjlab_logs/$exp/$(basename "$sub")"
    mkdir -p "$dest"
    cp "$sub"events.out.tfevents.* "$dest/" 2>/dev/null || true
    cp -r "$sub"params "$dest/" 2>/dev/null || true
    last_ckpt=$(ls "$sub"model_*.pt 2>/dev/null | sort -V | tail -1)
    [ -n "$last_ckpt" ] && cp "$last_ckpt" "$dest/" || true
  done
done

# legged_gym 关键 checkpoint（基线 3000 迭代 + 3 个实验各最后 1 个）
mkdir -p "$TMP/$NAME/results/checkpoints"
for exp in rough_a1 rough_a1_no_vel_tracking rough_a1_no_feet_air rough_a1_high_torque_pen; do
  last_ckpt=$(ls legged_gym/logs/$exp/*/model_*.pt 2>/dev/null | sort -V | tail -1)
  if [ -n "$last_ckpt" ]; then
    cp "$last_ckpt" "$TMP/$NAME/results/checkpoints/$(basename $exp).pt"
  fi
done

# 4. 清理体积（日志、缓存、安装包）
find "$TMP/$NAME" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$TMP/$NAME" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
find "$TMP/$NAME" -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf "$TMP/$NAME/legged_gym/logs"
rm -rf "$TMP/$NAME/results/mjlab_logs"/*/git 2>/dev/null || true

echo "== 生成 ZIP =="
rm -f "/home/czm/桌面/robocon/$NAME.zip"   # 删除旧包，避免 zip 追加
cd "$TMP"
zip -rq "/home/czm/桌面/robocon/$NAME.zip" "$NAME"
cd /home/czm/桌面/robocon
rm -rf "$TMP"

ls -lh "$NAME.zip"
echo "完成: $(pwd)/$NAME.zip"
