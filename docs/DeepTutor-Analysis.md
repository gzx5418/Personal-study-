# HKUDS/DeepTutor 深度分析报告

> 分析日期：2026-05-07
> 仓库地址：https://github.com/HKUDS/DeepTutor
> 开源协议：Apache-2.0
> Stars：20,000+
> 开发团队：香港大学数据智能实验室（HKUDS）

---

## 一、项目概述

### 1.1 DeepTutor 是什么？

DeepTutor 是一个 **Agent 原生智能个性化辅导平台**。它不是简单的对话机器人，而是融合了多 Agent 协作、检索增强生成（RAG）、持久化记忆、知识管理于一体的全方位 AI 学习伴侣。

### 1.2 解决的核心问题

| 问题 | 现状 | DeepTutor 的解法 |
|------|------|------------------|
| AI 辅导缺乏长期跟踪 | 一问一答，无记忆 | 双文件记忆系统（PROFILE + SUMMARY） |
| 学习资料散落各处 | PDF/论文/笔记分散 | RAG 知识库，统一索引检索 |
| 缺少自动化学习材料生成 | 手动出题、做笔记 | 自动生成测验、概念图、动画 |
| 缺乏多模态支持 | 纯文字对话 | Manim 动画、SVG 图表、交互式可视化 |
| 辅导工具被动响应 | 等用户提问 | TutorBot 主动提醒、复习建议 |

### 1.3 项目规模

- 代码量：约 **20 万行**
- 后端 Python 包核心模块：15+
- 前端 Next.js 页面/组件：50+
- 支持 LLM 提供商：30+
- 支持消息渠道：10+
- 最新版本：v1.3.6，发布频率极高（几乎每天都有新版本）

---

## 二、项目架构

### 2.1 顶层目录结构

```
HKUDS/DeepTutor/
├── deeptutor/                # 核心 Python 包（后端逻辑）
│   ├── core/                 # 核心抽象层：协议、流、上下文
│   ├── runtime/              # 运行时：编排器、注册表、引导启动
│   ├── agents/               # 各类 Agent 实现
│   ├── capabilities/         # 能力层（Level 2 插件）
│   ├── tools/                # 工具层（Level 1 插件）
│   ├── services/             # 服务层：LLM、Embedding、RAG、Memory、Session
│   ├── api/                  # FastAPI 后端 + WebSocket 路由
│   ├── book/                 # Book Engine（交互式"活书"编译器）
│   ├── co_writer/            # AI 协作写作模块
│   ├── tutorbot/             # TutorBot 自主辅导 Agent 引擎
│   ├── knowledge/            # 知识库管理
│   ├── config/               # 配置系统
│   ├── events/               # 异步事件总线
│   ├── logging/              # 日志系统
│   └── utils/                # 工具函数
├── deeptutor_cli/            # CLI 命令行接口（Typer 框架）
├── web/                      # Next.js 16 + React 19 前端
├── tests/                    # 测试套件
├── scripts/                  # 运维脚本（安装向导、更新、启动等）
├── requirements/             # 分层依赖声明
├── SKILL.md                  # Agent 技能描述文件
├── AGENTS.md                 # Agent 原生架构说明
└── Dockerfile + compose      # Docker 部署配置
```

### 2.2 扇出流式架构（Fan-out Streaming Architecture）

所有入口统一经过 `ChatOrchestrator`，通过 `StreamBus` 事件总线扇出到多个消费者：

```
入口:  CLI (Typer)  |  WebSocket /api/v1/ws  |  Python SDK
                    ↓           ↓              ↓
         ┌──────────────────────────────────────────┐
         │          ChatOrchestrator                 │
         │  路由到 ChatCapability 或选定 Capability  │
         └─────────┬──────────────┬─────────────────┘
                   │              │
         ┌─────────▼──┐  ┌───────▼──────────┐
         │ ToolRegistry│  │CapabilityRegistry │
         │  (Level 1)  │  │   (Level 2)       │
         └─────────────┘  └──────────────────┘
                   │              │
                   ↓              ↓
         ┌─────────────────────────────┐
         │        StreamBus            │
         │   (asyncio.Queue pub-sub)   │
         └──┬──────┬──────┬───────────┘
            ↓      ↓      ↓
        CLI渲染  WS推送  JSON流(Agent)
```

