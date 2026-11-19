# D1 Max 轮足训练：任务、PPO 与评估

## 已部署的内容

宿主机 `/data/dengming/isaaclab_fairino/robotdog_d1_max/training`，容器内对应 `/home/isaaclab_fairino/robotdog_d1_max/training`。

| 文件 | 职责 |
|---|---|
| `prepare_asset.py` | 创建训练 USD 覆盖层与 asset audit |
| `d1_env.py` | DirectRLEnv 场景、动作、观测、奖励、终止、重置 |
| `run.py` | prepare/smoke/train/evaluate，PPO、导出与报告 |
| `run.sh` | 在宿主机进入容器调用已有 CUDA launcher，结束后修正项目文件归属 |
| `reports/` | 机械检查、模型审计 |
| `logs/<时间_名称>/` | checkpoint、TensorBoard、manifest、env.yaml、评估 |

目标是平地轮腿速度跟踪，允许滚动。它没有踏步相位奖励、粗糙地形或越障 curriculum；“训练机械狗”不自动等于四足踏步。

## MDP 精确接口

物理 200 Hz、策略 50 Hz；episode 20 s；默认 64 环境、间距 4 m；重力 -9.81 m/s²。只在 reset 写根和关节状态，步进过程中写关节目标。

### 动作：16 维，裁剪到 [-1,1]

前 12 维顺序：FAR/FBL/RAR/RBL，每腿 ABAD、HIP、KNEE。后 4 维为同顺序 FOOT 轮速。

```text
q_target_leg = q_default_leg + 0.25 × action[0:12]     # rad
wheel_target = 6 × action[12:16]                    # rad/s
q_default = ABAD 0, HIP -0.20, KNEE +0.40 rad
```

腿位置目标还受 soft limits 裁剪。腿仿真驱动 180/18，140 Nm、10 rad/s；轮驱动 0/8，50 Nm、25 rad/s。这些是仿真初始配置，不是厂商控制器参数。

### 观测：56 维

| 索引（半开） | 内容 | 缩放 |
|---|---|---|
| 0:3 | body frame 基座线速度 | 1 |
| 3:6 | body frame 基座角速度 | 0.25 |
| 6:9 | 投影重力 | 1 |
| 9:12 | vx、vy、yaw 指令 | 1 |
| 12:24 | 腿角度减 nominal | 1 |
| 24:36 | 腿角速度 | 0.05 |
| 36:40 | 轮角速度 | 0.05 |
| 40:56 | 上一步动作 | 1 |

连续轮角不进观测；末端/机身视觉和语言均不进该策略。基座线速度是仿真真值，实机需要估计或重新设计 actor 观测。观测随后裁剪 [-20,20] 并经过训练中学习的归一化统计。

每 4 s 采新命令：vx∈[-0.2,0.6] m/s，vy=0，yaw∈[-0.6,0.6] rad/s；15% 设为全零站立。此分布决定学什么，不要求策略完成侧向轮滑。

## 奖励与终止

每项乘控制步长 0.02 s 后求和：

| 项 | 当前形式/权重 | 目的 |
|---|---|---|
| track_linear | `2 exp(-||v_cmd_xy-v_xy||²/0.16)` | 速度跟踪 |
| track_yaw | `exp(-(yaw_cmd-wz)²/0.25)` | 转向跟踪 |
| upright | `-2 ||gravity_xy||²` | 姿态 |
| height | `-8 (z-0.61)²` | 保持高度 |
| vertical_velocity | `-vz²` | 减少跳动 |
| roll_pitch_rate | `-0.05 ||w_xy||²` | 姿态稳定 |
| torques | `-1e-5 Σtau²` | 抑制过大驱动 |
| action_rate | `-0.02 Σ(a_t-a_prev)²` | 动作平滑 |
| leg_posture | `-0.05 Σ(q_leg-q_nominal)²` | 保持合理腿姿 |
| bad_contacts | `-0.5 × HIP/KNEE 连杆接触数`；历史窗口最大力模长 >5 N 才计数 | 避免腿部擦地 |
| termination | `-2 × 跌倒标记` | 限制失败 |

无直接轮速奖励，减少空转投机，但仍须检查滑移。站立与高度奖励过强可能使策略宁可不走；速度奖励过强又可能鼓励不稳定冲刺，需要看分项与闭环指标调参。

接触传感器历史长度为 3、每 0.005 s 更新；上述计数逐 HIP/KNEE 连杆在当前可用历史窗口取最大力模长，再以 >5 N 判断。BASE 接触的终止条件另用 >20 N，不与该奖励阈值混淆。

