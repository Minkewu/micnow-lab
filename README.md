# MicNow Lab

让 AI 助手和浏览器操作**同一台模拟 MicNow**：读取设置、修改 Speak 模式、回读核验，并体验模拟按键与故障恢复。无需麦克风硬件，无需另外配置模型 API 密钥。

当前版本 **0.5.1**。这是本地设备实验室，**不会录音、控制真实硬件、发送系统按键或修改外部应用**。页面里的 Speak 文字是预置演练样例。

## 选择你的 Agent，三步开始

以下五个入口已有真实模型运行记录，具体版本和覆盖范围写在各节末尾。**目前实测环境为 macOS；Windows、Linux 尚未完成客户端运行实测。**

| 你正在使用 | 下载什么 | 安装步骤 |
| --- | --- | --- |
| Codex CLI | 完整项目 ZIP | [前往 Codex](#codex) |
| WorkBuddy | 标准技能 ZIP，保持压缩包 | [前往 WorkBuddy](#workbuddy) |
| 豆包工作 | 标准技能 ZIP，解压后上传文件夹 | [前往豆包工作](#doubao) |
| 千问本地工作助理 | 标准技能 ZIP，保持压缩包 | [前往千问](#qwen) |
| DeepSeek Harness | 完整项目 ZIP | [前往 DeepSeek Harness](#deepseek) |

**安装前准备：**电脑需要 Python 3.9 或以上、浏览器，以及已安装并登录、可以执行本机命令的对应 Agent。没有 Python 时可从 [Python 官网](https://www.python.org/downloads/) 安装。MicNow Lab 不需要另外配置模型 API 密钥；Agent 自身仍需可用账号或模型配置。首次使用时按客户端提示允许本次本机运行。

本指南使用各平台的**本机工作／编程入口**。普通网页聊天、手机聊天、远程或云端 Agent 不自动具备运行这个本机实验室的能力。其他 Agent 的进度见 [兼容状态](#compatibility)。

<a id="codex"></a>

### Codex CLI

1. **下载：**点击 [下载完整项目 ZIP](https://github.com/Minkewu/micnow-lab/archive/refs/heads/main.zip) 并解压，也可点击本页上方 **Code → Download ZIP**。打开解压后的 `micnow-lab-main` 文件夹，里面应有 `install.py`。
2. **安装：**打开终端，输入 `cd` 和一个空格，把上述文件夹拖入终端，按回车；再复制执行：

   ```sh
   python3 install.py --agent codex --install
   ```

3. **开始用：**在本机 Codex CLI 新开会话，发送：

   > 使用 $micnow-lab 打开本地 MicNow 实验室，读取当前设置，并打开同一会话的网页。

安装后找不到技能时，重启 Codex 再开会话。这里下载的是**完整项目 ZIP**；下方用于应用内上传的标准技能 ZIP 不含 `install.py`。

实测范围：Codex CLI 使用 **0.5.0** 完成技能读取、模型修改与回读、模拟 Speak 和退出清理；浏览器连接通过 HTTP 检查，本轮未操作可视网页。当前下载版本为 0.5.1，未将旧版结果记为新版完整重测。

<a id="workbuddy"></a>

### WorkBuddy

1. **下载：**点击 [下载标准技能 ZIP · 0.5.1](https://github.com/Minkewu/micnow-lab/raw/refs/heads/main/downloads/micnow-lab-0.5.1.zip)，保留 `.zip` 文件，**不用解压**。
2. **安装：**在 WorkBuddy 打开 **专家·技能·连接器 → 技能 → 添加技能 → 上传技能**，选择下载的 `micnow-lab-0.5.1.zip`。导入完成后确认 `micnow-lab` 已启用。
3. **开始用：**新建工作任务，选用 `micnow-lab`，发送：

   > 使用 micnow-lab 打开本地 MicNow 实验室，读取当前设置，并打开同一会话的网页。

实测范围：WorkBuddy **5.9.3** 已用 0.5.0 完成完整功能流程；0.5.1 已通过原生 ZIP 安装、启动、读取设置、显示网页和模型关闭清理，新版配置修改与 Speak 尚未重测。

<a id="doubao"></a>

### 豆包工作

1. **下载：**点击 [下载标准技能 ZIP · 0.5.1](https://github.com/Minkewu/micnow-lab/raw/refs/heads/main/downloads/micnow-lab-0.5.1.zip)，**解压**，得到 `micnow-lab` 文件夹。
2. **安装：**在豆包工作打开 **插件·技能·伙伴 → 技能 → + 添加 → 上传技能**，选择完整的 **`micnow-lab` 文件夹**，导入后开启技能。文件夹中应包含 `SKILL.md`、`scripts`、`assets` 等内容，不能只上传 `SKILL.md`。
3. **开始用：**新建工作任务，选用 `micnow-lab`，发送：

   > 使用 micnow-lab 打开本地 MicNow 实验室，读取当前设置，并打开同一会话的网页。

实测范围：豆包工作 **2.35.12** 已用 **0.5.0** 完成文件夹导入、模型操作、真实网页双向修改、模拟 Speak 和退出清理；0.5.1 尚未完成同样的完整重测。这里适用于豆包工作客户端。

<a id="qwen"></a>

### 千问本地工作助理

1. **下载：**点击 [下载标准技能 ZIP · 0.5.1](https://github.com/Minkewu/micnow-lab/raw/refs/heads/main/downloads/micnow-lab-0.5.1.zip)，保留 `.zip` 文件，**不用解压**。
2. **安装：**在千问本机应用打开 **本地工作助理 → 技能 → 新建 → 上传 ZIP**，选择 `micnow-lab-0.5.1.zip`，等待校验完成并开启技能。
3. **开始用：**新建本地工作任务，选用 `micnow-lab`，发送：

   > 使用 micnow-lab 打开本地 MicNow 实验室，读取当前设置，并打开同一会话的网页。

实测范围：千问工作助理 **5.2.0.298** 已用 0.5.1 完成模型操作、真实网页双向设置和模拟 Speak；模型关闭及清理在另一次独立会话补测通过。两次结果分别记录。这里适用于国内千问本地工作助理；Qwen Code 的状态另列。

<a id="deepseek"></a>

### DeepSeek Harness

先安装并登录 [DeepSeek 官方 Harness](https://www.deepseek.com/en/harness/)，准备一个可用的本地项目。以下对应官方 Harness 的本机 Web 界面；普通 DeepSeek 网页聊天不适用。

1. **下载：**点击 [下载完整项目 ZIP](https://github.com/Minkewu/micnow-lab/archive/refs/heads/main.zip) 并解压。打开解压后的 `micnow-lab-main` 文件夹，里面应有 `install.py`。
2. **安装：**打开终端，输入 `cd` 和一个空格，把上述文件夹拖入终端，按回车；再复制执行：

   ```sh
   python3 install.py --agent deepseek-harness --install
   ```

3. **开始用：**重新打开 Harness 的本地项目，新建任务，发送：

   > 使用 micnow-lab 打开本地 MicNow 实验室，读取当前设置，并打开同一会话的网页。

实测范围：官方 npm 客户端 **0.2.2-rc.1 的 Web profile** 已用 0.5.1 完成同一会话中的模型／真实网页双向设置、模拟 Speak、模型关闭和独立清理核验。该预览版的项目选择按钮曾无响应，测试使用官方接口完成项目注册；处理经过见 [客户端实测记录](docs/client-validation.md)。原生桌面版尚未实测。

## 打开后怎么用、怎么结束

看到实验室网页后，可以继续在**同一个 Agent 任务**中发送：

> 把 Speak 改为按两次开始和结束，保留其他设置，完成后回读核验。

也可以在网页修改设置，再让 AI 检查：

> 读取当前设置，告诉我刚才在网页修改的设置是否已经生效。

AI 应实际执行命令、读取结果，并与网页操作同一个模拟设备。页面中的 Speak 是模拟演练，不会录音或向其他应用输入文字。

**用完后发送：**

> 关闭这次 MicNow 实验室，并确认后台服务已经停止。

只关闭浏览器标签页不会停止后台服务；需要让 Agent 完成关闭操作。

## 安装或使用遇到问题

- **找不到 `install.py`：**Codex 和 Harness 应下载完整项目 ZIP，并在含有该文件的目录执行安装命令。
- **找不到技能：**确认安装／导入成功且技能已启用，再新开会话；必要时重启客户端。上传时保留完整资源，不要只上传说明文件。
- **提示找不到 Python：**安装 Python 3.9+ 后重启终端和 Agent；可用 `python3 --version` 检查。Windows 可使用 `py -3` 或 `python`，但 Windows、Linux 的客户端运行仍待实测。
- **提示已有不同版本：**命令安装在原命令末尾加 `--update`，例如 `python3 install.py --agent codex --install --update`。安装器会备份旧版；应用内上传请使用该客户端的更新／重新导入入口，避免重复安装同名技能。
- **网页打不开：**让 Agent 确认实验室仍在运行，并使用这次启动返回的网址。Agent、服务和浏览器需能访问同一台电脑的 `127.0.0.1`；按客户端正常流程允许本机连接。

项目级安装、其他安装方式与平台限制见 [Agent 安装与兼容说明](docs/agents.md)。

<a id="compatibility"></a>

## 全部 Agent 的兼容状态

核对日期：**2026-11-13**。0.5.1 补充了限定诊断范围的指引，没有改变模拟行为或 0.4 协议。下表区分安装成功、功能操作与退出清理；未完成项保留待验证。

| 名称 | 当前提供的接入方式 | 验证边界 |
| --- | --- | --- |
| Codex | 标准 Skill + 安装器 | 0.5.0 真实 CLI 已完成发现、模型调用、读写与清理；本轮未操作可视网页，0.5.1 未完整重测 |
| Claude Code | 标准 Skill + 安装器 | 0.5.1 安装及 19 文件校验通过；技能发现和模型运行未验收，当前无可用账号 |
| WorkBuddy | 项目安装器或技能 ZIP | `5.9.3` 完成 0.5.0 完整功能测试；0.5.1 原生 ZIP 安装、最小生命周期与本次限定范围诊断通过，配置修改和 Speak 未重测 |
| Cursor | 标准 Skill + 安装器 | 0.5.1 安装及 19 文件校验通过；当前无可用测试账号，技能发现和模型运行未验收 |
| Gemini CLI | 标准 Skill、安装器或原生 GitHub 安装 | `0.68.0` 完成 0.5.1 安装、正常项目信任与技能发现；官方 Google 登录返回个人账号不再支持此客户端，模型运行未验收 |
| 千问 | 千问工作助理原生 ZIP 上传；Qwen Code Skill / 扩展 | 工作助理 `5.2.0.298` 完成 0.5.1 功能与真实网页测试；另一次独立生命周期补测完成模型关闭、托管任务退出和文件清理，不合并为单次完整流程。Code 计划限制另记 |
| Kimi | Kimi Work 原生 ZIP 上传；Kimi Code CLI Skill / 插件 | Work `3.2.27` 完成 0.5.1 模型/真实网页双向设置与模拟 Speak；外部工具清理通过，模型收尾未验收；CLI 发现通过 |
| DeepSeek | 官方 Harness + 安装器；Claude Code 替代路线未实测 | Harness `0.2.2-rc.1` 完成 0.5.1 真实模型与网页双向设置、模拟 Speak、模型关闭及独立清理核验；项目选择界面问题另记 |
| Perplexity | Computer / Personal Computer 专用根目录 ZIP | `26.44.0`（build `163`）安装、登录、0.5.1 ZIP 上传及宿主界面发现通过；本次账号发送任务时提示升级，模型读取与运行未验收 |
| 豆包 | 豆包工作个人自定义技能上传 | `2.35.12` 完成 0.5.0 文件夹导入、模型调用、真实网页双向修改、模拟 Speak 与清理 |

详细步骤、官方来源及每个平台的运行限制见 **[Agent 安装与兼容说明](docs/agents.md)**，本轮版本和证据范围见 **[客户端实测记录](docs/client-validation.md)**。格式适配不等于已经在十个客户端逐一验收，也不表示获得官方市场认证。

## 下载与文件校验

- [完整项目 ZIP](https://github.com/Minkewu/micnow-lab/archive/refs/heads/main.zip)：含 `install.py`，用于上文 Codex、DeepSeek Harness 的命令安装。
- [标准技能 ZIP](https://github.com/Minkewu/micnow-lab/raw/refs/heads/main/downloads/micnow-lab-0.5.1.zip)：外层是 `micnow-lab/`，用于 WorkBuddy、千问上传，或解压后供豆包工作导入文件夹。
- [Perplexity 技能 ZIP](https://github.com/Minkewu/micnow-lab/raw/refs/heads/main/downloads/micnow-lab-perplexity-0.5.1.zip)：`SKILL.md` 直接位于 ZIP 根目录。
- [技能包校验值](downloads/SHA256SUMS.txt)。标准技能包和 Perplexity 包包含同一份 Skill 和程序，仅 ZIP 层级不同；Perplexity 的模型运行仍待验证。

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
