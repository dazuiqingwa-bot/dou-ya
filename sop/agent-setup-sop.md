# Agent 搭建 SOP
_基于禾禾/豆芽系统经验提炼 · 2026-03-29_

适用场景：为家庭成员搭建专属 AI 伙伴 + 可选的后台系统（如学习中心、记录系统）。
下次搭苗苗时直接照此执行，遇到新坑在文档末尾补记。

---

## 一、整体结构

```
家庭成员
    ↓ 飞书/Telegram/其他渠道
前台 Agent（豆芽/苗苗的 Agent）
    ↓ sessions_send（单向通知，不等回复）
后台系统 Agent（Learning Center / 记录系统）
    ↓ exec 调脚本
外部存储（Notion / Obsidian）
```

**关键原则：前台 Agent 只负责陪伴和交互，后台系统负责数据处理。两者之间单向通知，不同步等待。**

---

## 二、搭建顺序

### Step 1：创建 Agent 目录结构

```bash
# workspace 下创建 agent 目录
mkdir -p ~/.openclaw/workspace/agents/<agent-name>

# 必须有这几个文件
SOUL.md        # 人设、行为规则、路由逻辑
IDENTITY.md    # 名字、emoji、自我介绍
USER.md        # 服务对象画像
AGENTS.md      # 工作区说明（可复制标准模板）
TOOLS.md       # 工具备注（可留空）
HEARTBEAT.md   # 心跳任务（可留空或写 HEARTBEAT_OK）
```

### Step 2：在 openclaw.json 里注册 Agent

```json
"agents": {
  "entries": [
    {
      "id": "<agent-name>",
      "name": "<agent-name>",
      "workspace": "/Users/dazuiqingwa/.openclaw/workspace/agents/<agent-name>",
      "agentDir": "/Users/dazuiqingwa/.openclaw/agents/<agent-name>/agent",
      "identity": {
        "name": "显示名",
        "emoji": "🌱"
      },
      "model": {
        "primary": "openai-codex/gpt-5.4",
        "fallbacks": ["zhipu-cn/glm-4-plus"]
      }
    }
  ]
}
```

⚠️ **坑：agentDir 必须写绝对路径，不能用 ~**

### Step 3：绑定渠道

在 openclaw.json 的 `plugins.entries` 里添加路由规则，将渠道消息路由给对应 agent：

```json
{
  "agentId": "<agent-name>",
  "match": {
    "channel": "feishu",
    "accountId": "default"
  }
}
```

⚠️ **坑：飞书每个用户有唯一 open_id，路由规则要精确到 open_id，否则所有飞书消息都会走这个 agent**

### Step 4：配置语音转写（STT）

OpenClaw 的 OpenAI STT provider 有 bug（未注册到内置 PROVIDERS 数组），必须用 CLI 脚本模式绕过：

```json
"tools.media.audio": {
  "enabled": true,
  "echoTranscript": true,
  "models": [{
    "type": "cli",
    "command": "/Users/dazuiqingwa/.openclaw/workspace/scripts/transcribe.sh",
    "args": ["{{MediaPath}}"],
    "timeoutSeconds": 30
  }]
}
```

`transcribe.sh` 已存在，直接复用，无需重新创建。

⚠️ **坑：不要用 `models: [{provider: "openai"}]` 的写法，会被静默跳过，转写永远不触发**

### Step 5：配置外部存储

**如果用 Obsidian（苗苗的情况）：**
- 确认库路径：`/Users/dazuiqingwa/Library/Mobile Documents/com~apple~CloudDocs/笔记/<库名>`
- 直接用 `write` 工具写 `.md` 文件即可，不需要额外 API

**如果用 Notion（禾禾的情况）：**
- API key 路径：`~/.config/notion/api_key`
- 数据库 ID 必须从浏览器 URL 复制，格式为 32 位无连字符字符串
  - ✅ 正确：`329d76be33b0804e9db3d9ee9fde3429`
  - ❌ 错误：`329d76be-33b0-80a0-a0b3-000bb66105a7`（带连字符的是错的）
- 数据库必须在 Notion 里手动共享给对应 integration（连接 → 添加 integration）
- 写入前先用 API 查询数据库字段列表，字段名必须完全匹配

### Step 6：写 SOUL.md

重点：
1. **前台 Agent 的图片/语音路由规则必须加"不等待"约束**
   - 调用 `sessions_send` 通知后台系统后，立刻回复用户，不等后台处理完
   - 否则用户会感受到 10-40 秒的沉默等待
