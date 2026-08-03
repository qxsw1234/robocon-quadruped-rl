#!/bin/bash
# 屏幕录制辅助脚本（用于录制 legged_gym viewer 演示）
# 用法: ./scripts/record_screen.sh <输出文件名.mp4> [时长秒] [屏幕坐标+尺寸]
# 示例: ./scripts/record_screen.sh results/videos/demo_walk.mp4 30
#
# 先用 `ffmpeg -f x11grab -framerate 30 -video_size 1280x720 -i :0.0` 录制，
# 结束后按 q 停止。

OUT="${1:-results/videos/demo.mp4}"
DURATION="${2:-30}"
SIZE="${3:-1920x1080}"
DISPLAY_NUM="${DISPLAY:-:0}"

ffmpeg -y -f x11grab -framerate 30 -video_size "$SIZE" -i "$DISPLAY_NUM" \
  -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p \
  -t "$DURATION" "$OUT" && echo "已保存: $OUT"
