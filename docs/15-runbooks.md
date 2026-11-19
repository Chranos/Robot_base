# 最小复现手册

以下命令针对已部署服务器，步骤间存在依赖。没有克隆仓库即可从零安装整套环境的承诺；资产、vendor 和历史容器仍在服务器。不同机器先参考 [环境](01-infrastructure.md) 做迁移计划。

## A. 只读健康检查

远程登录前先按 [1008 VPN 指南](17-vpn-1008.md)连接系统 VPN 并检查 TCP 22；在实验室 LAN 时可按指南核对局域网地址。不要因另一个 VPN 已连接而跳过此步。

```bash
# 本机
ssh dengming@192.168.190.200
```

```bash
# 服务器宿主机
docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Image}}'
nvidia-smi
df -h /data
docker inspect -f '{{.Name}} network={{.HostConfig.NetworkMode}} mounts={{json .Mounts}}' \
  isaacvnc_dengming frros2_sj
docker exec isaacvnc_dengming cat /workspace/isaaclab/VERSION
```

通过：个人容器存在、挂载正确、GPU 可见、关键文件在。失败时先定位层级，不启动其他成员容器。

## B. FR5 有限仿真检查

```bash
# 服务器宿主机；将运行仿真
docker exec isaacvnc_dengming bash -c '
  /home/isaaclab_fairino/run_isaaclab_cuda.sh -p \
  /home/isaaclab_fairino/scripts/smoke_test.py \
  --headless --device cuda:0 --steps 20
'
```

通过：最终 PASS、有限步数、无资产加载错误。不能据此宣布真实夹持成功。

## C. 已有数据校验

```bash
# 服务器宿主机；读取数据，不启动采集
docker exec isaacvnc_dengming /isaac-sim/python.sh \
  /home/isaaclab_fairino/scripts/validate_pick_dataset.py \
  /home/isaaclab_fairino/output/datasets/fairino_pick_pilot_v1
```

读取 validator 全部错误/退出码。自动检查通过后抽查 RGB/depth/semantic 与阶段/物体状态，仍须确认数据适合目标任务。追加采集见 [数据](08-datasets-imitation.md)。

## D. D1 并行环境与 PPO 短测

```bash
# 服务器宿主机；运行仿真并写报告/日志
cd /data/dengming/isaaclab_fairino/robotdog_d1_max/training
bash run.sh --mode smoke --num-envs 4 --steps 400
bash run.sh --mode smoke --num-envs 64 --steps 400 --randomize
bash run.sh --mode train --num-envs 64 --iterations 10 --randomize --run-name onboarding
```

通过：有限观测/奖励/状态、实际接触位移、独立 reset、checkpoint 和 export 存在。长训练和评估见 [D1](09-d1-max-rl.md)，不要将这 10 次更新命名为“训练完成”。

## E. ROS 与相机只读检查

```bash
# 服务器宿主机
docker exec frros2_sj bash -c '
  source /opt/ros/humble/setup.bash
  timeout 8 ros2 node list --no-daemon
  timeout 8 ros2 topic list --no-daemon -t
  timeout 8 ros2 topic info -v /d455/color/image_raw --no-daemon
'
```

不要 source 不存在的 90C install。不要为恢复 publisher 运行旧 hardware/demo launch。上游图像驱动的启动应在核对设备占用、工作区版本后单独操作。

## F. 取回视频与日志

```bash
# 本机，写入当前目录；先确认无同名文件以免覆盖
scp dengming@192.168.190.200:/data/dengming/isaaclab_fairino/output/d1_max_physx_action_demo_h264.mp4 ./
```

历史 D1 动作视频为脚本关节目标下蹲/鞠躬/轮腿动作，非 PPO 策略输出。记录来源与类型，不用其替代训练验收。

## G. 从服务器工程走向版本管理

本仓库以文档为主。修改训练源码时另建代码分支/项目，保存配置和源码 hash，生成新输出目录。不要把公共 README 的改动视为已更新服务器运行代码；两边需分别部署与校验。

遇到任何命令错误，记录执行位置、退出码和第一条错误，查 [排障](13-troubleshooting.md)。
