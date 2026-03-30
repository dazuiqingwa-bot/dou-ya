# 模型管理面板说明

## 位置
- 面板页面：`canvas/index.html`
- 数据文件：`canvas/model-panel-data.json`
- 刷新脚本：`scripts/model_panel_refresh.py`

## 当前已实现（V0.1）

### 1) 核心状态监控
- 当前默认模型
- 当前会话模型（最近一次快照）
- 可用模型列表
- 回退链
- OAuth / token 健康状态
- 本地模型运行时检测（Ollama）
- Mac mini 本地部署预留位

### 2) KPI 监控
当前先展示“最近一次快照”的会话级指标：
- 输入 Token
- 输出 Token
- 上下文占用
- 剩余额度

> 说明：真正跨会话/跨天/跨模型的 KPI，需要后续增加采集器，把 session_status 和 provider usage headers 持续写入数据仓。

### 3) 刷新策略建议
- **默认建议：15 秒轮询，仅在盯盘时开启**
- 日常使用：手动刷新
- 不建议“实时秒刷”：成本高、噪音大、实际价值低

## 当前未完全打通的部分

### A. 浏览器内真正一键切换模型
现在的页面先展示“安全可复制命令”：
- `openclaw models set openai-codex/gpt-5.4`
- `openclaw models set claude`
- `openclaw models set ollama/gpt-oss:20b`

原因：纯静态 Canvas 页面本身不能直接执行本地 CLI。要做真一键，需要增加一个**本地操作桥**（例如本机小型 HTTP bridge），让页面按钮调用桥，再由桥执行白名单命令。

### B. 面板内直接安装/更新本地模型
同理，现在先给命令位：
- `ollama pull gpt-oss:20b`
- `ollama pull qwen2.5-coder:32b`
- `ollama pull deepseek-r1:32b`

要做真正按钮化安装/更新，也需要同一个本地操作桥。

## 我建议的下一步（V0.2 / V0.3）

### V0.2：真操作版
增加本地操作桥，只开放这些白名单动作：
- `openclaw models set <allowed model>`
- `openclaw models auth login --provider <allowed provider>`
- `ollama pull <approved model>`
- `ollama list`

### V0.3：生产级版
- 会话历史 KPI 趋势图（1h / 24h / 7d）
- 模型评测分区：候选 / 已批准 / 生产默认
- 三层模型路由视图：决策层 / 问题解决层 / 执行层
- 成本监测与告警阈值
- 本地 GPU / 内存 / 上下文利用率监控（Mac mini 到货后）

## 使用方法

### 手动刷新数据
```bash
python3 /Users/gaojames/.openclaw/workspace/scripts/model_panel_refresh.py
```

### 打开面板
如果通过 OpenClaw Canvas：
- 网关 URL：`http://127.0.0.1:18789/__openclaw__/canvas/`

或者直接用浏览器打开本地文件：
- `/Users/gaojames/.openclaw/workspace/canvas/index.html`

## 原则
这个面板的目标不是“展示得花”，而是三件事：
1. 一眼看清当前能不能用
2. 一步切到正确模型
3. 为 Mac mini 本地部署提前留好口子
