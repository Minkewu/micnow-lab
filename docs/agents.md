# 在不同 Agent 中安装 MicNow Lab

文档核对日期：2026-11-13。当前版本：0.5.1。

仓库地址：<https://github.com/Minkewu/micnow-lab>。

MicNow Lab 是不需要硬件的本地模拟设备实验室。一个标准 `SKILL.md` 配合随包的 Python 脚本和网页资源，可以由不同本地 Agent 使用；它不会录音、控制真实麦克风或向外部应用输入文字。

本仓库仅授权查看、下载、安装和运行，**未采用开放源码许可证**；其他权利与素材说明见 [使用范围](../USAGE.md) 和 [素材来源](../ASSET-SOURCES.md)。平台名称仅用于说明安装位置，不代表平台背书或市场审核通过。

## 安装前

需要 Python 3.9 或以上、本机命令执行能力、可保持运行的后台进程，以及能与该进程访问同一 `127.0.0.1` 的浏览器。Agent 自身必须已登录或配置可用模型；这与 Skill 安装是两个步骤。安装 Skill 不会自动安装 Python，也不会授予执行权限。脚本调用结果会进入当前 AI 对话。

以下安装命令在仓库根目录执行。可以下载 GitHub 仓库 ZIP 并解压，或使用：

```sh
git clone https://github.com/Minkewu/micnow-lab.git
cd micnow-lab
python3 --version
```

Windows 若使用 Python Launcher，将下文 `python3` 换成 `py -3`。命令中的项目路径要换成已存在的实际目录。

`install.py` 默认只显示安装预览；加 `--install` 才复制文件。更新已有的不同版本时，先检查预览，再加 `--install --update`，安装器会备份旧版本。不要同时使用目录安装和同平台扩展安装，以免出现两个同名技能。

当前 macOS 本地通信链路已有验证；**格式符合文档、文件复制成功、ZIP 导入成功，都不等于每个客户端完成端到端实测**。具体版本、已观察行为和阻塞点见 [客户端实测记录](client-validation.md)。Windows 和未实际运行的客户端仍需完成文末的验收。远程 SSH、容器、云电脑与网页聊天中的 localhost 也不自动指向用户电脑。

## 1. Codex

面向本机 Codex 桌面／CLI 会话。用户级安装：

```sh
python3 install.py --agent codex
python3 install.py --agent codex --install
```

安装位置为 `~/.agents/skills/micnow-lab/`。仅供某个项目使用时：

```sh
python3 install.py --agent codex --project "/path/to/project" --install
```

项目位置为 `.agents/skills/micnow-lab/`。新会话中请求“使用 micnow-lab 打开本地实验室”。目录被发现后，仍须按 Codex 的权限流程允许本机服务与通信；这不是 OpenAI 公共插件目录上架。

