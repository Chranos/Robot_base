# 单向状态同步与 Sim-to-Real

## 先定义“同步”

| 类型 | 数据方向 | 当前工程 |
|---|---|---|
| 状态镜像 | 实机测量→仿真显示 | 接收式脚本存在，当前反馈未验证 |
| 离线回放 | 录制状态→仿真 | 建议测试入口，不要求实机在线 |
| 策略迁移 | 仿真训练策略→实机命令 | 尚未完成，需要独立验证/授权 |
| 双向闭环 | 实机/仿真互相影响 | 不属于已部署能力 |

镜像准确只能证明模型/角度/反馈协议对齐，不能证明质量、摩擦或策略可迁移。

## FR5 接收式路径

```text
控制器 TCP 8081 ──recv──> relay_fairino_tcp_udp.py
                             │ JSON、仅发往 loopback
                             v
                       127.0.0.1:15050/UDP
                             │
                             v
                  sync_real_to_isaac.py → 虚拟 j1…j6
```

若已有 ROS 状态发布者，可用 `relay_fairino_state_udp.py` 订阅 `/nonrt_state_data` 后发 loopback。Isaac 镜像脚本默认 UDP；直接 ROS 模式要求 Isaac Python 可 import rclpy 和 fairino_msgs，当前不能假定满足。

TCP relay 的 controller socket 只 `recv`，没有应用层 send/write；但建立 TCP 本身会有握手/ACK，不能描述成“网络上零字节”。UDP 仅在本机 loopback 发送。两个容器使用 host 网络时共享该回环；bridge 模式的 127.0.0.1 不是同一个网络命名空间。

## 协议与防旧数据

relay 按历史 V3.8.3 打包结构解析：帧头 `/f/b`、长度字段、帧尾 `III/b/f`、六个 little-endian double 关节角。增量 buffer 处理分包/粘包，检查长度与有限值。其他固件/驱动结构可能不同，不能只因为连接成功就相信解析。

JSON schema 为 `fairino_joint_feedback_v1`，包含 sequence、sent_monotonic_ns、joint_deg。仿真转换为 rad，校验名字与顺序；stale timeout 默认 0.5 s，失去更新时冻结虚拟状态，max-step 默认 0.15 rad 限制显示跳变。

这些限幅只作用于仿真镜像，不是实机急停。反馈中没有可靠的实测夹爪宽度，不能从完成标志猜夹爪位姿。

## 当前链路检查，不启动机器人驱动

```bash
# 服务器宿主机：不向控制器建立连接
ip -br link show enp8s0
ip -br addr show enp8s0
ip route get 192.168.58.2
docker inspect -f '{{.Name}} {{.HostConfig.NetworkMode}}' frros2_sj isaacvnc_dengming
```

当前确认接口为 192.168.58.3/24；控制器地址 192.168.58.2 来自历史配置，未在本次通信验证。UP/route 不能代替有效状态帧。文档任务没有运行 relay、SDK、RPC 或控制 API。

需要复查只读同步时，先核验协议/物理状态和已有话题，再单独启动接收器。不要为取得反馈启动 `FairinoHardwareInterface`、MoveIt demo、ros2_cmd_server 或 ServoJ 例程；历史整套启动可能带出实机命令。

## 训练策略迁移需要补什么

对 D1，目前需补：

- 名字/方向/零位/减速比，关节限位和电机响应实测。
- 观测同步、基座速度估计、IMU 对齐、滤波与延迟。
- PD、力矩/速度/温度等限幅的实际接口定义。
- 摩擦、质心、惯量、轮半径、接触几何、驱动时延的随机化/校准。
- Sim-to-Sim 与故障注入：掉帧、陈旧数据、观测 NaN、策略输出异常。
- 分级验收：离线回放→不发命令的 shadow inference→受约束测试→更多动作。

shadow inference 是预测并记录动作，不将其接给驱动。当前没有实现/验收此链路，不把它写成可用功能。任何实机执行都属于单独操作任务，不能从文档或仿真训练的授权中推导。
