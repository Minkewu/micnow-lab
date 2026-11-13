---
name: micnow-lab
description: Open the local MicNow device lab without hardware. Send actual tool commands through a local bridge to a simulated device, verify its replies, and keep AI and Web on the same session. Supports configuration, simulated Speak and fault recovery; no real microphone, device or external-app control.
metadata:
  version: "0.5.0"
---

# MicNow 设备实验室

在没有硬件时，让用户通过 Web 自己设置，或通过当前 AI 对话操作同一台模拟 MicNow。必须实际调用工具，依据设备回执汇报，不把动画、模拟授权或预置文字当成真机结果。

## 运行条件

需要能够执行本机命令的桌面宿主、Python 3.9 或以上，以及能访问同一台电脑 `127.0.0.1` 的浏览器。先检查这些条件；缺少 Python 或本地执行能力时说明具体缺项，不自动安装软件，也不声称服务已启动。Python 服务、CLI 与浏览器必须在可互通的同一本地执行环境；宿主需要允许后台进程和本机 loopback。当前运行链路已在 macOS 验证，其他客户端与 Windows 不因格式兼容而视为已实测。受限时按宿主的正常授权流程处理，不自动修改安全设置、不改为公网监听。

工具输出会返回当前 AI 对话，不能宣称所有数据永不离开本机。v0.4 的连接凭证在正常关闭时清理；强制终止可能残留。

## 启动与复用

如当前对话已有 v0.4 `connection_file`，先用 `state` 读取并复用。不要扫描其他聊天的临时目录或另建会话隐藏故障。

没有正在使用的服务时，在保留的终端会话启动：

```text
python3 "SKILL_DIR/scripts/serve_device_lab.py" --port 0
```

先确认可用的 Python 3.9+ 命令（例如 `python3`，Windows 可能为 `py -3`），以下命令按已发现的运行器替换。将 `SKILL_DIR` 替换为本技能绝对目录。用启动结果的真实 `url` 打开可见的浏览器预览，保存返回的 `connection_file` 供本对话后续操作。打开失败时提供真实 URL，不能声称页面已显示。服务只监听本机，不注册开机启动；用户关闭体验时终止本次服务并清理其子进程。

`connection_file` 只保留在本机，包含操作凭证，不打印内容、不将 token 粘贴进聊天或协议文档。CLI 会安全读取它。Web 与 CLI 必须使用同一服务；Web 上修改的配置是后续操作的当前值。

最初说明一次：这是模拟设备，不会修改真实麦克风、Typeless 或其他应用。随后依靠界面的“本地模拟”标识，不重复打断体验。

## 实际操作

以下 `CONNECTION_FILE` 使用启动结果给出的路径。用结构化参数或正确的 shell 引号传值，不把用户文本拼成可执行代码。

```text
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" state
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" command device.capabilities
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" command config.get
```

仅查看时不改变配置。用户要求自动设置时，沿用已明确提供的偏好；未知的值使用当前模拟预设并说明来源，不宣称已读取真实软件。保留用户没有要求改变的配置。

```text
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" setup --shortcut RightOption --speak-mode toggle --target-app codex
```

这是示例值，不能当作所有用户的默认设置。宿主名称与模拟配置的 `target_app` 是不同概念；不要因为正在 Claude Code、Cursor 或其他宿主里运行就自动改动目标应用。该模拟字段仅支持 `codex`、`workbuddy`、`general`；用户需要通用目标时使用 `general`，它不代表已控制任何外部应用。`setup` 通过真实本地通信执行读取能力、读取配置、必要的写入和回读核验。它不是大模型聊天接口，也不会操作真实目标 App。

单项修改先读取当前 `revision`，再提交 `config.set`，完成后调用 `config.verify`。请求参数是 JSON，使用 CLI 的 `--args` 参数；具体字段见 [最小协议](references/minimum-protocol.md)。配置版本冲突时重新读取，不能静默覆盖 Web 的修改。用户明确要求更改模拟设置时可以直接执行，不重复征求许可。

结果判断：

- `ok` 与设备回执、回读验证都成功，才能说“模拟配置已保存并核验”。
- 超时表示结果未知，先回读；没有证据时不能说成功或重复写入。
- 回读不符时停止，不覆盖故障记录。说明目前配置与预期的差异。
- 断连、权限待允许或不支持时保留现场，告知当前需要的一个动作。
- 配置核验与 Speak 演练分别报告；不能将配置成功说成真实音频可用。

## Speak 与故障演练

用户在 Web 可以直接试按 Speak。用户在聊天明确要求模拟按下／松开时，可以调用对应工具。只有用户要求演示或测试时才代为完成演练。

```text
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" command speak.press
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" command speak.release
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" command speak.test
```

`speak.test` 返回预置样例，不录音、不转写、不向任何应用输入文字。按住说与按两次的模拟行为只证明本实验的协议处理，不证明真实语音工具支持。

`hold` 模式松开即停止；`toggle` 模式松开不会停止，需要再调用一次 `speak.press`、`speak.release` 才结束。完整演练后读取状态确认 `speak.active=false`，不要让用户以为演练已经结束而设备状态仍在输入中。

用户要求异常测试时使用 `lab.scenario`。支持 `disconnected`、`receiver-only`、`permission-required`、`write-timeout`、`readback-mismatch`、`audio-silent`、`unsupported-app` 和 `ready`。`lab.permission` 只用于用户已同意的模拟授权，不改变操作系统权限。恢复环境不自动证明配置或试说通过。

用户取消时停止继续发操作，不通过新建会话绕过当前失败。重置会清空当前模拟会话，只在用户要求重新开始或明确授权的测试中使用。

用户结束体验时，关闭本次服务与其模拟设备进程：

```text
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" shutdown
```

## 边界与资料

- 当前管理报文通过本地虚拟串口 PTY（不支持的平台使用明确标记的进程管道）到独立模拟设备进程；不是已实现的 USB CDC、Management HID 或量产固件。
- 不枚举真实硬件、不录音、不输出键盘事件、不修改外部软件、不安装常驻服务、不发布网站或平台插件。
- 本地工具回执只能证明这次本地调用；Skill 文件被识别、ZIP 打包或上传成功，都不等于客户端端到端测试或市场审核通过。普通云端聊天不能直接访问用户电脑的 localhost。
- 三枚自定义键与原 Web 已锁定按键页不在本实验改动范围。
- 需要详细命令时读 [模拟协议](references/minimum-protocol.md)；真机能力边界见 [硬件说明](references/hardware-questions.md)。这些实验不替代真实固件验收。