**三大入口点：**

1. **CLI** — 通过 `deeptutor_cli/main.py`（Typer 框架）
2. **WebSocket API** — 通过 `deeptutor/api/routers/unified_ws.py`
3. **Python SDK** — 通过 `deeptutor/app/facade.py`（`DeepTutorApp` 门面类）

**运行模式：** `RunMode` 枚举（CLI / SERVER），通过环境变量 `DEEPTUTOR_MODE` 控制。

---

## 三、技术栈

### 3.1 后端

| 技术 | 用途 |
|------|------|
| Python 3.11+ | 核心运行时 |
| FastAPI + Uvicorn | HTTP/WebSocket API 服务 |
| asyncio | 全异步架构，贯穿所有 I/O |
| LlamaIndex | RAG 管线和文档索引 |
| OpenAI SDK | 原生 OpenAI API 调用 |
| Anthropic SDK | 原生 Claude API 调用 |
| Pydantic v2 | 数据模型与校验 |
| SQLite (aiosqlite) | 会话持久化 |
| Typer + Rich | CLI 界面 |
| PyMuPDF | PDF 文档解析 |
| Manim | 数学动画生成（可选） |

### 3.2 前端

| 技术 | 用途 |
|------|------|
| Next.js 16 | React 全栈框架 |
| React 19 | UI 组件库 |
| Tailwind CSS | 样式系统 |
| TypeScript | 类型安全 |
| Chart.js | 数据可视化 |
| Mermaid | 图表/流程图渲染 |
| KaTeX | LaTeX 数学公式 |
| Cytoscape | 概念图网络可视化 |
| i18next | 国际化（10 种语言） |
| Framer Motion | 动画效果 |

### 3.3 LLM 提供商支持（30+）

| 类别 | 提供商 |
|------|--------|
| 商用 API | OpenAI, Anthropic, DeepSeek, Gemini, DashScope, Groq, Mistral |
| 开源部署 | Ollama, vLLM, LM Studio, llama.cpp |
| 企业集成 | Azure OpenAI, GitHub Copilot, OpenAI Codex |
| 搜索集成 | Brave, Tavily, Serper, Jina, SearXNG, DuckDuckGo, Perplexity |

所有提供商通过统一的 `LLMProvider` 抽象基类接入，支持自动重试（429/5xx）、指数退避、多模态降级。

---

## 四、核心功能详解

### 4.1 统一聊天工作区（六合一模式）

单一线程内支持六种工作模式自由切换：

| 模式 | 功能 | 核心机制 |
|------|------|----------|
| **Chat** | 工具增强对话 | 自由组合 RAG/搜索/代码/推理工具 |
| **Deep Solve** | 多 Agent 问题求解 | 规划 → 推理 → 书写，每步附带引用 |
| **Quiz Generation** | 测验生成 | 基于知识库出题，内置验证机制 |
| **Deep Research** | 深度研究 | 主题分解，并行调度 Agent，生成引用报告 |
| **Math Animator** | 数学动画 | 概念转 Manim 动画 |
| **Visualize** | 可视化生成 | 自然语言 → SVG/Chart.js/Mermaid/HTML |

**关键设计：工具与工作流解耦** — 用户自行选择启用哪些工具，工作流负责推理编排。

### 4.2 Book Engine（交互式"活书"引擎）

将用户的学习资料自动编译为结构化的交互式书籍。

**生命周期四阶段：**

```
Ideation → Spine Synthesis → Page Compilation → Background Queue
(意图捕获)  (章节骨架生成)     (页面编译)        (异步队列)
```

| 阶段 | Agent | 职责 |
|------|-------|------|
| Ideation | IdeationAgent | 捕获意图，生成书籍提案 |
| Spine Synthesis | SourceExplorer + SpineSynthesizer | 并行探索知识源，多轮合成-批评循环生成骨架 |
| Page Compilation | BookCompiler | 为每章生成页面，按内容类型选择 Block 策略 |
| Background Queue | 异步队列 | 按优先级处理页面，用户打开时即时编译 |

**14 种 Block 类型：**

