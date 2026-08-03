#!/bin/bash
# 激活 legged_gym 训练环境（conda leg + LD_LIBRARY_PATH 修复）
# 用法: source scripts/leg_env.sh
source /home/czm/miniconda3/etc/profile.d/conda.sh
conda activate leg
export LD_LIBRARY_PATH=/home/czm/miniconda3/envs/leg/lib:$LD_LIBRARY_PATH
echo "leg env activated (python $(python --version 2>&1 | awk '{print $2}'), LD_LIBRARY_PATH set)"
