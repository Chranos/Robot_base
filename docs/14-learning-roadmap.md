# 学习路线：以能验收的小项目推进

建议按能力门槛推进，时间仅供安排：有基础可跳级，无基础先做练习。目标是能解释/复现/排错，不是把所有库安装一遍。

| 阶段 | 建议投入 | 学什么 | 必须交付的练习/通过标准 |
|---|---|---|---|
| 0 环境 | 2–3 天 | Linux、SSH、Git、Docker、bind mount、日志 | 登录服务器，解释宿主机/两容器路径；只读盘点并写版本清单 |
| 1 数学与 Python | 1–2 周 | NumPy/PyTorch、矩阵/四元数、单位、概率、优化 | 六轴 degree→rad 对齐；两段坐标变换；有限值/shape 检查 |
| 2 机器人模型/ROS | 1–2 周 | URDF/Xacro/SRDF、TF、topic/service/action、QoS | 解释 FR5＋90C 的 joint/link；离线模型树；topic 发布者/订阅者核验 |
| 3 仿真与控制 | 1–2 周 | USD、PhysX、碰撞、PD、多频率 | FR5/D1 小 smoke；记录接触/角度/力矩；指出动画与动力学差别 |
| 4 感知与数据 | 1–2 周 | RGB-D、内参、手眼、数据 schema/split | 可视化深度反投影；校验 pilot；写数据卡和时序/动作定义 |
| 5A 轮足 RL | 2–4 周 | MDP、PPO、奖励、随机化、评估 | 复现短测；补齐评估记录，按[固定窗口、样本数、基线和候选阈值](12-experiments.md)完成多命令/多 seed 验收 |
| 5B 机械臂模仿 | 2–4 周 | BC、图像编码、action chunk、闭环 | 状态 BC→图像 BC；按 episode 留出测试；仿真闭环统计失败 |
| 6 VLA/基准 | 2–4 周 | RLDS、LIBERO、OpenVLA/OFT、微调 | 一个数据 episode→模型输入→解码动作→仿真；固定版本复现一个任务 |
| 7 Sim-to-Real | 按研究进度 | 参数辨识、状态估计、延迟、shadow inference | 离线与只读反馈对齐报告；实机执行另立任务与验收 |

## 前两周可直接执行的计划

### 第 1–3 天：能准确找到东西

读 [环境](01-infrastructure.md)、[技术地图](00-stack-map.md)。手写三个路径映射例子；用 `docker inspect` 核对而非记忆。解释“旧源码在、install 不在”“topic 在、publisher 为 0”分别说明什么。

产物：个人 `environment-notes.md`，包含命令位置、版本和读数时间，不含密码。通过条件：换一个同学按记录找到同一文件并说明状态。

### 第 4–7 天：理解机器人模型和坐标

读 [基础](02-foundations.md)、[资产](03-robot-assets.md)、[ROS](04-ros2-moveit.md)。画 FR5 base→tool→camera 链，解释 camera optical frame；列 90C 与基础配置的不同。D1 找到四腿各四关节，说明 FOOT 连续限位问题。

产物：坐标图、单位表、joint 名称表、一个离线变换练习。通过条件：能说明一米为何不能传成一千米、xyzw 为何不能按 wxyz 读取。

### 第 8–10 天：仿真加载与控制

读 [运行时](05-isaac-runtime.md)，运行有限 smoke；用 D1 固定轮速检查接触与位移。记录策略 dt 与物理 dt，检查动作来自目标驱动还是状态重写。

产物：小测试日志＋关键数值。通过条件：不看视频也能用角度、位移、接触力解释运动来源。

### 第 11–14 天：数据与第一次训练

先验证现有抓取 pilot，再读 [D1](09-d1-max-rl.md) 跑少量 PPO。写一张 action contract，加载导出策略比对动作。长训练不作为入门练习的默认步骤。

产物：数据检查报告、短测配置/seed/checkpoint、固定命令误差。通过条件：能承认“流程跑通，但策略未收敛”，并给出证据。

阶段 5A 不能直接用现有 `evaluation.json` 判通过：它只有总体均值/总 reset，nominal 换 seed 也不等于随机评估。先按[实验协议](12-experiments.md)补逐环境失败、存活、滑移/饱和和匹配基线；该新增能力未实现，不把建议验收写成现成一键功能。

## 选择主线，避免同时展开所有项目

轮足方向：阶段 3→5A→参数/地形研究。机械臂方向：阶段 3→4→5B→6。两条线共用坐标、数据、物理与评估基础；OpenVLA 不替代 PPO，PPO 也不替代相机标定。

每阶段只选择 1 个可交付任务。读论文时提取任务定义、观测/动作、数据/奖励、基线、评估协议和失败条件，再对照本工程的缺口，不先复制所有依赖。

## 阅读顺序

1. [ROS 2 Humble Tutorials](https://docs.ros.org/en/humble/Tutorials.html)：CLI、TF2、QoS。
2. [Modern Robotics](https://modernrobotics.northwestern.edu/)：坐标、正逆运动学、雅可比与控制。
3. [Isaac Lab 2.1 Tutorials](https://isaac-sim.github.io/IsaacLab/v2.1.0/source/tutorials/index.html)：资产→传感器→DirectRLEnv→训练。
4. [Spinning Up PPO](https://spinningup.openai.com/en/latest/algorithms/ppo.html)：理解优化/GAE/clip，再读 RSL-RL 实现。
5. [legged_gym](https://github.com/leggedrobotics/legged_gym)：理解随机化/腿式任务，注意其推荐迁移 Isaac Lab。
6. [OpenVLA](https://github.com/openvla/openvla)、[LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO)：接口与基准优先于大规模微调。

参考链接是技术资料，不要求使用 OpenAI API 或额外云服务；本路线可先在本地/服务器仿真完成。
