# 最终训练 checkpoint 说明

## 文件与来源

- 提交包路径：`results/checkpoints/model_3000.pt`
- 训练任务：legged_gym `a1` 基线任务（Unitree A1）
- 本机训练 run：`rough_a1/Aug03_17-57-33_`
- 训练迭代：累计 3000 iterations
- 文件大小：6,881,354 bytes
- SHA-256：`c7be70a4c2996a8b49616d8a9dcc2ac4f3fb2f2ada24d2cfd940fa639311f9bc`

该 checkpoint 由本机实际训练得到，不是开源项目附带的预训练策略。公开 GitHub
仓库继续排除二进制权重；邮件提交 ZIP 只保留这一份最终基线 checkpoint，其他中间
checkpoint 和 TensorBoard 原始日志不打包。

## 对应证据

- 训练步数与耗时：见 `考核结果报告.md` 和 `开发记录.md`
- 训练曲线：见 `results/curves/baseline_3000.png`
- 奖励配置：见 `legged_gym/legged_gym/envs/a1/a1_config.py`
- 最终演示：见 `results/videos/demo_assessment_stand_walk.mp4`

## 回放命令

```bash
python scripts/play_demo.py --task=a1 --mode=assessment --vx=1.0 \
  --steps=900 --stand-steps=400 --num_envs=1 --flat --follow-camera
```

回放时将 checkpoint 放入 `legged_gym/logs/rough_a1/<run>/model_3000.pt`，并在
命令中增加 `--load_run <run> --checkpoint 3000`；默认配置也会加载该 run 的最新 checkpoint。
