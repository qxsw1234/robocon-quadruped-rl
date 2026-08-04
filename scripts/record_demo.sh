#!/bin/bash
# 录制 legged_gym 演示视频（ffmpeg 录屏 + play_demo viewer）
# 用法: ./scripts/record_demo.sh <stand|walk> <输出文件名.mp4> [steps] [--flat|--rough]
# 示例: ./scripts/record_demo.sh stand results/videos/demo_stand.mp4 600 --flat
#       ./scripts/record_demo.sh walk  results/videos/demo_walk.mp4  600 --flat
#       ./scripts/record_demo.sh walk  results/videos/demo_walk_rough.mp4 600 --rough

MODE="${1:-stand}"
OUT="${2:-results/videos/demo_$MODE.mp4}"
STEPS="${3:-600}"
TERRAIN="${4:---flat}"
VX=1.0
DURATION=$((STEPS * 20 / 1000 + 5))   # 仿真 20ms/步 + 5s 余量

cd /home/czm/桌面/robocon
source scripts/leg_env.sh > /dev/null

echo "准备录制: mode=$MODE vx=$VX steps=$STEPS terrain=$TERRAIN out=$OUT"

# 启动录屏（全屏 1920x1080@30fps）
ffmpeg -y -f x11grab -framerate 30 -video_size 1920x1080 -i "${DISPLAY:-:0}" \
  -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -t "$DURATION" "$OUT" &
FFMPEG_PID=$!
sleep 2

# 启动演示（viewer 模式）
python scripts/play_demo.py --task=a1 --mode="$MODE" --vx="$VX" --steps="$STEPS" \
  --num_envs=4 $TERRAIN 2>&1 | tail -10
DEMO_EXIT=$?

# 等录屏结束
wait $FFMPEG_PID 2>/dev/null
echo "录制完成: $OUT (demo exit=$DEMO_EXIT)"
ls -lh "$OUT"
