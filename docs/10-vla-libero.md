# VLA、OpenVLA/OFT、LIBERO 与 RLDS

## 已发现工程，先分清状态

以下为宿主机 `/data/songjie/EMAI` 下的目录证据：`openvla`、`openvla-oft-main`、`LIBERO`、`mujoco-learning-main`、`rlds_dataset_builder-main`、`rlds_dataset_mod-main`、`SpatialBot-main`、`GLM-4-main`、`Real_control`、`val_sim`、`isaacsim_env`。

ROS 容器 `/home/LIBERO` 也存在，但没有证据说明它与 EMAI/LIBERO 同步。另见 conda 环境名 `depthfm`、`grasp`、`rlds_env`、`robosuite`、`ros2bot`，名称不证明包版本或模型可用。当前未逐个激活环境、加载权重或跑 benchmark，不能宣称端到端 VLA 控制已部署。

## 模型在闭环里的位置

VLA 把图像、语言任务与机器人状态映射为动作。视觉编码器提取图像特征，语言/多模态 backbone 结合指令，动作头输出 token、连续动作或动作序列。它仍需要状态/动作适配、控制周期、限幅、碰撞检查和失败恢复。

OpenVLA 是具体开放实现；OFT 是面向高效微调/推理与连续/分块动作等设计的相关工程路线。应以所选仓库 commit 的配置为准，不能因名称相似把基础 OpenVLA 的调用方式直接套入 OFT。

| 方法 | 数据/训练信号 | 适合起点 | 本服务器状态 |
|---|---|---|---|
| 状态行为克隆 | 状态→动作，监督损失 | 先验证动作语义 | 建议基线 |
| 图像行为克隆/ACT | 图像/状态→动作或 chunk | 演示较充分的单任务 | 未验证部署 |
| Diffusion Policy | 去噪生成动作序列 | 连续动作、多模态演示 | 未验证部署 |
| OpenVLA/OFT | 预训练视觉语言＋动作微调 | 指令泛化、多任务 | 源码目录存在 |
| PPO | 环境交互与奖励 | D1 连续物理控制 | 已有短测任务 |

不要让模型选择先于数据接口：D1 的 16 维关节/轮速策略和 FR5 的六轴演示，不是同一 action space。

## 接口是最容易失败的环节

在启动任何新模型前写一张 action contract：

```text
observation:
  images: 相机顺序/尺寸/颜色空间/时间
  proprio: 关节或 TCP、单位、frame
instruction: 字符串来源和任务定义
action:
  类型: joint target / joint delta / TCP delta / velocity / torque
  顺序: 每一维名字
  单位和参考系
  gripper: +1 是开还是关，连续还是离散
  chunk: 长度、执行频率、何时重新观测
normalization: 对应数据集 key 和统计文件 hash
```

常见 VLA 例子使用末端 6D delta＋夹爪的 7 维动作，但不是通用标准。当前 FR5 数据为 6 维绝对关节目标，缺少夹爪 action；直接 rename 字段不能完成适配。需根据目标模型设计新标签、IK/控制接口，并先离线回放验证。

归一化反变换用同数据集统计；不能把归一化数值当米/rad 送控制器。预测动作成功解码不等于能执行，正负号错误可能在离线 loss 中不明显。

## RLDS 与 LIBERO

RLDS 是 episode/step 数据组织约定，常配 TFDS：observation、action、reward/discount、is_first/is_last/is_terminal，加 episode metadata 和语言任务。builder 决定从原数据解析、特征类型、split 与版本；mod 可能做转换或重打包。目录存在不说明本工程 NPZ 已转换。

LIBERO 基于机器人仿真任务评估终身/多任务学习，常涉及 robosuite/MuJoCo、演示和语言任务。它不是 Isaac Lab 的环境插件，成功率不能直接与本 FR5 或 D1 任务比较。机器人、相机、初始分布、成功条件和控制器都可能不同。

建议复现顺序（待实施）：

1. 固定 Python/torch/transformers/MuJoCo/robosuite 版本和 repo commit；专用环境，避免改 ROS/Isaac runtime。
2. 在 CPU 上验证一个 episode 的 schema/动作单位，再验证单次模型 inference。
3. 单任务、少量 episode 做闭环 LIBERO 评估，记录 seed 和是否使用演示初始化。
4. 用官方预处理/归一化对齐数据，再微调；保存数据版本、LoRA/完整参数、统计文件。
5. 先在仿真 adapter 做动作回放，不通过历史 Real_control 一键启动实机。

## 4090 的资源选择

24 GiB 显存不保证能全参微调大型 VLA。模型参数、精度、优化器状态、激活、batch、图像数和 chunk 长度都占显存。先验证推理，再测 batch=1；需要时考虑 LoRA、混合精度、梯度累积/检查点等。不要引用其他 GPU 或仓库自述训练时间当本服务器承诺。

本次文档不下载权重、不运行 LLM 网络服务、不读取工程里的 API 密钥/证书。发布仓库只保留架构与配置方法；Real_control 目录含敏感文件，不能整目录提交。

官方/项目入口：[OpenVLA](https://github.com/openvla/openvla)、[OpenVLA-OFT](https://github.com/moojink/openvla-oft)、[LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO)、[RLDS](https://github.com/google-research/rlds)、[RLDS builder 示例](https://github.com/kpertsch/rlds_dataset_builder)、[Diffusion Policy](https://github.com/real-stanford/diffusion_policy)。这些解释技术，不构成本地运行验收。
