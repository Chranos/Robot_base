# 相机、手眼标定与抓取感知

## 服务器实际状态

USB 枚举发现 Intel RealSense L515 与 D455。ROS 容器存在 `/home/ros2_realsense_ws`，其中见 librealsense-2.54.1；宿主机另有 `librealsense2.53.1` 与 `docker_realsense`。不要把目录版本当成当前加载的库版本。

本次 ROS 图读取到：

| 话题 | 类型 | 发布者 | 订阅者 |
|---|---|---|---|
| `/d455/color/image_raw` | sensor_msgs/msg/Image | 0 | rqt，1 |
| `/l515/color/image_raw` | sensor_msgs/msg/Image | 0 | rqt，1 |

因此只能确认设备与订阅图存在，不能确认正在采图，更不能确认 depth 对齐/曝光/标定有效。不要为截图直接启动旧的实机综合控制脚本。

```bash
# 服务器宿主机，纯检查
lsusb
docker exec frros2_sj bash -c '
  source /opt/ros/humble/setup.bash
  timeout 8 ros2 topic info -v /d455/color/image_raw --no-daemon
  timeout 8 ros2 topic info -v /l515/color/image_raw --no-daemon
'
```

有发布者后再验证 `camera_info`、color/depth、depth-to-color 对齐、TF 和时间戳，不能只看一张 RGB。

## RGB-D 管线

```text
color + depth + intrinsics + timestamps
            ↓ 对齐、深度尺度、无效像素掩码
      point cloud in optical frame
            ↓ 去桌面/ROI/物体分割
      grasp proposals / object pose
            ↓ 手眼变换到 base
      IK + collision + workspace check
```

彩色和深度的 FOV、分辨率、畸变模型可不同。将 depth 数组按 RGB 像素直接索引前，确认已对齐。深度滤波能平滑噪声，也可能抹平细长/边缘结构；为抓取保留原始值和有效性标记。

## 手眼标定

眼在手上求 `T_ee_camera`，眼在手外求固定 `T_base_camera`。典型方程 `A X = X B` 来自两次末端运动与靶标观测的相对变换；有解不等于标定质量好。

建议的离线验收步骤：

1. 固定工具/相机/靶标安装关系并标记版本；相机内参先独立校准。
2. 收集不同姿态与深度，不只做平移或绕单一轴旋转。
3. 同步记录机器人反馈和图像时间；缓慢移动后的静态采样降低时延误差。
4. 求解后使用保留姿态验证重投影误差与 base 坐标误差。
5. 在多个位置重复验证，记录平移 mm、旋转 deg 的统计与最坏值。

标定产物至少保存：父子 frame、4×4 矩阵、wxyz/xyzw 约定、单位、相机序列号的本地记录、内参、采样时间、求解器、残差和安装版本。公开仓库不放设备私密标识。

本次只看到 handeye 工作区及相关实验文件名，未读取有效标定结果；不提供虚构的变换矩阵。若相机或 TCP 重装，原标定通常需要复核。

## 已发现感知与适配项目

| 项目/路径（均在 `/data/songjie/EMAI` 下） | 技术角色 | 当前证据边界 |
|---|---|---|
| `graspnet-baseline-main` | 点云抓取位姿/候选评估 | 源码目录存在，未验证权重、扩展编译或准确率 |
| `depth-fm-main` | 单目深度基础模型研究 | 存在源码，不视为米制深度替代品 |
| `SpatialBot-main` | 空间感知/视觉语言研究 | 目录存在，未验证模型接口 |
| `Real_control/fairino_realsense_env` | 相机、机器人、标记、记录、MoveIt 适配 | 文件名证据；包含实机代码，不作为默认启动入口 |
| `/home/ext_config_ws/src/camera_flask_server`（ROS 容器） | 图像服务桥接 | package.xml 存在，服务运行与安全参数未核验 |

单目深度可能有尺度偏差，不能将输出直接当相机毫米深度用于接近实物。GraspNet 的 grasp frame、夹爪尺寸、可达性与本工程 90C 不会自动一致。

对感知模型，先用录制 RGB-D 离线验证，再将结果叠加可视化、检查坐标，最后在仿真规划；这几步都不要求控制真实机械臂。

资料入口：[RealSense ROS](https://github.com/IntelRealSense/realsense-ros)、[GraspNet baseline](https://github.com/graspnet/graspnet-baseline)、[DepthFM](https://github.com/CompVis/depth-fm)。
