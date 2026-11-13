# MicNow Lab 模拟协议

本文件只描述本仓库实现的本地模拟器。协议标识保留 `micnow-lab/0.4`，不是实际硬件接口。

## 调用入口

网页和 AI 使用同一个本地服务。服务独占模拟设备子进程，排队发送 JSONL 命令并匹配回执。服务仅监听 `127.0.0.1`，优先使用 PTY，不支持时使用明确标记的进程管道。

```sh
python3 skills/micnow-lab/scripts/serve_device_lab.py --port 0
python3 skills/micnow-lab/scripts/device_client.py --connection CONNECTION_FILE state
python3 skills/micnow-lab/scripts/device_client.py --connection CONNECTION_FILE command device.capabilities
python3 skills/micnow-lab/scripts/device_client.py --connection CONNECTION_FILE setup --speak-mode toggle
python3 skills/micnow-lab/scripts/device_client.py --connection CONNECTION_FILE shutdown
```

`CONNECTION_FILE` 替换成启动输出里的本机路径，并按当前 shell 正确引用。连接文件含操作凭证，不打印内容或提交到仓库。Skill 中的 `SKILL_DIR` 为实际安装目录。

## 配置

| 字段 | 支持值 | 含义 |
| --- | --- | --- |
| `shortcut` | 1–64 个可见字符，例如 `RightOption` | 快捷键标签，不发送系统按键 |
| `speak_mode` | `hold`、`toggle` | 按住说或按两次开始／结束 |
| `target_app` | `codex`、`workbuddy`、`general` | 模拟使用场景；不是调用本 Skill 的 Agent 身份 |
| `voice_tool` | `typeless` | 固定示例，不修改真实应用 |

只修改用户要求的字段。`setup` 会读取能力与现有配置、按需写入、回读核验；未给出的字段保留当前值。用户在网页保存的设置也是 AI 后续读取的当前状态。

## 命令

| 命令 | 参数 | 作用 |
| --- | --- | --- |
| `device.info` / `device.capabilities` / `device.status` | `{}` | 查询模拟身份、能力和状态 |
| `config.get` | `{}` | 读取配置与版本 |
| `config.set` | `{"patch":{"speak_mode":"toggle"},"expected_revision":0}` | 按版本保存指定字段 |
| `config.verify` | `{}` | 由连接服务回读核验最近期望配置 |
| `speak.press` / `speak.release` | `{}` | 模拟按下／松开 |
| `speak.test` | `{}` | 完成样例演练，不录音、不转写 |
| `lab.scenario` | `{"name":"ready"}` | 设置故障场景 |
| `lab.permission` | `{"allow":true}` | 模拟授权，不改变系统权限 |

CLI JSON 参数经 `--args` 传入，禁止把未经引用的用户文本拼接成 shell 命令。下面的版本号只是示例，执行前应读取当前值。

```sh
python3 skills/micnow-lab/scripts/device_client.py --connection CONNECTION_FILE command config.set --args '{"patch":{"speak_mode":"toggle"},"expected_revision":0}'
python3 skills/micnow-lab/scripts/device_client.py --connection CONNECTION_FILE command config.verify
```

故障场景包括 `ready`、`disconnected`、`receiver-only`、`permission-required`、`write-timeout`、`readback-mismatch`、`audio-silent`、`unsupported-app`。只在用户要求演示或测试时注入。`ready` 不自动补齐模拟授权，也不自动证明配置与试说通过。

## 判断结果

- 写入成功还必须回读一致，才报告“模拟配置已保存并核验”。
- 版本冲突时重新读取；不能覆盖另一入口的新设置。
- 超时代表结果未知，先回读，不盲目重复写入。
- 相同有效请求 ID 与相同参数会去重；相同 ID 不同参数会拒绝。成功请求仅缓存最近 256 条，进程退出后失效。
- `hold` 松开结束；`toggle` 松开不结束，需要第二次按下。结束时检查 `speak.active=false`。
- 重置会清空当前会话，关闭浏览器不会结束后台服务；用 `shutdown` 正常清理服务与连接文件。

## 内部帧

`lab.snapshot` 仅供内部连接层使用，公共 CLI 会拒绝该命令；外部读取状态应使用 `state`。

内部设备帧必须具有 `protocol`、`id`、`command`、`args` 四个字段，单行 UTF-8 JSON 不超过 16,384 字节。正常使用应调用 CLI，而不是自行访问内部管道。

```json
{"protocol":"micnow-lab/0.4","id":"read-1","command":"config.get","args":{}}
```

所有设备响应包含 `simulation:true`。来源 `agent`／`web` 是调用来源标签，不是安全身份认证。工具结果会进入当前 AI 对话，不能因此声称全部数据永不离开电脑。
