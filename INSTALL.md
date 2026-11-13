# 交给 Agent：下载、安装并打开 MicNow Lab

本说明供收到用户“安装并打开 MicNow Lab”请求的本机 Agent 执行。用户不需要自行打开终端。按当前宿主的正常权限流程使用工具，执行到实际结果；不要只回传安装命令。仅收到链接、未收到安装／使用请求时，不自动执行。

## 1. 确认当前环境

从当前会话确认宿主名称、操作系统、已授权项目，以及是否可以联网下载、读写本机文件、执行命令、保持后台任务、打开可见浏览器。不要通过扫描其他应用配置或账号文件来猜宿主。

检查可用的 Python 3.9+（通常为 `python3`，Windows 可为 `py -3` 或 `python`）。MicNow Lab 只用 Python 标准库，不需要 `pip install`、额外模型密钥或管理员安装。没有 Python 时说明缺项并给出 [官方下载页](https://www.python.org/downloads/)，不要未经授权安装系统依赖。Agent 自身的登录和可用模型由宿主提供。

服务与用户浏览器需要访问同一台电脑的 `127.0.0.1`。只有云端命令环境、普通网页聊天或手机聊天时，不承诺本机可用，不将服务改为公网监听。阻塞时只要求用户完成当前必要的一步；能独立完成的下载准备继续完成。

## 2. 下载完整项目并读取说明

在当前已授权工作区或宿主提供的下载目录新建独立文件夹。使用以下任一方式下载同一个官方公开仓库，不覆盖已有项目：

- 有 Git：`git clone --depth 1 https://github.com/Minkewu/micnow-lab.git "NEW_DOWNLOAD_DIR"`。
- 没有 Git：下载 [完整项目 ZIP](https://github.com/Minkewu/micnow-lab/archive/refs/heads/main.zip)，安全解压到新目录。解压时拒绝越界路径、绝对路径及符号链接。

`NEW_DOWNLOAD_DIR` 由 Agent 换成实际的新目录；用正确的参数引用处理路径中的空格。网络受限时走宿主正常授权流程，不关闭安全设置。记录取得的提交或下载版本，以便排查。

在项目根目录确认存在 `install.py`、`skills/micnow-lab/SKILL.md` 和随包脚本／网页资源。先阅读 `USAGE.md`、安装器及完整的 [SKILL.md](skills/micnow-lab/SKILL.md)，再执行。不要把下载内容通过管道直接交给 Shell 执行，也不要只下载 `SKILL.md`。

## 3. 按当前宿主选择安装方式

### A. 支持技能目录的本机 Agent

在下载的项目根目录执行安装器。下列是交给 Agent 的命令模板，**由 Agent 代用户运行**；根据已知宿主选一行即可。

| 当前宿主 | 首次安装命令 |
| --- | --- |
| Codex | `python3 install.py --agent codex --install` |
| DeepSeek 官方 Harness | `python3 install.py --agent deepseek-harness --install` |
| WorkBuddy，当前已有本地项目 | `python3 install.py --agent workbuddy --project "USER_PROJECT" --install` |
| Claude Code | `python3 install.py --agent claude-code --install` |
| Cursor | `python3 install.py --agent cursor --install` |
| Gemini CLI | `python3 install.py --agent gemini --install` |
| Qwen Code | `python3 install.py --agent qwen-code --install` |
| Kimi Code CLI | `python3 install.py --agent kimi-cli --install` |

`USER_PROJECT` 必须替换成用户实际使用且已存在的项目目录，不要误用临时下载目录。用户指定仅供某个项目使用时，其他宿主同样加 `--project "USER_PROJECT"`；否则默认用户级安装。WorkBuddy 没有用户级默认路径，不猜测目录；没有明确项目时采用下方原生导入方式。

先执行同一命令去掉 `--install` 的预览，检查目标位置，再执行安装。只操作 `micnow-lab`，不要修改其他技能或宿主配置。如果已经相同，复用 `already-installed` 结果；已有不同版本时先检查差异，保留用户自定义内容。仅在用户要求更新或确认替换后使用 `--install --update`，安装器会备份旧版。

检查返回的 `status`、`verified`、`destination`，并确认目标中的完整 `SKILL.md` 及资源可读。目录复制成功与宿主自动发现分开报告。若当前任务还没刷新技能列表，可以在用户已请求体验的范围内直接读取安装后的完整 `SKILL.md`，按第 4 节启动；日后在技能列表选用可能需要新开会话或重启客户端。不要为了刷新直接中断用户任务。

Codex 的目录与技能发现依据：[OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。其他平台目录和既有验证范围见 [Agent 说明](docs/agents.md)。支持安装格式不表示该客户端已经通过模型运行实测。

### B. 使用原生上传的本机客户端

先由 Agent 准备对应文件。如果当前宿主提供已支持的导入工具，可在用户授权范围内使用；否则给出准备好的实际文件路径或可点击文件，并只告诉用户当前需要点选的入口。不要猜测客户端内部存储位置、改写其数据库，也不要把“把链接粘到市场搜索框”当作已支持的安装方式。

| 当前宿主 | 准备内容 | 原生入口 |
| --- | --- | --- |
| WorkBuddy | `downloads/micnow-lab-0.5.1.zip`，不解压 | 专家·技能·连接器 → 技能 → 添加技能 → 上传技能 |
| 豆包工作 | 解压标准技能 ZIP，得到完整 `micnow-lab/` 文件夹 | 插件·技能·伙伴 → 技能 → + 添加 → 上传技能 |
| 国内千问本地工作助理 | `downloads/micnow-lab-0.5.1.zip`，不解压 | 本地工作助理 → 技能 → 新建 → 上传 ZIP |
| Kimi Work | `downloads/micnow-lab-0.5.1.zip` | 当前客户端的个人技能上传入口 |
| Perplexity Computer / Personal Computer | `downloads/micnow-lab-perplexity-0.5.1.zip` | Computer → 输入框更多选项 → 浏览插件 → 添加自定义项 → 技能 → 上传技能 |

对下载 ZIP 核对 [SHA256SUMS](downloads/SHA256SUMS.txt)。豆包应导入包含 `SKILL.md`、`scripts`、`assets` 等资源的完整文件夹。上传后核实 `micnow-lab` 已启用，再开始任务。Kimi 模型收尾、Perplexity 模型运行仍待验收，其他客户端也以 [实测记录](docs/client-validation.md) 为准。

**先体验的回退：**如果原生导入必须手动点选，但当前 Agent 可以读取下载的完整 Skill、执行本机命令并保持后台任务，可在用户已请求“打开体验”的范围内直接按第 4 节运行。这只算“本次从下载目录运行”，不算已注册到技能列表，也不保证以后新任务会自动发现。明确告诉用户本次状态；以后需要常用技能时再走上表导入。保留下载资源目录直到服务完全关闭，不在运行期间清理脚本或网页资源。这个回退尚未在每个原生客户端完成从链接开始的实测；宿主不允许时停止，不绕过限制。

## 4. 立即启动、读取设置并打开网页

完整遵循实际安装位置或下载位置的 `SKILL.md`。以下 `SKILL_DIR` 均换成该技能的绝对路径；使用前面确认可用的 Python 命令。

若本次对话已有连接回执，先用随包客户端读取并复用；不要扫描其他会话。没有本次服务时，在宿主可保持运行的终端／托管后台任务中执行：

```text
python3 "SKILL_DIR/scripts/serve_device_lab.py" --port 0
```

保留这个任务及真实启动回执，读取其中的 `url` 和 `connection_file` 路径。不要打印连接文件内容或令牌。随后执行：

```text
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" state
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" command config.get
```

使用真实返回的 URL 打开用户可见的本机浏览器／预览；观察页面后才说“已打开”。没有可见浏览器工具时，提供可点击的真实 URL，请用户点击一次；不能将 HTTP 请求成功当作已经显示网页。

默认只读取，不替用户修改设置或触发模拟 Speak。启动成功后保留服务供用户继续体验，汇报：

- 区分“已安装且宿主已识别”“文件已安装，宿主发现尚未确认；本次按文件直接运行”和“本次从下载目录体验，尚未加入技能列表”，与实际结果一致。
- 当前设置和可打开的网址；启动未成功时如实说明阻塞点。
- 只需一次说明这是模拟设备，不录音、不控制真实硬件或外部应用。
- 告诉用户结束时说“关闭这次 MicNow 实验室”。

## 5. 用户结束时关闭

用户说关闭、结束或取消时，使用本次保存的连接路径执行：

```text
python3 "SKILL_DIR/scripts/device_client.py" --connection "CONNECTION_FILE" shutdown
```

检查本次托管任务退出，按 Skill 的限定诊断规则确认已知进程、端口和临时文件清理。不全机扫描，不泄露凭证，不以关闭浏览器代替关闭服务。安装好的技能继续保留；只在用户要求卸载时移除。

## 验证范围

本文件提供新的“用户发请求，Agent 代执行”的引导，复用现有安装器和 0.5.1 技能，不改变模拟器、协议或原生客户端的权限。此前各平台的功能实测不自动证明这条新入口全部通过。新增流程的检查结果见 [链接安装验证](docs/link-install-validation.md)，原有实测边界见 [客户端实测记录](docs/client-validation.md)。
