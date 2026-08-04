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

# 3. 结果（曲线 + 视频 + 评估数据）
mkdir -p "$TMP/$NAME/results"
cp -r results/curves "$TMP/$NAME/results/curves"
cp -r results/videos "$TMP/$NAME/results/videos"
# mjlab 训练日志（含 tensorboard 事件，可复现曲线）
cp -r results/mjlab_logs "$TMP/$NAME/results/mjlab_logs" 2>/dev/null || true

# 4. 清理体积（日志、缓存、安装包）
find "$TMP/$NAME" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$TMP/$NAME" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
find "$TMP/$NAME" -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf "$TMP/$NAME/legged_gym/logs"
rm -rf "$TMP/$NAME/results/mjlab_logs"/*/git 2>/dev/null || true

echo "== 生成 ZIP =="
cd "$TMP"
zip -rq "/home/czm/桌面/robocon/$NAME.zip" "$NAME"
cd /home/czm/桌面/robocon
rm -rf "$TMP"

ls -lh "$NAME.zip"
echo "完成: $(pwd)/$NAME.zip"
