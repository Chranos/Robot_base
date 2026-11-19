# 仿真数据集、完整性校验与模仿学习

## 当前采集器到底采什么

`scripts/collect_pick_dataset.py` 独立于 ROS/SDK，在 Isaac 中执行预定 FR5 轨迹，输出 RGB、深度、语义和六轴状态。物体闭合后运动学附着。适合验证相机/标签/训练 IO；不包含接触真实度保证，也不是 VLA 现成训练集。

已发现数据目录（宿主机）：

```text
/data/dengming/isaaclab_fairino/output/datasets/
  fairino_pick_pilot_v1/       # 10 个 episode 目录
  fairino_pick_preflight_v1/   # 单个预检目录
  fairino_pick_smoke/          # 单个 smoke 目录
```

存在这些目录不等于本次已经全量重验；具体证据见 [核验记录](16-evidence.md)。100-episode baseline 是启动配置，不是已经采完的事实。

## 数据结构与语义

```text
dataset/
  manifest.json
  episode_000000/
    metadata.json
    states.npz
    rgb/000000.png ...
    depth/000000.png ...
    semantic/000000.png ...
```

| `states.npz` 字段 | 形状（T 为帧数） | 语义 |
|---|---|---|
| time_s | T | 模拟采样时间，从 0 开始 |
| joint_pos_rad / joint_vel_rad_s | T×6 | j1…j6 的仿真状态；速度因轨迹直接写入可能缺乏真实动力学意义 |
| action_joint_pos_rad | T×6 | 绝对关节目标，不是力矩 |
| action_delta_rad | T×6 | 当前目标减上一目标；第一帧相对初始目标 |
| ee_pose_w_xyz_wxyz | T×7 | `g_base_link` 位姿，不自动等于接触 TCP |
| object_pose_w_xyz_wxyz | T×7 | 物体 world 位姿 |
| stage_id / attached / done | T | 动作阶段、附着标记、最后帧终止 |

RGB 为 uint8，depth/semantic 为 uint16 PNG。深度单位毫米，0 无效；语义值是 ID，不能把调色板颜色当标签。metadata 提供相机 K、world pose、ROS optical 约定四元数、语义映射、单位、seed、轨迹/附着模型及 success。

代码按物体最终抬升 ≥0.15 m 且末阶段为 5 判 success；这一条件不会检测穿透、真实夹持力或掉落。若将数据用于学习，要把 `trajectory`/`grasp_model` 一起保存到数据卡。

## 时间、动作与泄漏

实际采样间隔由 `round(PHYSICS_HZ/fps)` 决定，不能在任意 FPS 下仅用 `1/fps` 推算。观测拍摄在动作/步进之后；使用它训练 `a_t` 时需明确“预测下一目标”还是“重建当前目标”，避免标签时序错位。

当前 split 按 episode 编号 `%10`：0–7 train、8 val、9 test。不要移动时重新编号，不按帧随机拆分同一段轨迹。若多个 episode 实际共享相同场景/轨迹，仍可能有相关性，需要按对象/场景/seed 分组评估。

## 运行与恢复

```bash
# 服务器宿主机：先验证现有 pilot，不启动新采集
docker exec isaacvnc_dengming /isaac-sim/python.sh \
  /home/isaaclab_fairino/scripts/validate_pick_dataset.py \
  /home/isaaclab_fairino/output/datasets/fairino_pick_pilot_v1

# 写入新数据/日志：pilot 目标总量 10，已够则仅验证
docker exec isaacvnc_dengming bash -c \
  '/home/isaaclab_fairino/scripts/run_collect_pick_dataset.sh pilot'

# 验收 pilot 后再启动 baseline：目标总量 100
docker exec isaacvnc_dengming bash -c \
  '/home/isaaclab_fairino/scripts/run_collect_pick_dataset.sh baseline'
```

launcher 从 manifest 最大 episode 编号续采；先做保守空间检查，调用 collector，最后验证。临时 episode 写完后原子重命名；不传 overwrite。中断恢复时先核对 manifest 与完整目录，不手改编号来“凑数量”。

估算未压缩模态字节：`episodes×T×W×H×7`（RGB3＋depth2＋semantic2），launcher 加 25% 余量。PNG 压缩比和文件系统实际占用另算，大规模采集先测一小批。

## 从 NPZ 到训练

建议先做最小行为克隆（未在本项目实现）：

1. 仅用状态输入预测下一关节目标，验证动作/时间对齐。
2. 加入图像编码器，固定分辨率、归一化和相机约定。
3. 把夹爪动作纳入标签；当前六轴标签不足以训练自主开合。
4. 训练 loss 按关节/单位统计，验证集按 episode 划分。
5. 在仿真闭环执行，统计任务成功、碰撞、停滞与恢复能力。

转换 RLDS 时定义 `observation`、`action`、`is_first`、`is_last`、`is_terminal`、语言 instruction、dataset/action statistics。不可直接把终帧 done 同时当所有 terminal 语义。OpenVLA 常见动作是 7 维末端 delta＋夹爪，当前 6 维关节目标需要单独定义与适配，见 [VLA](10-vla-libero.md)。

建议后续数据扩展：物体几何/材质/光照/位姿/相机变化、有效失败演示、接触任务、多个场景以及数据卡。不要把大量近乎重复的成功动画当成泛化数据。
