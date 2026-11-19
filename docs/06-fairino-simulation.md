# Fairino FR5＋90C：从历史实验到 Isaac

## 工程数据流

```text
frros2_sj:/home/383_ws/fr_90c_ws
    ├─ fairino_gp_description
    └─ fairino5_90c_config
              │ 保留原文件、修正派生 mesh 路径
              v
/data/dengming/isaaclab_fairino/
    assets/fairino5_v6_90c/ → usd/fairino5_v6_90c.usd
              │
    scripts/fairino_cfg.py → 载入/轨迹/采集/镜像
```

宿主机 `/data/songjie/pkgs/config` 是基础配置参考，并非 90C 历史实验的唯一来源。选错夹爪会导致 TCP、碰撞模型、joint 列表和末端语义全部不一致。

## 关节与参数

`fairino_cfg.py` 对机械臂 `j1...j6` 使用 ImplicitActuator：仿真力矩上限 150 Nm、速度 3.2 rad/s、stiffness 400、damping 40。夹爪 `.*_Joint` 使用 30 Nm、1 rad/s、100/10。初始臂关节 `[0,-0.5,1,0,0.5,0] rad`。

这些是仿真工程设定，不是已经实测标定的电机响应。固定底座、自碰撞开关、夹爪 mimic/零范围关节和 solver 参数都要与任务一起核验。

历史 90C 导入存在零范围 mimic 关节，当前抓取录制器因此直接写关节状态，并在闭合后把物体附着到夹爪中点。它证明资产部署、轨迹显示和采集流程，不能用于评价真实接触抓取成功率。

## 三种脚本，不要混为一谈

| 脚本 | 用途 | 通过后可以宣称 |
|---|---|---|
| `smoke_test.py` | 有限无头载入/物理步进 | 资产能加载并步进 |
| `record_pick_demo.py` | 按预定轨迹显示抓取并录像 | 场景/机械臂部署和运动演示 |
| `collect_pick_dataset.py` | 运动学演示采 RGB/深度/语义与状态 | 数据模式和导出管线可用 |
| `sync_real_to_isaac.py` | 反馈驱动虚拟关节 | 获得有效反馈时的单向状态镜像 |

最后一项不属于自主控制。前三项不需要真实机器人在线。

## 在已有环境中复现

```bash
# 服务器宿主机：检查资产与关键配置存在
docker exec isaacvnc_dengming bash -c '
  test -f /home/isaaclab_fairino/usd/fairino5_v6_90c.usd
  ls /home/isaaclab_fairino/assets/fairino5_v6_90c/urdf
  sed -n "1,150p" /home/isaaclab_fairino/scripts/fairino_cfg.py
'
```

运行有限 smoke 见 [运行时](05-isaac-runtime.md)。历史录制命令使用 Xvfb 隔离显示：

```bash
# 服务器宿主机；新输出文件会写入 output，请选未使用的名称
docker exec isaacvnc_dengming bash -c '
  xvfb-run -a -s "-screen 0 1280x720x24 -ac" \
  /home/isaaclab_fairino/run_isaaclab_cuda.sh -p \
  /home/isaaclab_fairino/scripts/record_pick_demo.py \
  --device cuda:0 \
  --experience /home/isaaclab_fairino/apps/isaaclab.python.headless.cuda13.rendering.kit \
  --frames 420 --fps 30 --width 1280 --height 720 \
  --output /home/isaaclab_fairino/output/fairino_fr5_pick_review.mp4
'
```

本次未重录该视频；原视频历史参数为 14 s、720p、30 FPS。验证新输出时用 ffprobe 检查编码/帧数/时长，并抽查靠近、闭合、抬升、终止帧；时长与动作真实度分别验收。

录制器显式物理 dt=1/120 s，主循环每输出帧只调用一次 `sim.step`。420 帧对应主循环显式模拟时间约 3.5 s，却按 30 FPS 编成 14 s 视频（不含初始化步）；这是慢放显示，不是物理与视频实时同步。该脚本还直接写状态，因此不能用视频速度证明电机或接触的真实响应。

## 如何升级成接触抓取任务

这是后续设计，尚未完成：

1. 重建有效夹爪自由度/mimic/碰撞和驱动，确认左右指联动方向。
2. 物体由动态刚体和接触力驱动，取消附着与逐帧 root 写入。
3. 记录夹爪开度、接触力、物体滑移、抬升高度、保持时间和意外碰撞。
4. 从已知位姿/已知摩擦开始，加入物体尺寸、质量、位置和纹理变化。
5. 定义成功：物体由夹爪接触持续抬起并保持，无穿透/隐藏约束；记录失败样本。

现有视频和数据可以用于学习管线排练，但不能用其“success=True”对外宣称经过接触验证。
