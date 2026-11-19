# Robot_base：实验室具身智能技术手册

从服务器上真实存在的工程出发，说明“是什么、怎样工作、怎么复现、怎么验收”。覆盖机械臂、轮足机械狗、相机与标定、ROS 2、Isaac Sim/Lab、数据集、强化学习和视觉语言动作模型。

盘点日期：**2026-11-19，Asia/Shanghai**。文档中的服务器路径用于实验室内复现；仓库不携带厂商模型、SDK 二进制、数据集、训练权重或凭据。

## 先看什么

| 你的任务 | 阅读入口 |
|---|---|
| 第一次使用服务器 | [1008 VPN 连接](docs/17-vpn-1008.md) → [环境与容器](docs/01-infrastructure.md) → [最小复现](docs/15-runbooks.md) |
| 想知道现在已经做到了哪一步 | [技术地图与状态](docs/00-stack-map.md) → [盘点证据](docs/16-evidence.md) |
| 学机械臂与 ROS 2 | [数学与控制](docs/02-foundations.md) → [模型](docs/03-robot-assets.md) → [ROS 2 / MoveIt](docs/04-ros2-moveit.md) |
| 把 FR5 放进 Isaac 并采数据 | [仿真运行时](docs/05-isaac-runtime.md) → [FR5](docs/06-fairino-simulation.md) → [数据集](docs/08-datasets-imitation.md) |
| 训练 D1 Max 轮足机器人 | [D1 Max / PPO](docs/09-d1-max-rl.md) → [评估和实验规范](docs/12-experiments.md) |
| 用相机定位、抓取 | [相机、标定与感知](docs/07-perception-calibration.md) |
| 研究 OpenVLA、OFT、LIBERO | [VLA 与基准](docs/10-vla-libero.md) |
| 从仿真走向实机 | [同步与 Sim-to-Real](docs/11-sim-to-real.md) |
| 遇到连接、CUDA、画面或训练故障 | [排障表](docs/13-troubleshooting.md) |
| 系统学习 | [分阶段学习路线](docs/14-learning-roadmap.md) |

## 当前能力边界

- Fairino FR5＋90C：历史 ROS 2 模型和 MoveIt 配置存在，已经迁移到个人 Isaac 环境；抓取采集器使用**运动学轨迹＋闭合后附着**，不能当成接触抓取算法成功。
- D1 Max：16 动作/56 观测的物理训练任务已部署，存在 256 环境检查和 PPO/续训/导出记录；现有短测策略**没有收敛**，不代表学会踏步或越障。
- D455/L515：USB 设备可见；盘点时 ROS 图中的彩色图像话题**发布者为 0**。话题名字存在不等于相机正在采集。
- OpenVLA/OFT、LIBERO、RLDS、GraspNet、DepthFM、SpatialBot 等源码存在。未逐个跑模型与基准，不能据此宣称完整管线已部署。
- 实机状态同步脚本存在；本次只读取工程和系统状态，未建立机器人反馈连接、未运行 SDK 或运动控制程序。

完整目录、版本、状态等级与证据见 [技术地图](docs/00-stack-map.md)。资料中发现的旧路径失效、容器配置错误和模型限制均写入对应章节，不照搬为可用命令。

## 文档使用约定

命令标注执行位置：`本机`、`服务器宿主机`、`Isaac 容器`、`ROS 容器`。`/data/dengming` 在个人 Isaac 容器内映射为 `/home`；不要在本机终端照抄容器路径。

状态标签：**当前核验**＝本次直接读取；**历史验证**＝已有报告/产物；**源码存在**＝未运行；**建议方案**＝尚未实现。每项能力都要有验收依据，不能用视频或奖励上涨代替。

运行文档检查：

```bash
python3 tools/check_docs.py
```

独立审核范围和结论记录在 [审核记录](docs/review.md)。内容更新流程、资产许可和凭据边界见 [维护约定](CONTRIBUTING.md)。
