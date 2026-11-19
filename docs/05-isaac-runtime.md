# Isaac Sim / Isaac Lab 运行时与 CUDA 兼容层

## 已核验版本

个人容器内 `/workspace/isaaclab/VERSION` 为 2.1.0，Python 3.10.15；PyTorch 2.5.1、RSL-RL 2.3.1、Gymnasium 1.1.1、NumPy 1.26.4、TensorBoard 2.19.0。Isaac Sim 4.5 为当前工程历史启动日志与路径基线，不能混用 5.1/最新版教程中的 API。

Isaac Sim 提供 Kit 应用、USD 场景、PhysX 和 RTX 渲染；Isaac Lab 在其上提供机器人资产接口、传感器、并行环境、MDP/RL 封装。`.kit` experience 决定加载哪些扩展和版本，不能只看 Python 的 `pip list`。

## CUDA 不兼容的具体含义

GPU 驱动、CUDA runtime、PyTorch 自带库、Warp、Kit 扩展可能来自不同发行版。`nvidia-smi` 显示的 CUDA 能力不是当前 Python 正在使用的 runtime；有 GPU 也不说明所有 CUDA 扩展都兼容。

历史问题发生在镜像自带 `omni.warp.core` / Warp 初始化与驱动组合，解决方案是局部兼容包：

```text
/home/isaaclab_fairino/
  vendor/warp_1_8_2/                 # Python Warp
  vendor/extensions/                # Kit Warp 扩展
  apps/isaaclab.python.headless.cuda13.kit
  apps/isaaclab.python.headless.cuda13.rendering.kit
  run_isaaclab_cuda.sh
```

启动器将 vendor 放到 PYTHONPATH 前，并在 Python launch 未指定 experience 时附加自定义无头 experience。渲染采集要显式指定 rendering experience。某些脚本另兼容 Warp `array(owner=False)` 参数移除；单独更换一个包不等于完整修复。

这是一套已有环境的局部适配，不表示任意 Isaac 4.5＋任意 CUDA 13 都能运行。重建须保留扩展与 Python 包的配对、版本和路径，先测试再改驱动。

## 启动顺序

Isaac Lab 脚本通常先解析 AppLauncher 参数、创建 app，再 import 依赖 Omniverse 扩展的模块。过早 import `omni.*`、Camera 或 Sim 对象可能失败。

```bash
# 服务器宿主机；有限物理检查，有仿真运行但不连接硬件
docker exec isaacvnc_dengming bash -c '
  /home/isaaclab_fairino/run_isaaclab_cuda.sh -p \
    /home/isaaclab_fairino/scripts/smoke_test.py \
    --headless --device cuda:0 --steps 20
'
```

预期查看机器人载入与 `smoke_test_steps=20 status=PASS`。这只证明该脚本的加载/步进，不证明抓取、相机或 PPO 都正确。

```bash
# 服务器宿主机：实际版本读取
docker exec isaacvnc_dengming bash -c '
  cat /workspace/isaaclab/VERSION
  /isaac-sim/python.sh -c "import sys, torch; print(sys.version); print(torch.__version__)"
'
```

## 物理与渲染分开验收

1. 先禁用相机，以小环境数检查有限状态、重力、接触、关节目标。
2. 再启用离屏相机，验证 robot mesh、光源、相机外参、RGB/depth/semantic。
3. 最后录视频或采集数据，确认 FPS 与模拟时间一致。

本工程遇到过 PhysX articulation 正常而无头相机网格更新异常。D1 录制器使用仅渲染副本复制 29 个物理 link 位姿，副本移除刚体/关节，物理模型仍唯一决定运动。训练不依赖此副本。

不要为修画面在训练步内 `write_joint_state_to_sim` 或平移 root；那会改变任务动力学。也不能用渲染不可见推断 physics 没运行。

## 日志判读

| 信息 | 判断 |
|---|---|
| GLFW/X Server warning | 纯 headless 可能预期；以相机输出/最终结果判断 |
| torchvision `image.so` warning | 未用 torchvision.io 时不一定阻碍物理；使用该 IO 时需单独检查 |
| Warp CUDA init/编译 error | 检查启动器、experience、PYTHONPATH、扩展版本，不能忽略 |
| 不存在 USD/mesh/reference | 先检查映射/资源路径；不是 CUDA 故障 |
| NaN / GPU illegal memory | 保存首个错误，减少环境数检查模型/容量；失败进程退出后再重跑 |
| 卡在退出 | 个别历史脚本保存资源后 `os._exit` 规避 Kit 关闭卡住，需保证 writer/checkpoint 先关闭 |

CPU fallback 可用于局部诊断，但不是“GPU 训练已修复”的证据。官方对应版本入口：[Isaac Lab 2.1](https://isaac-sim.github.io/IsaacLab/v2.1.0/)。
