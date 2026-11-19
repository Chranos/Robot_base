# 机器人资产：URDF、Xacro、SRDF、USD 与物理检查

## 各文件负责什么

| 文件 | 负责 | 不能代替 |
|---|---|---|
| URDF | link/joint 树、关节轴、限位、质量惯量、visual/collision | 控制器和规划器配置 |
| Xacro | URDF 的宏、参数、复用；展开后才是模型 | 运行时运动求解 |
| SRDF | group、end-effector、禁碰对、命名姿态、虚拟关节 | 几何/动力学定义 |
| STL 等网格 | 外形，单位由资源约定决定 | 关节、质量和控制 |
| USD | 场景组合、引用、材质、层覆盖及物理 schema | “文件能打开”不证明 articulation 可训练 |
| YAML | joint limits、kinematics、controller 等 | 与 URDF 名字不匹配时不会自动修复 |

`visual` 可以精细，`collision` 应兼顾精度和计算成本；对动态刚体直接用复杂非凸网格可能失败或代价高，需选择凸包/凸分解/简单几何并验证。

## FR5 的模型选择

有三类容易混淆的来源：

1. `/data/songjie/pkgs/config`：基础 `fairino5_v6_robot.*`、MoveIt/ros2_control YAML。
2. ROS 容器 `/home/383_ws/fr_90c_ws`：`fairino_gp_description` 和 `fairino5_90c_config`，对应历史 90C 工程。
3. 个人目录 `/data/dengming/isaaclab_fairino/assets/fairino5_v6_90c`：为 Isaac 处理资源路径的派生资产。

历史抓取以第 2 类为来源；第 1 类虽也是 FR5，工具/夹爪/配置可能不同。迁移时对照 joint names、`g_base_link`、`Left_Pad_Link`/`Right_Pad_Link`，不能只对照机械臂外观。

Isaac 4.5 导入器对本工程的 ROS `package://` 路径解析不完整，因此派生 URDF 使用容器内绝对 mesh 路径。原始 ROS 资产保留不改。迁移另一台机器时需重新展开/改路径并转换，不能只拷贝顶层 USD。

## D1 Max 的两种资产

资料包原始 `SM_ZNZZSYS_Device_03.usdc` 是视觉模型；历史检查记录显示 1 个 mesh、0 个物理 joint。可展示外形，不能直接训练。

训练使用 `max_description/urdf/max.urdf` 转换的 `d1_max_renderable.usd`，29 个物理 body、16 个可驱动 DOF。四条腿标识：FAR、FBL、RAR、RBL；每腿 ABAD/HIP/KNEE/FOOT。

`training/prepare_asset.py` 生成覆盖层 `training/assets/d1_max_training.usda`，不覆盖原 USD：

- 腿关节保留原位置限位。
- 四个 FOOT 关节改为 ±inf 连续限位，修复 URDF 声明 continuous 却写 ±3.14 的矛盾。
- 生成 `asset_audit.json`，记录原文件 hash、关节信息和质量。

USD revolute limit 单位是度；Isaac Lab tensor 中关节角通常是 rad。源文件数字比较前先确认接口单位。

## 动力学资产的验收顺序

| 检查 | 方法 | 通过标准 |
|---|---|---|
| 资源完整 | 加载 USD，遍历引用/mesh | 无缺失引用、尺度正确 |
| 拓扑 | 查看 articulation root、body、joint、axis | 名称/数量/父子结构一致 |
| 惯性 | 查 mass、COM、惯量主值 | 正质量、有效惯量；零值语义明确 |
| 碰撞 | 打开 collision 可视化、落地测试 | 不穿地，形状不异常放大 |
| 限位 | 单关节小幅目标、轮足多圈 | 腿不越界，轮连续旋转 |
| 驱动 | 记录目标、实测角/速度/力矩 | 无瞬移、NaN、持续饱和 |
| 接触 | 记录地面反力/滑移/高度 | 支撑合理，无隐藏固定根 |
| 并行 | 多环境 clone/reset | 无跨环境碰撞/状态串扰 |

训练层报告中 17 个主要连杆显式质量合计约 41.0453 kg，另有 12 个灯/传感器连杆采用 0 值自动计算质量。这个合计不是已核实整机质量。自碰撞当前关闭，不能宣称所有动作都符合真实结构约束。

## 可复现入口

```bash
# 服务器宿主机；已部署项目内生成训练覆盖层，有文件写入
cd /data/dengming/isaaclab_fairino/robotdog_d1_max/training
bash run.sh --mode prepare
bash run.sh --mode smoke --num-envs 4 --steps 400
```

FR5 重新转换属于重建操作，先备份输出并核对 [运行时](05-isaac-runtime.md)，不要把旧 asset 的参数直接用于 D1。模型许可未在本仓库确认，厂商 STL/STEP、SDK 压缩包和 USD 不随公共仓库发布。