| 类型 | 说明 |
|------|------|
| text | 正文段落 |
| callout | 提示/注意框 |
| quiz | 嵌入式测验 |
| flash_cards | 闪卡 |
| code | 代码块 |
| figure | 图片/图表 |
| deep_dive | 深度展开子页面 |
| animation | Manim 动画 |
| interactive_demo | 交互式演示 |
| timeline | 时间线 |
| concept_graph | 概念图（Cytoscape） |
| section | 章节分隔 |
| user_note | 用户笔记 |
| placeholder | 占位符 |

### 4.3 持久化记忆系统

双文件记忆架构：

| 文件 | 内容 | 更新时机 |
|------|------|----------|
| **PROFILE.md** | 用户身份画像：偏好、知识水平、学习风格、目标 | 每次对话后 LLM 判断是否更新 |
| **SUMMARY.md** | 学习旅程摘要：当前关注、已完成、开放问题 | 每次对话后 LLM 判断是否更新 |

**更新机制：**

1. 对话轮次结束后，将用户消息和助手回复交给 LLM
2. LLM 判断是否需要更新记忆文件
3. 严格校验 LLM 输出（必须包含预期标题如 Identity、Learning Style 等）
4. 校验通过才写入，`NO_CHANGE` 则跳过
5. 防止模型随意输出污染记忆

### 4.4 TutorBot（自主 AI 辅导员）

基于 nanobot 构建的持久化多实例自主 Agent：

| 特性 | 说明 |
|------|------|
| Soul 模板 | 定义辅导员人格、语气和教学理念 |
| 独立工作区 | 每个 Bot 有独立目录、记忆、会话、技能 |
| 心跳系统 | Bot 可主动发起学习提醒、复习提示 |
| 全工具访问 | RAG、代码执行、Web 搜索、论文搜索、深度推理 |
| 技能学习 | 通过 Skill 文件教授新能力 |
| 多 Agent | 支持子 Agent 生成和多 Agent 团队编排 |

**支持渠道（10+）：**

Telegram、Discord、Slack、飞书、企业微信、钉钉、Email、QQ、WhatsApp、Matrix

### 4.5 AI 协作写作（Co-Writer）

多文档 Markdown 编辑器，AI 作为一等公民：

- 选中文本后进行重写、扩写、摘要
- 可结合知识库和 Web 搜索
- 非破坏性编辑（完整 undo/redo）
- 写作成果可保存到 Notebook

### 4.6 知识管理（Knowledge Hub）

| 功能 | 说明 |
|------|------|
| 知识库 | 上传 PDF/TXT/MD 构建 RAG 向量集合 |
| Notebooks | 跨会话学习记录，支持分类着色 |
| Question Bank | 测验题目汇集，支持书签和 @-mention |
| Skills | 通过 SKILL.md 定义自定义教学人格 |

---

## 五、核心设计模式

### 5.1 两层插件模型

这是 DeepTutor 最核心的架构创新：

```
Level 1 — Tools（工具层）
  - 轻量级单功能，LLM 通过 Function Calling 按需调用
  - 实现 BaseTool 抽象类
  - 提供 get_definition()（OpenAI function-calling Schema）
  - 提供 execute() 方法

Level 2 — Capabilities（能力层）
  - 多步骤 Agent 管线，接管整个对话流程
  - 实现 BaseCapability 抽象类
  - 提供 CapabilityManifest（名称、描述、阶段、工具列表）
  - 提供 run() 方法
```

**工具是原子操作，能力是编排逻辑，两者可独立演进。**

### 5.2 StreamBus 扇出模式

基于 `asyncio.Queue` 的发布-订阅事件总线：

- **生产者**（能力/工具）：通过 `emit()`、`content()`、`stage()` 推送事件
- **消费者**（CLI/WS/JSON）：通过 `subscribe()` 获取异步事件流
- 支持多消费者同时订阅，历史事件回放

**事件类型：**

| 事件 | 说明 |
|------|------|
| CONTENT | 文本内容流 |
| THINKING | 推理过程 |
| OBSERVATION | 观察结果 |
| TOOL_CALL / TOOL_RESULT | 工具调用/结果 |
| PROGRESS | 进度更新 |
| SOURCES | 引用来源 |
| STAGE_START / STAGE_END | 阶段开始/结束 |
| RESULT | 最终结果 |
| ERROR / DONE | 错误/完成 |

