# 服务器、网络、Docker 与持久化

## 当前基线

| 项目 | 2026-11-19 读取结果 |
|---|---|
| 系统 | Ubuntu 22.04.5 LTS，内核 6.8.0-138-generic |
| CPU / RAM | i7-13700K，24 逻辑 CPU，约 31 GiB RAM |
| GPU | RTX 4090，24564 MiB，驱动 580.178.04 |
| `/data` 所在分区 | 总 916 GiB，已用约 636 GiB，可用约 234 GiB；随时变化 |
| VPN 地址 | 192.168.190.200/24，`vpn_vpn` |
| 实验室 LAN | 192.168.1.49/24，`enp9s0` |
| 控制器侧网卡 | 192.168.58.3/24，`enp8s0`；链路 UP 不证明控制器状态流可用 |
| 另有虚拟网络 | 10.161.42.69/24；不假定所有客户端都可访问 |

不把 SSH 密码写进命令、仓库、截图或自动脚本。使用交互密码或个人 SSH 密钥。Windows 客户端可用 PowerShell 自带 OpenSSH；macOS/Linux 用终端。

```bash
# 本机
ssh dengming@192.168.190.200
```

连接问题按 [排障](13-troubleshooting.md) 分层检查。不要仅因为服务端有 VPN 地址，就随意把本机物理网卡改为同网段静态地址。

## 容器的职责

| 容器 | 镜像 | 网络 / 挂载 | 盘点时状态 |
|---|---|---|---|
| `isaacvnc_dengming` | `isaac_vnc:v1.0` | host；`/data/dengming:/home` | 运行 |
| `frros2_sj` | `sunny666666/frros2_desktop:v1.0` | host；`/data/songjie:/workspace` | 运行 |
| `isaacsim_env` | `dengminglrobotlab:isaacsim-5.1-20260731` | bridge；`/lab/workspace:/workspace` | 停止 |
| `isaac_sj` | `nvcr.io/nvidia/isaac-lab:2.1.0` | 本次未核对挂载 | 停止 |

还有其他成员容器；不将其状态当成个人服务，不在文档中给出批量重启/清理指令。5.1 是镜像标签证据，不是本次运行版本验证。`/lab/workspace` 本次为空，不宜拿该停止容器当现成项目入口。

```bash
# 服务器宿主机：只读检查
docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Image}}'
docker inspect -f '{{.Name}} network={{.HostConfig.NetworkMode}} mounts={{json .Mounts}}' \
  isaacvnc_dengming frros2_sj
nvidia-smi
df -h /data

# 已存在的个人容器停止时才启动
docker start isaacvnc_dengming
docker exec -it isaacvnc_dengming bash
```

容器内 `/workspace/isaaclab` 是运行时；个人持久化代码在 `/home/isaaclab_fairino`。写入容器可写层的文件不会因 stop 消失，但容器删除重建时会丢失；bind mount 内文件独立于容器生命周期。

### 新容器示例，非现有容器的恢复命令

仅在确需独立环境时使用唯一名称/目录。原教学命令包含 `--privileged --net=host --gpus all`，权限范围大；已有容器优先复用，不为读文档再创建。

```bash
# 服务器宿主机；先确认目录和名称属于自己且不存在同名容器
mkdir -p /data/dengming/new_experiment
docker run -d -it --net=host --privileged \
  --name isaacvnc_dengming_new \
  --mount type=bind,source=/data/dengming/new_experiment,destination=/home \
  --gpus all isaac_vnc:v1.0
```

该新目录不自动包含 Fairino/D1 工程，也不自动获得 CUDA 兼容层。不要据此承诺一条命令即可复刻个人容器。

## noVNC 与无头运行

无头模式不创建交互桌面，物理照常运行；加相机时仍可离屏渲染 RGB/深度。PPO 训练不需要桌面或相机，可减少显存和开销。

旧资料写 `:999`，本次监听表出现 `9993` 和 `5903`，但未确认其所属进程。端口是否存在、属于哪个容器、VNC display 与 WebSocket 代理是否匹配，需要同时检查：

```bash
# 服务器宿主机
ss -lnt | rg ':(999|9993|5900|5903)\b'
docker exec isaacvnc_dengming sed -n '1,180p' /workspace/novnc.sh
```

若服务器没有 `rg`，可用 `grep -E`。确认脚本未与他人 display/端口冲突后，再按其参数启动；不要用猜测的 URL 修改公共脚本。跨 VPN 推荐 SSH 隧道与视频文件回传，LAN 桌面延迟通常更低。

## 资源与可复现性

启动训练前记录 GPU/磁盘与其他任务；`nvidia-smi` 空闲只是一个时刻。镜像标签可变，至少记录镜像 ID、运行时版本、代码 hash、模型 hash、seed 和配置。

保留 `/data/dengming/isaaclab_fairino` 的代码、USD 相对依赖、`apps`、`vendor` 和配置。备份时不只复制顶层 USD：它可能引用 `configuration/` 或绝对路径。容器镜像不是个人 bind mount 数据的备份。