官方来源：[Codex 本地技能目录与安装](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。

## 2. Claude Code

这里的目标是本机 **Claude Code**，不是普通 Claude 网页聊天。

```sh
python3 install.py --agent claude-code
python3 install.py --agent claude-code --install
```

安装到 `~/.claude/skills/micnow-lab/`；添加 `--project "/path/to/project"` 可安装到项目 `.claude/skills/`。使用 `/micnow-lab` 或直接描述任务。

标准技能格式可直接复用。Claude Code 的执行隔离可能影响本地通信：macOS 上本地监听可能受限；Linux／WSL2 沙箱中的 localhost 可能属于单条命令的私有网络。受限时按客户端的正常授权流程处理，不自动关闭安全设置或改为公网监听。本轮在独立测试项目中通过安装器的正常更新流程备份旧版、安装 0.5.1，19 个文件与发布源一致；客户端技能发现和模型运行尚未验收，当前无可用账号继续测试。

官方来源：[技能目录](https://code.claude.com/docs/en/skills#choose-where-skills-load)、[本地服务访问限制](https://code.claude.com/docs/en/sandboxing#a-command-fails-to-reach-a-server-on-localhost)。

## 3. WorkBuddy

推荐从 [下载目录](https://github.com/Minkewu/micnow-lab/tree/main/downloads) 下载 `micnow-lab-0.5.1.zip`，在 WorkBuddy 打开“专家·技能·连接器 → 技能 → 添加技能 → 上传技能”，选择 ZIP。

也可安装到一个已存在的项目：

```sh
python3 install.py --agent workbuddy --project "/path/to/project"
python3 install.py --agent workbuddy --project "/path/to/project" --install
```

位置为项目 `.codebuddy/skills/micnow-lab/`。安装器不猜测 WorkBuddy 用户级目录。官方文档中的对话安装适用于技能市场，不应把粘贴任意 GitHub URL 描述为已确认入口。

WorkBuddy 支持脚本执行，仍可能要求工作区信任或命令授权。本轮 `5.9.3` 使用 0.5.0 技能及 Python `3.13.12` 完成模型操作、真实浏览器双向设置、模拟 Speak 与退出清理。该次诊断范围风险及 0.5.1 指引补强、后续限定范围补测单独记录在 [客户端实测记录](client-validation.md)。这里是自行导入，不代表 WorkBuddy 市场审核通过。

随后通过客户端原生上传入口导入公开的 0.5.1 标准 ZIP，安装后的 19 个技能文件与发布源逐项一致。新版以 Hy4 模型、Python `3.13.12` 和 PTY 完成独立最小生命周期：启动、只读查询默认状态、观察真实嵌入网页，再由模型调用随包 `shutdown`；服务、模拟器、端口、连接文件及运行目录清理另经独立检查确认。本次诊断限定在已知进程、端口和文件存在性，未放宽宿主权限。该结果只覆盖这次最小生命周期与限定范围诊断，不包含新版配置修改或 Speak 重测，也不替代其他模型行为验收。

官方来源：[技能上传](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)、[项目目录](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Project)、[执行权限](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes)。

## 4. Cursor

```sh
python3 install.py --agent cursor
python3 install.py --agent cursor --install
```

使用 `~/.agents/skills/micnow-lab/`；加 `--project "/path/to/project"` 改为项目 `.agents/skills/`。Cursor 也支持 `.cursor/skills/`。在本机 Agent 中通过 `/` 查找技能或直接提出任务。

官方确认支持随技能执行 Python 等脚本，但实际命令权限由客户端决定。此安装路径不自动同步到 Cloud Agents；云端运行也不等于本机运行。本轮 0.5.1 的 19 个安装文件与发布源一致；当前没有可用测试账号，客户端未登录，技能发现和端到端运行尚未验收。

官方来源：[Cursor Agent Skills](https://cursor.com/docs/skills)。

## 5. Gemini CLI

可使用仓库安装器：

```sh
python3 install.py --agent gemini
python3 install.py --agent gemini --install
```

使用 `~/.agents/skills/micnow-lab/`。Gemini CLI 也接受 `.gemini/skills/`，并提供直接从 GitHub 安装的入口，可选其一：

```sh
gemini skills install https://github.com/Minkewu/micnow-lab.git --path skills/micnow-lab
```

先在目标项目交互启动 Gemini，审阅项目内容并按界面选择信任该项目；0.68.0 的信任管理入口为 `/permissions trust`。通过 `/skills list` 检查发现情况；新安装后可 `/skills reload`。未受信任的项目会跳过项目技能。不要把全局跳过信任检查作为安装步骤。技能激活及命令执行遵守 Gemini CLI 的确认流程，容器或隔离网络可能影响本机端口。

本轮 `0.68.0` 在独立项目安装 0.5.1，19 个文件与发布源一致；通过正常交互选择 **Trust folder** 后，客户端重启并持久保存当前项目的信任，原生技能列表显示 `micnow-lab [Enabled]`，未使用信任绕过选项。随后选择官方 Google 登录，服务返回此客户端已不再支持 Gemini Code Assist 个人账号、提示迁移至 Antigravity。该次没有模型或工具调用，实验室未启动；模型运行仍未验收。本轮验证的是项目安装器路径，未验证原生 GitHub URL 安装。

官方来源：[技能安装](https://geminicli.com/docs/cli/skills/)、[发现与工作区信任](https://geminicli.com/docs/cli/tutorials/skills-getting-started/)、[执行环境](https://geminicli.com/docs/cli/sandbox/)。

## 6. 豆包

目标是**豆包工作客户端**。2026-11-11 更新的官方帮助明确支持个人自定义技能上传：

1. 下载并解压标准技能 ZIP，保留整个 `micnow-lab/` 文件夹。
2. 在客户端进入“插件·技能·伙伴 → 技能 → + 添加 → 上传技能”。
3. 选择包含 `SKILL.md` 的完整 `micnow-lab/` 文件夹，保留全部 19 个文件；导入后开启技能，不要只上传说明文件。
4. 在工作任务中选用该技能，请模型打开 MicNow 实验室、执行修改并回读。浏览器修改后，再请同一任务中的模型读取新设置；结束时执行 `shutdown`。

本轮在 macOS 豆包工作 `2.35.12` 使用 0.5.0 技能实际完成个人文件夹上传、开启与模型调用。模型使用 Python `3.14.7` 和本机 PTY 启动实验室；真实浏览器与模型在同一设备会话中交替修改设置、回读一致，模拟 Speak 与退出清理均通过。安装的 19 个文件与当时发布源一致，详见 [客户端实测记录](client-validation.md)。

官方个人上传说明支持文件或文件夹；本轮验证的是完整文件夹，不承诺个人入口支持哪一种 ZIP 层级，也不猜测固定技能目录或 GitHub 直接安装命令。结果限于上述本机客户端，不能推广到普通豆包网页聊天或其他系统。

开放平台的企业专属或公开上架属于另外的审核流程，本次 GitHub 安装不需要代替用户提交该流程。该开放平台要求根目录 `SKILL.md` 的 ZIP，与本节的个人文件夹上传应分开处理。

官方来源：[豆包工作使用技能](https://www.doubao.com/work/docs/zh-cn/articles/081010973544-skills)、[开发者技能接入指南](https://open.doubao.com/document/doubao-developer-guide/skill-integration-guide)。

## 7. 千问：本地工作助理与 Qwen Code

国内千问本机应用使用原生入口安装：

1. 进入“本地工作助理 → 技能 → 新建 → 上传 ZIP”。
2. 选择标准 `micnow-lab-0.5.1.zip`，等待客户端校验完成并开启技能。
3. 在本地工作任务中请求模型读取技能、打开 MicNow 实验室，按宿主正常权限流程允许本机运行。

本轮千问工作助理 `5.2.0.298` 的上传校验、开启、模型发现和读取均已通过，导入的 19 个文件与 0.5.1 包一致。模型使用 Python `3.9.6` 启动实验室，首次本机通信受限后经正常授权恢复，实际使用进程管道回退；模型与真实网页双向设置、保留其他配置及模拟 Speak 均通过。该次关闭请求在桌面锁屏期间停于单次审批，旧服务由外部工具正常终止，独立确认服务和模拟器退出、端口关闭；旧连接文件删除未取得独立证据。

解锁后拒绝过期审批、停止旧任务，再以新设备会话单独补测生命周期。经正常单次命令授权，模型执行随包 `shutdown`，托管任务正常退出，模型实际检查连接文件和运行目录均不存在。补测没有重做网页配置与 Speak；两次测试分别记录，不能拼成单次完整端到端流程。补测的独立端口检查与具体进程核验边界见 [客户端实测记录](client-validation.md)。这个原生应用入口不使用下面的 Qwen Code 登录流程，也不能推广到普通网页聊天。

另提供 **Qwen Code** 本地 CLI 的目录安装：

```sh
python3 install.py --agent qwen-code
python3 install.py --agent qwen-code --install
```

使用 `~/.agents/skills/micnow-lab/`；Qwen Code 同时支持 `.qwen/skills/`。本仓库另提供 `qwen-extension.json`，可改用扩展安装：

```sh
qwen extensions install https://github.com/Minkewu/micnow-lab
```

若客户端的 GitHub 安装流程选择了不含扩展清单的 Release 附件，在已下载的完整仓库根目录改用 `qwen extensions install .`。通用技能 ZIP 不是扩展 ZIP；扩展安装需要根目录的 `qwen-extension.json`。

扩展安装后的技能名称带前缀，可在 `/skills` 查看并使用 `/micnow-lab:micnow-lab`。Qwen Code 的 Shell 工具支持受管理后台进程；Agent 应保持实验室服务运行，并在结束时清理。容器或关闭的网络模式仍可能隔离 localhost。本轮项目发现及本地路径扩展安装已实测；GitHub／ZIP 原生安装入口和模型运行尚未实测。

拥有千问聊天账号不等于已具备 Qwen Code 可用模型。在交互客户端的 `/auth` 中选择适合已有账户的认证方式；当前 “Qwen Account with Subscription” 入口需要 `chat.qwen.ai` 的有效 Plus 或 Pro 订阅。安装 Skill 不会创建订阅或配置 API 密钥。

官方来源：[技能目录](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/)、[扩展清单与安装](https://qwenlm.github.io/qwen-code-docs/en/users/extension/introduction/)、[后台执行](https://qwenlm.github.io/qwen-code-docs/en/developers/tools/shell/)、[账户与模型认证](https://qwenlm.github.io/qwen-code-docs/en/users/configuration/auth/)。

## 8. DeepSeek：官方 Harness 与其他宿主

优先使用 [DeepSeek 官方 Harness](https://www.deepseek.com/en/harness/)。安装 Harness 后，通过仓库安装器放入同一份标准 Skill：

```sh
python3 install.py --agent deepseek-harness
python3 install.py --agent deepseek-harness --install
```

用户级技能默认安装到 `~/.dsh/skills/micnow-lab/`；如果已经设置 `DSH_HOME`，安装器使用该目录下的 `skills/micnow-lab/`。项目级安装加 `--project "/path/to/project"`，使用项目 `.dsh/skills/micnow-lab/`，不受 `DSH_HOME` 影响。Harness 将最近的 `.git` 所在目录作为项目根；请在目标项目根安装并启动。目录依据见 [官方技能发现说明](https://deepseek-harness.github.io/deepseek-harness/en/reference/subsystems/skills.md) 与 [配置目录](https://deepseek-harness.github.io/deepseek-harness/en/reference/config-catalog.md)。

本轮官方 npm 客户端 `0.2.2-rc.1` 使用 Node.js `24.22.3` 在独立目录安装，0.5.1 的 19 个技能文件与发布源一致。正常账号登录后，在 Web profile 中使用 DeepSeek-V4.1-Flash、High 推理设置；真实模型通过 `load_skill` 读取技能，以 Python `3.9.6` 的进程管道回退启动并保留后台任务。模型与真实浏览器在同一设备会话中完成双向配置、偏好保留、模拟 Speak 和随包 `shutdown`，关闭与清理另经独立核验，完整本机功能流程通过。

该预览版本的 Web 原生目录选择按钮在本轮没有响应，测试改用官方 `workspace/create` 接口注册独立项目，再继续正常 Web 界面操作；不将此记录为纯界面一键完成项目注册。首次定位已知服务的子进程时，经正常单次授权批准限定范围的进程查询；保留默认 `workspace-write` 安全设置。具体步骤与边界见 [客户端实测记录](client-validation.md)。

另保留 **DeepSeek 模型 + Claude Code 等本地宿主** 的替代路线。已按 DeepSeek 官方指南配置好 Claude Code 时，可安装同一份技能：

```sh
python3 install.py --agent claude-code
python3 install.py --agent claude-code --install
```

随后在该 Claude Code 会话调用 `/micnow-lab`。该路线的目录与执行权限由 Claude Code 决定；安装器不切换模型、不设置 API 密钥。已有其他宿主时，按该宿主的技能安装文档操作。

DeepSeek 官方明确：模型返回工具调用，具体函数由调用方执行。因此不能把“DeepSeek 支持 Tool Calls”当作 DeepSeek 网页聊天已支持本机脚本。本轮通过的是上述 Harness Web profile 的本机流程；DeepSeek 模型接入 Claude Code 的替代路线仍未实测。

官方来源：[Harness 代码仓库](https://github.com/deepseek-ai/deepseek-harness)、[DeepSeek 接入 Claude Code](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/)、[Tool Calls 执行责任](https://api-docs.deepseek.com/guides/tool_calls/)。

## 9. Kimi：Kimi Work 与 Kimi Code CLI

Kimi Work 本机应用使用原生入口安装：

1. 登录本机 Kimi Work，从个人技能上传入口选择标准 `micnow-lab-0.5.1.zip`。
2. 导入后在工作任务中选用技能，请模型打开 MicNow 实验室。
3. 在同一任务中核验网页修改；结束时让模型执行随包 `shutdown`。

本轮 Kimi Work `3.2.27`（build `3.2.27.25`）已通过上传、发现和真实模型读取；导入的 19 个文件与 0.5.1 包一致。模型与真实网页的双向设置、其他配置保留及模拟 Speak 均通过。两次模型关闭请求均受服务高峰阻断，随后由外部工具调用同一随包客户端完成关闭，进程、端口及连接文件清理经独立核验通过。后来单独重试最小生命周期仍遇服务高峰，未执行；模型自行收尾尚未验收。这个原生应用入口不需要另外登录 Kimi Code CLI。

另提供新版 **Kimi Code CLI** 的目录安装；普通 Kimi 网页聊天也是另一套运行环境：

```sh
python3 install.py --agent kimi-cli
python3 install.py --agent kimi-cli --install
```

使用 `~/.agents/skills/micnow-lab/`。新版也支持 `.kimi-code/skills/` 与用户的 `$KIMI_CODE_HOME/skills/`（默认 `~/.kimi-code/skills/`）；旧版 `.kimi/skills/` 不作为当前唯一入口。

本仓库有 `kimi.plugin.json`，也可在 Kimi 会话中使用插件方式安装：

```text
/plugins install https://github.com/Minkewu/micnow-lab
/reload
/skill:micnow-lab:micnow-lab
```

可用 `/plugins list` 检查插件；若界面显示不同插件 ID，以实际列出的限定技能名为准。Kimi 的 Bash 支持后台执行，但默认后台任务超时为 10 分钟，应按工具选项管理实验室生命周期。CLI 自身不保证 Python 已安装。本轮项目发现及本地路径插件安装已实测；GitHub／ZIP 原生安装入口和模型运行尚未实测。

官方来源：[技能目录](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html)、[插件安装](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html)、[工具与后台任务](https://www.kimi.com/code/docs/en/kimi-code-cli/reference/tools.html)、[版本迁移](https://www.kimi.com/code/docs/en/kimi-code-cli/guides/migration.html)。

Kimi Work 与上述隔离 CLI 的模型配置分别记录，不能由 CLI 未配置模型推断 Kimi Work 不可用。

## 10. Perplexity

目标是 **Perplexity Computer / Personal Computer**，不是普通搜索聊天。请下载 [下载目录](https://github.com/Minkewu/micnow-lab/tree/main/downloads) 中的 `micnow-lab-perplexity-0.5.1.zip`。

1. 在本轮实测的 macOS 客户端进入 **Computer 模式 → 输入框更多选项 → 浏览插件 → 添加自定义项 → 技能 → 上传技能**。
2. 选择 `micnow-lab-perplexity-0.5.1.zip`，等待上传成功；在已安装技能列表确认 `micnow-lab` 已开启。
3. 打开详情检查完整资源树，点击“使用技能”，再填写实际任务。模型执行仍取决于当前账号计划和任务的本机执行环境。

这个专用 ZIP 将 `SKILL.md` 放在 ZIP 根，保留 `scripts/`、`references/` 和 `assets/`；不要用仅有文字的 `.md` 替代完整包。官方单技能限额为 20 MB、100 文件。本仓库当前不提供 Perplexity 的 GitHub 插件导入入口，因为这需要另外的插件清单。

网页 Computer 运行在云端；Personal Computer 才涉及本机文件与应用。本机服务、持续进程和 localhost 仍需实测；仅上传成功不能保证实验室能在用户浏览器打开。不猜测 Perplexity 的内部技能目录。

本轮 macOS 官方 `26.44.0`（build `163`）通过 Finder 正常安装并登录，安装件与 DMG 文件一致，严格签名及公证检查通过。公开下载的 0.5.1 专用 ZIP 上传成功，已安装技能列表显示 `micnow-lab` 已启用；详情文件树展示 19 个资源及新版诊断规则。上传前 ZIP 哈希与完整资源树已核验，但未逐字节回读客户端存储，因此只记为安装、上传及宿主界面发现通过。

点击“使用技能”后填写本机任务，发送时本次账号出现 **Upgrade to Pro** 提示，任务仍停留在输入框，没有模型读取或实验室启动，也未购买升级。该限制只描述本轮账号和入口，不推断所有 Perplexity 用户的计划要求；模型运行仍待验收。

官方来源：[技能 ZIP 格式与导入](https://www.perplexity.ai/help-center/en/articles/13914413-how-to-use-computer-skills)、[本机与云端区别](https://www.perplexity.ai/help-center/en/articles/14659663-what-is-personal-computer)。

## 每个客户端的验收方法

请在目标客户端实际完成以下流程，再把对应环境标为“已验证”：

1. 客户端能发现并读取 `micnow-lab`，可访问随包脚本与网页资源。
2. Agent 用可用的 Python 3.9+ 启动服务，读取真实输出的 URL；浏览器能打开同一服务。
3. CLI 读取状态成功；Web 中修改一项设置后，Agent 能回读该值，证明两端使用同一会话。
4. 用户明确要求时，执行一项模拟设置并回读核验；模拟 Speak 后确认状态已结束。
5. 结束体验时关闭服务，确认服务及其子进程退出；不把凭证内容粘贴进聊天。

记录客户端版本、系统版本、Python 版本、安装方式和失败位置。仅列出技能、尚未实际执行时，应写“发现已验证”；完成以上步骤才写“本机运行已验证”。异常时保留错误事实，不通过新会话、改公网监听或放宽安全设置掩盖失败。
