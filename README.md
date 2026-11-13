# MicNow Lab

让 AI 助手和浏览器操作**同一台模拟 MicNow**：读取设置、修改 Speak 模式、回读核验，并体验模拟按键与故障恢复。无需麦克风硬件，无需另外配置模型 API 密钥。

当前版本 **0.5.0**。这是本地设备实验室，**不会录音、控制真实硬件、发送系统按键或修改外部应用**。页面里的 Speak 文字是预置演练样例。

## 开始安装

需要 Python 3.9+、现代浏览器，以及已登录、允许执行本机命令的 Agent。Skill 本身不需要新增模型密钥，但所用 Agent 仍需要自己的可用账户或模型配置。服务、后续命令和浏览器必须能访问同一个本机 `127.0.0.1`。纯网页聊天读取文件，不等于可以运行本机服务。

下载本仓库（页面上方 **Code → Download ZIP**）并解压，或者：

```sh
git clone https://github.com/Minkewu/micnow-lab.git
cd micnow-lab
```

在解压后的仓库目录运行安装预览，再确认安装。以下以 Codex 为例：

```sh
python3 install.py --agent codex
python3 install.py --agent codex --install
```

`--agent` 可选 `codex`、`claude-code`、`cursor`、`gemini`、`qwen-code`、`kimi-cli`。默认安装到当前用户的技能目录；只想放进一个项目时，加 `--project "/你的项目路径"`。

WorkBuddy 当前使用已核实的项目目录：

```sh
python3 install.py --agent workbuddy --project "/你的项目路径" --install
```

Windows 请先确认 Python 3.9+ 已安装，并将示例中的 `python3` 换为可用的 `py -3` 或 `python`。Windows 客户端端到端运行尚未实测。

安装器只复制 `micnow-lab`，不修改其他技能或 Agent 配置。默认只预览；已有不同版本时必须显式加 `--update`，旧版会备份在技能目录旁的 `.micnow-lab-backups/`。更新后重新打开会话或刷新客户端的技能列表。

## 在 Agent 里使用

Codex 可以输入 `$micnow-lab`；Claude Code 可以使用 `/micnow-lab`。其他本地 Agent 在确认技能已经发现后，直接说：

> 用 micnow-lab 打开本地 MicNow 设备实验室。先读取当前设置，把 Speak 改为按两次开始和结束；保留其他设置，完成后回读核验，并打开同一会话的网页。

AI 应实际启动服务、执行命令和回读结果。网页上修改设置后，AI 会读取到同一个模拟设备的新状态。“连接 AI”页可复制当前会话的操作提示；不要把连接文件的内容或令牌发到公开聊天、Issues 或仓库。

结束时说“关闭这次 MicNow 实验室”，让 AI 执行 `shutdown`。只关闭浏览器标签页不会停止后台进程。

## 十个目标入口

| 名称 | 当前提供的接入方式 | 验证边界 |
| --- | --- | --- |
| Codex | 标准 Skill + 安装器 | 真实 CLI 已完成发现、模型调用、读写与清理；本轮未操作可视网页 |
| Claude Code | 标准 Skill + 安装器 | 实际 CLI 和技能文件已安装；登录阻塞，未运行模型 |
| WorkBuddy | 项目安装器或技能 ZIP | 已打开真实客户端上传入口；文件选择待完成，未验证导入 |
| Cursor | 标准 Skill + 安装器 | 实际 CLI 和技能文件已安装；登录阻塞，尚未验证技能发现 |
| Gemini CLI | 标准 Skill、安装器或原生 GitHub 安装 | 条件性发现已观察；正常信任流程及模型运行待验证 |
| 千问 | Qwen Code 本地客户端 + 扩展入口 | 真实运行时发现与本地扩展导入通过；测试配置缺少认证 |
| Kimi | Kimi Code CLI + 插件入口 | 真实目录发现与本地插件导入通过；测试配置未配置模型 |
| DeepSeek | 通过 Claude Code 等本地宿主加载 Skill | 模型接入与宿主安装分开；不自动配置 API 账户 |
| Perplexity | Computer / Personal Computer 专用根目录 ZIP | 导入格式已核实；本机执行与服务生命周期待实测 |
| 豆包 | 豆包工作个人自定义技能上传 | 官方已确认文件／文件夹上传入口；客户端安装与运行未完成 |

详细步骤、官方来源及每个平台的运行限制见 **[Agent 安装与兼容说明](docs/agents.md)**，本轮版本和证据范围见 **[客户端实测记录](docs/client-validation.md)**。格式适配不等于已经在十个客户端逐一验收，也不表示获得官方市场认证。

## 下载独立技能包

- [标准技能 ZIP](https://github.com/Minkewu/micnow-lab/raw/refs/heads/main/downloads/micnow-lab-0.5.0.zip)：外层是 `micnow-lab/`，用于下载后手动安装及 WorkBuddy 上传。
- [Perplexity 技能 ZIP](https://github.com/Minkewu/micnow-lab/raw/refs/heads/main/downloads/micnow-lab-perplexity-0.5.0.zip)：`SKILL.md` 直接位于 ZIP 根目录。
- [文件校验值](downloads/SHA256SUMS.txt)。两个包包含同一份 Skill 和程序，仅 ZIP 层级不同。

## 只体验网页

无需安装 Skill，也可在仓库目录运行：

```sh
python3 skills/micnow-lab/scripts/serve_device_lab.py --port 0
```

打开启动输出里的 `url`。服务仅监听本机，配置保存在本次模拟进程中。终端按 Ctrl+C 或使用客户端 `shutdown` 结束服务。某些 Agent 的执行隔离或后台超时可能切断本机连接，应按客户端的正常权限流程处理，不需要把服务暴露到公网。

## 数据与权限

程序使用 Python 标准库，没有内置遥测或对外模型请求。命令结果会返回当前 AI 对话，仍受你所用 Agent 的数据处理方式影响。正常关闭会清理连接凭证；强制终止可能残留临时文件。请勿将凭证、日志或真实个人资料提交到 Issues。

## 开发与检查

```sh
python3 -m unittest discover -s tests -v
python3 tools/build_packages.py
```

详见 [验证记录](VALIDATION.md)、[模拟协议](skills/micnow-lab/references/minimum-protocol.md) 和 [版本记录](CHANGELOG.md)。本仓库只含实验室，不包含生产硬件协议、量产固件或其他产品工程。

## 使用授权与反馈

目前公开供查看、下载、安装和运行，**尚未采用开放源码许可证**。请阅读 [使用范围](USAGE.md) 和 [素材说明](ASSET-SOURCES.md)。品牌标识不代表第三方背书。问题和兼容性反馈可在 [Issues](https://github.com/Minkewu/micnow-lab/issues) 提交，请附客户端版本、操作系统、Python 版本及已隐藏敏感信息的错误信息。

## English

MicNow Lab is a hardware-free local simulator shared by an AI agent and a browser. Install the complete `skills/micnow-lab` folder using `install.py`, then ask your local agent to read, update and verify the simulated device. It does not record audio or control real devices or external applications. Python 3.9+ and a shared local execution environment are required. Client-specific instructions and verification limits are in [docs/agents.md](docs/agents.md). This is source-available for installation and use, not an open-source licensed release.