### 5.3 Agentic Chat Pipeline

思考-行动-观察-响应循环（Think-Act-Observe-Respond）：

1. 根据启用的工具动态组装系统提示词
2. 调用 LLM，LLM 自主选择调用工具
3. 工具执行结果作为观察反馈
4. 支持最多 8 个并行工具调用
5. 工具结果截断为 4000 字符控制上下文
6. 循环直到 LLM 不再请求工具，产生最终响应

### 5.4 UnifiedContext 统一上下文

贯穿整个系统的数据载体：

```python
@dataclass
class UnifiedContext:
    session_id: str
    user_message: str
    history: list
    enabled_tools: list
    current_capability: str
    knowledge_base_refs: list
    attachments: list
    language: str
    notebook_context: dict
    memory_context: dict
    skill_context: dict
```

### 5.5 单例 + 懒初始化

广泛使用模块级单例：

- `get_llm_client()` — LLM 客户端
- `get_embedding_client()` — Embedding 客户端
- `get_event_bus()` — 事件总线
- `get_book_engine()` — Book Engine

确保资源全局共享且按需创建。

### 5.6 分层依赖管理

```
.[cli]           → CLI 全功能
.[server]        → [cli] + FastAPI/uvicorn
.[tutorbot]      → [server] + TutorBot Agent + 渠道 SDK
.[matrix]        → Matrix 渠道（需 libolm 系统依赖）
.[math-animator] → Manim 动画（需 LaTeX/ffmpeg）
.[all]           → 以上全部
```

---

## 六、RAG 管线架构

基于 LlamaIndex 构建：

```
deeptutor/services/rag/pipelines/llamaindex/
├── document_loader.py       # 文档加载（PDF/TXT/MD）
├── embedding_adapter.py     # Embedding 适配（桥接到 LlamaIndex）
├── pipeline.py              # 核心管线（索引构建 + 查询）
├── storage.py               # 向量存储管理
└── smart_retriever.py       # 智能检索（多查询策略）
```

**Embedding 提供商支持：**

OpenAI、Cohere、Jina、Ollama、vLLM、OpenAI 兼容接口、阿里云 DashScope

分批处理，自动限制批次大小，批次间插入延迟避免速率限制。

---

## 七、Agent 原生 CLI

基于 Typer + Rich 的完整命令行界面：

| 功能 | 命令示例 |
|------|----------|
| 能力执行 | `deeptutor run <capability> "消息"` |
| 交互 REPL | `deeptutor chat` |
| 知识库管理 | `deeptutor kb create/add/list` |
| 斜杠命令 | `/cap`、`/tool`、`/kb`、`/memory` |
| 双输出模式 | Rich 彩色 / JSON 结构化（供 AI Agent 消费） |
| 会话恢复 | 自动保存/恢复会话上下文 |

---

## 八、与"智学助手"的功能映射

| 智学助手功能 | DeepTutor 对应模块 | 进阶方向 |
|-------------|-------------------|----------|
| 首页推荐 | Chat 模式 + Memory | 基于记忆的动态推荐 |
| 学习画像 | PROFILE.md 记忆系统 | LLM 自动维护的用户画像 |
| 资源中心 | Knowledge Hub + RAG | 文档索引 + 向量检索 |
| 学习路径 | Book Engine | 交互式"活书"自动编译 |
| 智能辅导 | Agentic Pipeline + TutorBot | Think-Act-Observe-Respond 循环 |

---

## 九、技术亮点总结

1. **Agent 原生架构**：从底层构建为 Agent 系统（Tools + Capabilities 两层插件）
2. **流式扇出**：统一后端逻辑同时服务 Web、CLI 和 AI Agent
3. **Book Engine**：散乱资料自动编译为交互式"活书"，极具特色
4. **TutorBot**：自主 Agent，主动学习、主动提醒，非被动响应
5. **渐进式记忆**：使用越多，系统越了解学习者
6. **极致可扩展**：30+ LLM 提供商、10+ 消息渠道、插件化架构
