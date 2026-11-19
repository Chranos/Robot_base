# 排障：按证据定位，不靠重装

## 网络先分层

本机先验证 VPN 地址、路由和 TCP 22，再诊断 SSH 认证。服务端网卡存在不表示客户端隧道正常；ping 被禁也不一定代表 SSH 不通。
macOS 本机应先核对系统设置中的 **1008（L2TP/IPSec）** 是否连接，而不是只看 Tailscale；具体步骤与当前配置边界见 [1008 VPN 指南](17-vpn-1008.md)。

```bash
# macOS 本机
ifconfig
route -n get 192.168.190.200
ping -c 4 192.168.190.200
nc -vz -G 3 192.168.190.200 22
ssh -o ConnectTimeout=8 dengming@192.168.190.200
```

```powershell
# Windows 本机（师兄的电脑也可据此检查）
ipconfig /all
route print
Test-NetConnection 192.168.190.200 -Port 22
ping 192.168.190.200
```

VPN 虚拟网卡的静态地址应由 VPN 分配/管理员规划。`192.168.190.208` 只能在确认 VPN 机制、地址未占用和掩码/路由后使用；不要套用到 Wi-Fi/物理以太网，也不能凭“同网段”绕过 VPN 客户端隔离。

服务端检查：`ip -br addr`、`ip route`、`ss -lnt`、必要时相应服务日志。同伴可连时比较两人的 route、VPN 会话和 TCP 测试；SSH 的 password denied 与 connect timeout 属不同层，不先反复改密码。

## 问题→检查→下一步

| 现象 | 首先查 | 下一步 |
|---|---|---|
| SSH timeout | VPN/路由/TCP 22 | 复核客户端会话和服务端监听；不改 Docker |
| SSH permission denied | 用户名、认证方式 | 用交互方式确认账号，避免连续失败重试 |
| 容器不存在/停止 | `docker ps -a` | 只启动自己的已知容器；勿重建覆盖数据 |
| `/home/...` 不存在 | 命令执行层、bind mount | 用 inspect 确认 `/data/dengming:/home` |
| `fr_90c_ws/install/setup.bash` 不存在 | 当前源码/安装树 | 先 source `/opt/ros/humble`，离线审阅构建计划 |
| `bash -lc` export 报错 | `/etc/profile` | `bash -c`＋显式 source；不要掩盖其他 source 失败 |
| 相机 topic 有名字但没图 | `topic info -v` 发布者数量 | 0 发布者先查驱动；>0 再查 QoS/时间/内容 |
| USB 相机可见但流失败 | 设备占用、带宽、USB 速率、SDK 版本 | 单相机低负载检查；不同时启动重复 pipeline |
| CUDA/Warp 初始化错误 | launcher、experience、vendor | 沿用当前已验证组合，小 smoke；不先升级驱动 |
| USD 只有外形不能控制 | articulation/joint/rigid body | 使用 URDF 转换资产，别拿视觉 USDC 训练 |
| 机器人穿地/漂浮 | collider、初始 pose、根固定、状态写入 | 停止脚本位姿写入，检查动力学/碰撞 |
| D1 轮子转不满圈/位移很短 | continuous joint 的 ±π 限位 | 训练覆盖层禁用位置限位，腿限位保留 |
| D1 看着走，实际没受力 | root/joint state 写入点 | 物理步用 target，检查接触力/位移 |
| PhysX 在动，画面不动/不见 | camera、render interval、fabric/mesh 更新 | 独立验证渲染；不可改物理来迁就视频 |
| PPO NaN | 首次非有限观测/奖励/参数 | 单环境/小动作/模型检查，定位前保存日志 |
| CUDA OOM | nvidia-smi、相机、环境数、模型 | 降环境数/关闭渲染/减 batch；Torch 指标不是总显存 |
| reward 升但机器人不走 | 速度误差、站立奖励、动作限幅 | 固定命令评估、看各项 reward 与滑移 |
| JIT normalizer 报 ignored function | 推理是否 `.eval()` | 保留归一化统计，比较原/导出动作 |
| 数据 validator 不通过 | 首个缺文件/schema/shape | 保留损坏 episode，定位中断/版本，不强行改 success |
| 状态同步冻结 | stale、sequence、解析单位、数据源 | 先离线检查输入，不启动实机控制恢复 |

## 记录最小故障包

保留：时间、命令（去掉凭据）、执行位置、版本、输入文件 hash、第一条错误、退出码、资源快照。不要只截最后一行，也不要整段导出 shell history、环境变量或含令牌的配置。

如果网络暂不可达，继续整理已有证据与源码，标注未复验；不要将历史结果改成当次通过。