终止：root z<0.30 m、投影重力 z>-0.5（倾斜过大）、base 接触力>20 N 或 root 非有限；超时单独处理。reset 可加入小关节/偏航扰动。当前自碰撞关闭，模型/真实约束不完全一致。

## 随机化与 PPO

`--randomize`：静摩擦 0.7–1.1、动摩擦 0.6–0.9、零恢复系数、基座质量缩放 0.9–1.1；对部分观测加入小噪声。材料/质量在 startup 采样，不是每步重采；同一环境运行期间基本固定。延迟、推力、质心/惯量和地形随机化未实现。

PPO：rollout 24 控制步/环境，actor/critic MLP 256→128→64，ELU；5 learning epochs、4 minibatches、初始 LR 3e-4、adaptive KL 0.01、gamma 0.99、lambda 0.95、clip 0.2、entropy 0.005、初始噪声 std 0.4、梯度范数上限 1。

256 环境×24×10 更新＝61,440 条新 transition。iteration、environment step、physics substep、video frame 是不同计数，不互相替代。

## 启动与产物

```bash
# 服务器宿主机；以下均会运行仿真/写日志
cd /data/dengming/isaaclab_fairino/robotdog_d1_max/training
bash run.sh --mode smoke --num-envs 64 --steps 400 --randomize
bash run.sh --mode train --num-envs 64 --iterations 10 --randomize --run-name pipeline_check

# 长训练建议起点：确认资源可用后执行；不是本次自动启动项
bash run.sh --mode train --num-envs 256 --iterations 1500 --randomize --run-name flat_v1
```

评估具体历史断点（容器路径）：

```bash
# 服务器宿主机
cd /data/dengming/isaaclab_fairino/robotdog_d1_max/training
bash run.sh --mode evaluate --num-envs 64 --steps 500 --vx 0.3 --yaw 0.0 \
  --checkpoint /home/isaaclab_fairino/robotdog_d1_max/training/logs/20261024_170713_resume_256_check/model_final.pt
```

续训同样加 `--checkpoint`，训练配置必须兼容；从不同环境数恢复有历史成功记录。新 run 目录不等于从零训练，manifest 要记录父 checkpoint。

`model_final.pt` 包含策略、critic、优化器及归一化；`exported/policy.pt` 为带归一化的 TorchScript 推理文件。推理先 `.eval()`，不要丢弃 normalizer 或对输入再次错误归一化。历史检查导出与原推理最大动作差为 0。

## 已有结果与限制

2026-10-24 历史报告：256 环境固定 2 rad/s 轮速检查平均前进约 0.9474 m，无 drive reset，轮接触力模长和均值约 415.99 N。高度报告由“每步各环境最小高度”序列归纳，不是全部环境高度的完整上下界。Torch 显存统计也不含 PhysX/Kit 全部显存。

PPO 只短测了 64×10 更新，再续训 256×10 更新。前者 0.3 m/s 指令误差约 0.237 m/s，后者约 0.327 m/s；没有收敛证据。短时无 reset 不等于长期稳定，`COMPLETED` 只表示评估执行完。

现有 evaluate 关闭初始姿态扰动；nominal 模式仅换 seed 不形成有意义的随机初态评估。`evaluation.json` 仅有总体平均 vx/yaw 误差、高度、总 reset 和一次初始观测批次的导出动作比对，不含逐环境跌倒/超时、滑移或饱和。自动 reset 后的读数仍进入均值，不能用低误差掩盖失败。完整评估协议和待扩展指标见 [实验验收](12-experiments.md)。

历史 256 环境报告末帧一个轮速与其他轮异号；摘要不足以判断轴向、接触或驱动原因。长训练前应逐轮记录目标/实测速度及接触，不直接认定轮方向正确或擅自翻转轴向。

下一步：多 seed 长训练 → 前后/转向/站立固定指令评估 → 动作/力矩/滑移可视化 → 校准模型 → 再加入地形。若目标是踏步，调整任务而非给现有滚动视频换标题。

参考：[官方 ANYmal](https://github.com/isaac-sim/IsaacLab/tree/v2.1.0/source/isaaclab_tasks/isaaclab_tasks/direct/anymal_c)、[RSL-RL 2.3.1](https://github.com/leggedrobotics/rsl_rl/tree/v2.3.1)、[Flamingo 轮腿](https://github.com/jaykorea/Isaac-RL-Two-wheel-Legged-Bot)、[B2-W 社区设计](https://github.com/LauraMQuiros/b2w-rl)。后两者不是本项目效果证明，参数/权重不能直接移植。