2. **图片触发规则要区分"题目图片"和"其他图片"**
   - 只有学科题目图片才路由给学习系统
   - 日记、海报、聊天截图等不应触发入库流程
3. **规则优先级要写在文件最顶部**
   - 写在第七节的规则容易被 session 历史压缩降权，执行不稳定
   - 最关键的约束放在 `## ⚠️ 零号规则` 这种形式，置于文件开头

### Step 7：重启并验证

```bash
openclaw gateway restart
```

验证顺序：
1. 发一条纯文字 → 确认 Agent 能正常回复
2. 发一段语音 → 确认转写触发（豆芽会先复述语音内容）
3. 发一张题目图片 → 确认路由给后台系统 + 存储写入
4. 发一张非题目图片 → 确认不触发入库

---

## 三、SOUL.md 写作要点

### 必须包含的模块
- 身份定位（是谁、服务谁、不是谁）
- 核心角色（几种工作模式）
- 路由规则（什么消息走什么流程）
- 边界（什么事不做、不说）

### 图片路由规则模板

```markdown
## ⚠️ 零号规则：收到图片，必须先判断再路由

收到图片时：
1. 先判断图片类型：
   - 学科题目（有题干、选项、公式）→ 走学习路由
   - 其他（日记、截图、海报、照片）→ 直接回复，不路由
2. 如果是题目：第一步调用 sessions_send 通知后台系统
3. 调用后立刻回复用户，不等待后台返回结果
4. 禁止在调用之前输出任何分析内容
```

### 后台系统路由规则

后台系统（Learning Center 等）处理完成后：
- **只向外部存储写入数据**
- **只通过 sessions_send 向前台 Agent 的用户渠道推送练习题**
- **不把处理结论发回给前台 Agent 的 session**（会污染对话流）

---

## 四、已知坑清单

| 坑 | 现象 | 解法 |
|----|------|------|
| Session 历史惯性 | SOUL.md 规则改了但执行不变 | `/reset` 清空 session 历史，新规则立刻生效 |
| OpenAI STT 不触发 | 发语音没有转写，也没有报错 | 改用 CLI 脚本模式，见 Step 4 |
| Notion 404 | 写入报错 object_not_found | 1) 检查数据库 ID 格式（无连字符）2) 检查 integration 是否已共享给数据库 |
| Notion 字段不存在 | 写入报错 validation_error | 先查询数据库字段列表，字段名必须完全一致 |
| LC 回复污染豆芽 session | 豆芽回了奇怪的内容 | LC 处理完不要 sessions_send 回前台 session，只推送给用户渠道 |
| GLM-5-Turbo 空输出 | 模型调用成功但正文为空 | 改用 GLM-4-Plus，GLM-5-Turbo 的推理模式有 bug，正文不输出 |
| 图片响应很慢 | 发图片后 20 秒才回复 | 国内访问 OpenAI/Anthropic 固有延迟，前台 Agent 异步通知后台可缓解体感 |

---

## 五、苗苗系统与禾禾系统的差异

| 项目 | 禾禾（豆芽）| 苗苗 |
|------|------------|------|
| 存储 | Notion 错题库 | Obsidian（直接写 .md 文件）|
| 后台系统 | Learning Center | 待定（可能不需要独立后台 agent）|
| 主要场景 | 学科辅导 + 陪伴 | 待定 |
| 渠道 | 飞书 | 待定 |

**Obsidian 写入方式（无需 API）：**
```python
# 直接写文件到 Obsidian 库路径
vault_path = "/Users/dazuiqingwa/Library/Mobile Documents/com~apple~CloudDocs/笔记/苗苗库"
# 用 write 工具写 .md 文件即可，iCloud 自动同步
```

---

## 六、复用的脚本和配置

| 文件 | 用途 | 能否复用 |
|------|------|---------|
| `scripts/transcribe.sh` | 飞书/Telegram 语音转写 | ✅ 直接复用 |
| `scripts/notion-insert.py` | Notion 写入 | ⚠️ 改 DB_ID 和字段 |
| `scripts/notion-update-status.py` | Notion 状态更新 | ⚠️ 改 DB_ID |
| `agents/douya/SOUL.md` | 前台 Agent 人设模板 | ⚠️ 大幅改写，但结构可参考 |
| `agents/learning-center/SOUL.md` | 后台系统模板 | ⚠️ 参考结构 |

---

_下次踩到新坑，在「四、已知坑清单」里补记。_
