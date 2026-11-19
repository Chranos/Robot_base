# ROS 2、MoveIt 与历史机械臂工程

## 软件分工

```text
URDF/Xacro ──> robot_state_publisher ──> /tf、/tf_static
/joint_states ──────────┘

目标位姿 ──> MoveIt(move_group) ──> trajectory controller
                                     │
                               ros2_control hardware
                                     │
                                厂商机械臂接口
```

ROS 2 topic 是流数据，service 是请求/应答，action 用于可取消、长时间任务。MoveIt 负责规划和碰撞场景；ros2_control 负责把状态/命令接口接给控制器；厂商 hardware 插件可能直接下发实机运动。

`robot_state_publisher` 不做 IK，也不发布真实传感器状态。`joint_state_publisher_gui` 可显示虚拟关节，不能当成硬件反馈。

## 当前实际工作区

ROS 容器为 `frros2_sj`，发行版 Humble：

| 路径 | 已发现内容 | 说明 |
|---|---|---|
| `/home/383_ws/frcobot_ros2-3.0.0_RobotV3.8.3` | `fairino_hardware`、`fairino_msgs`、`fairino_description`、多个机型 MoveIt config | 历史驱动源码，不混用不同固件结构 |
| `/home/383_ws/fr_90c_ws` | `fairino_gp_description`、`fairino5_90c_config` | 90C 实验描述和配置 |
| `/home/ros2_control_ws` | realtime_tools/control_toolbox 等源码 | 基础控制工具，不代表 hardware 正运行 |
| `/home/ext_config_ws/src` | `ext_config`、`camera_flask_server` | 自定义配置/图像服务 package.xml 存在 |
| `/home/ros2_realsense_ws` | librealsense-2.54.1 来源目录 | 和宿主机 `librealsense2.53.1` 是不同来源 |
| `/home/handeye_ws` | 工作区目录 | 本次未找到足够证据确认其有效标定产物 |

宿主机另有 V3.8.6 驱动源码。不能用目录“版本更新”推断固件已升级、驱动已替换；反馈帧布局也必须对应实际版本。

## 本次发现的配置漂移

旧 README 让人 `source /home/383_ws/fr_90c_ws/install/setup.bash`，但本次该文件不存在。直接复制该命令会失败。源码 package 存在不等于 workspace 已 colcon build。

`bash -lc` 还会触发 `/etc/profile` 第 28 行两个无效 export。盘点使用 `bash -c` 加显式 source；这绕过登录配置错误，不是重建环境。修改共享 profile 前应单独审阅，当前文档工作未修改它。

```bash
# 服务器宿主机；只读检查，不启动驱动
docker exec frros2_sj bash -c '
  source /opt/ros/humble/setup.bash
  printf "ROS_DISTRO=%s\n" "$ROS_DISTRO"
  test -f /home/383_ws/fr_90c_ws/install/setup.bash
  find /home/383_ws/fr_90c_ws -maxdepth 3 -name package.xml
  timeout 8 ros2 node list --no-daemon
  timeout 8 ros2 topic list --no-daemon -t
'
```

最后三个命令可正常运行不代表 `test` 成功；单独检查退出码或用 `if`，不要把整段的最后退出码当所有步骤通过。

## 历史状态接口

`fr_state_brodcast`（历史源码拼写）读取反馈，发布 `/nonrt_state_data`，类型 `fairino_msgs/msg/RobotNonrtState`；`j1_cur_pos...j6_cur_pos` 单位为度。标准 `/joint_states` 则按名字匹配 `j1...j6`、单位 rad。

本次 node list 只看到了 `rqt_gui_cpp_node_5604`；未观测到机械臂状态节点或 `/nonrt_state_data`。因此不能声称当前已实时同步。DDS 图发现有时间窗口/域限制，这也不是“全服务器永远没有该节点”的证明。

原 hardware 的 `write()` 路径会周期调用 `ServoJ`，不要为检查 topic 启动整套 `demo.launch.py`、controller_manager 或 hardware interface。状态读取应走 [独立只读路径](11-sim-to-real.md)。

## 如何读 MoveIt 配置

| 配置 | 检查重点 |
|---|---|
| `*.srdf` | arm group 包含哪几个 joint、end effector 是哪个 link、禁碰对是否过宽 |
| `kinematics.yaml` | solver、group 名、timeout、搜索分辨率 |
| `joint_limits.yaml` | velocity/acceleration 是否与 URDF/控制器相容 |
| `ros2_controllers.yaml` | joint 名称、command/state interface、update rate |
| `moveit_controllers.yaml` | FollowJointTrajectory action 名、controller 映射 |
| `initial_positions.yaml` | 初始角度与坐标/限位 |
| `*.ros2_control.xacro` | fake/mock hardware 与真实 hardware plugin 选择 |

先验证离线模型、TF、规划场景和 mock hardware，再讨论真实执行。`ros2 topic echo` 本身只订阅，但在 SDK 或 launch 中 import/构造对象可能建立硬件连接，不能以“只想看看”为由运行未知脚本。

## 常见图通信问题

ROS_DOMAIN_ID、RMW 实现、网络发现、多网卡、host/bridge 和 QoS 都会影响发现与收包。图像常用 BEST_EFFORT；订阅者请求 RELIABLE 时可能收不到 BEST_EFFORT 发布者。先用 `topic info -v` 检查两端，再看 `hz`/时间戳，不先改 QoS 或重启所有进程。

官方概念参考：[ROS 2 Humble](https://docs.ros.org/en/humble/Concepts.html)、[MoveIt Humble](https://moveit.picknik.ai/humble/index.html)、[ros2_control Humble](https://control.ros.org/humble/index.html)。
