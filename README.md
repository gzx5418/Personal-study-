# 智学助手 - 基于多智能体的个性化学习系统

> 高等教育个性化学习资源生成与学习路径规划系统

## 项目简介

智学助手是一个基于多智能体架构的个性化学习系统，通过 AI 技术为学生提供定制化的学习资源、智能辅导和学习路径规划。系统采用模块化设计，支持多智能体协同工作，实现真正的个性化学习体验。

## 核心功能

### 🤖 多智能体协同
- **10 个专业化 Agent**：对话、深度求解、画像构建、资源生成、路径规划、评估反馈、学习诊断、安全审查、画像提取、资源规划
- **能力路由调度**：根据用户意图自动选择合适的 Agent
- **SSE 流式通信**：实时内容生成反馈

### 📚 个性化学习资源
- **AI 生成内容**：讲义、练习题、代码案例、思维导图
- **文件上传**：支持 PDF、DOCX、代码文件、文本文件
- **图片分析**：支持图片上传，使用视觉模型（GLM-4.6V）分析
- **Markdown 渲染**：代码高亮、Mermaid 图表、数学公式

### 🎯 学习路径规划
- **知识依赖图**：19 个 Python 知识点、18 条依赖边
- **拓扑排序**：基于掌握度的个性化路径生成
- **自适应调整**：评估后自动调整学习路径
- **图谱可视化**：Mermaid.js 渲染知识依赖关系

### 📊 学习评估
- **掌握度追踪**：做对/做错自动更新，支持衰减机制
- **练习在线作答**：选择题、填空题、编程题
- **评估报告**：掌握度分布、薄弱知识点、学习建议

### 🖼️ 智能辅导
- **多模态输入**：文字、图片、文件上传
- **深度求解**：Plan → Solve → Write 三阶段管线
- **RAG 增强**：基于知识库的检索增强生成
- **安全审查**：生成内容自动质量校验

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端（原生 JS + marked.js + Mermaid.js）      │
├─────────────────────────────────────────────────────────────┤
│                    API 层（FastAPI + SSE）                      │
├─────────────────────────────────────────────────────────────┤
│                    Orchestrator 总控调度                        │
├─────────────────────────────────────────────────────────────┤
│    Chat  │ DeepSolve │ ProfileBuilder │ Generator │ Evaluator │
│    Agent │   Agent   │     Agent      │   Agent   │   Agent   │
├─────────────────────────────────────────────────────────────┤
│              服务层（LLM / RAG / 知识图谱 / 掌握度）               │
├─────────────────────────────────────────────────────────────┤
│                    SQLite 持久化存储                            │
└─────────────────────────────────────────────────────────────┘
```

### 后端技术栈
- **框架**：FastAPI
- **数据库**：SQLite（WAL 模式）
- **LLM**：SiliconFlow API（GLM-4.7 / DeepSeek V3.2 / GLM-4.6V）
- **RAG**：LlamaIndex + ChromaDB（向量检索）+ 关键词检索
- **知识图谱**：NetworkX DAG

### 前端技术栈
- **框架**：原生 JavaScript（SPA）
- **Markdown**：marked.js + highlight.js
- **图表**：Mermaid.js
- **样式**：CSS 变量 + OKLCH 色彩空间

## 项目结构

```
├── index.html                 # 前端入口
├── css/                       # 样式文件
│   ├── tokens.css             # 设计令牌
│   ├── base.css               # 基础样式
│   ├── layout.css             # 布局样式
│   ├── components.css         # 组件样式
│   ├── dashboard.css          # 首页样式
│   ├── profile.css            # 画像样式
│   ├── resources.css          # 资源样式
│   ├── path.css               # 路径样式
│   ├── evaluation.css         # 评估样式
│   └── tutor.css              # 辅导样式
├── js/                        # JavaScript 文件
│   ├── app.js                 # SPA 路由
│   ├── api.js                 # API 封装
│   ├── data.js                # 数据管理
│   ├── utils/dom.js           # DOM 工具 + Markdown 渲染
│   └── modules/               # 页面模块
│       ├── dashboard.js       # 首页
│       ├── profile.js         # 学习画像
│       ├── resources.js       # 资源中心
│       ├── path.js            # 学习路径
│       ├── evaluation.js      # 学习评估
│       └── tutor.js           # 智能辅导
├── backend/                   # 后端代码
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 配置管理
│   ├── core/                  # 核心模块
│   │   ├── agent.py           # BaseAgent 基类
│   │   ├── orchestrator.py    # 总控调度器
│   │   ├── stream_bus.py      # SSE 事件流
│   │   └── context.py         # UnifiedContext
│   ├── agents/                # AI Agent
│   │   ├── chat_agent.py      # 对话 Agent
│   │   ├── deep_solve.py      # 深度求解 Agent
│   │   ├── profile_builder.py # 画像构建 Agent
│   │   ├── generator.py       # 内容生成 Agent
│   │   ├── path_planner.py    # 路径规划 Agent
│   │   ├── evaluator.py       # 评估反馈 Agent
│   │   ├── diagnostic.py      # 学习诊断 Agent
│   │   ├── safety.py          # 安全审查 Agent
│   │   ├── profiler.py        # 画像提取 Agent
│   │   └── resource_planner.py # 资源规划 Agent
│   ├── services/              # 服务层
│   │   ├── database.py        # SQLite 数据库
│   │   ├── llm_service.py     # LLM 调用封装
│   │   ├── rag_service.py     # RAG 检索服务
│   │   ├── knowledge_graph.py # 知识图谱服务
│   │   ├── mastery_service.py # 掌握度追踪
│   │   ├── profile_service.py # 画像服务
│   │   ├── session_service.py # 会话管理
│   │   ├── resource_service.py # 资源存储
│   │   └── prompt_manager.py  # Prompt 模板管理
│   ├── api/                   # API 路由
│   │   ├── chat.py            # 对话 API
│   │   ├── profile.py         # 画像 API
│   │   ├── resources.py       # 资源 API
│   │   ├── path.py            # 路径 API
│   │   └── evaluation.py      # 评估 API
│   ├── prompts/               # Prompt 模板
│   └── data/                  # 数据文件
│       ├── knowledge_bases/   # 知识库
│       └── uploads/           # 上传文件
└── docs/                      # 文档
```

## 快速开始

### 环境要求
- Python 3.10+
- SiliconFlow API Key

### 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 配置环境变量
复制 `.env.example` 为 `.env`，填入你的 API Key：
```bash
cp backend/.env.example backend/.env
```

编辑 `.env` 文件：
```env
LLM_API_KEY=your_siliconflow_api_key
LLM_MODEL=Pro/zai-org/GLM-4.7
LLM_HOST=https://api.siliconflow.cn/v1
```

### 启动服务
```bash
# 启动后端
cd backend
python main.py

# 启动前端（另一个终端）
python -m http.server 3782
```

### 访问应用
- 前端：http://localhost:3782
- 后端 API：http://localhost:8001
- API 文档：http://localhost:8001/docs

## API 文档

### 对话 API
- `POST /api/chat` - 流式对话（SSE）
- `POST /api/chat/sync` - 同步对话
- `GET /api/chat/sessions/{user_id}` - 获取会话列表
- `GET /api/chat/history/{session_id}` - 获取会话历史
- `DELETE /api/chat/session/{session_id}` - 删除会话

### 画像 API
- `GET /api/profile/{user_id}` - 获取画像
- `PUT /api/profile/{user_id}` - 更新画像
- `POST /api/profile/build` - 引导构建画像

### 资源 API
- `POST /api/resources/generate` - 生成资源（SSE）
- `POST /api/resources/upload` - 上传文本资源
- `POST /api/resources/upload-file` - 上传文件（PDF/DOCX/代码）
- `GET /api/resources/list/{user_id}` - 获取资源列表
- `GET /api/resources/detail/{user_id}/{resource_id}` - 获取资源详情
- `DELETE /api/resources/{user_id}/{resource_id}` - 删除资源

### 路径 API
- `POST /api/path/plan` - 生成学习路径
- `POST /api/path/adjust` - 调整学习路径
- `GET /api/path/graph/{course_id}` - 获取知识图谱

### 评估 API
- `POST /api/evaluation/submit` - 提交练习结果
- `POST /api/evaluation/parse-quiz` - 解析练习题
- `GET /api/evaluation/mastery/{user_id}` - 获取掌握度

## 创新点

### 1. 对话式动态画像
通过自然语言对话自动构建并持续更新学生画像，支持 8 个维度的个性化信息收集。

### 2. 多智能体协同生成
10 个专业化 Agent 协同工作，从画像分析到资源生成再到安全审查，形成完整的智能辅导链路。

### 3. 学习路径与资源联动
基于知识依赖图的路径规划，结合掌握度动态调整，实现真正的自适应学习。

### 4. 基于 RAG 的防幻觉
知识库约束 + 来源引用 + 保守回答策略，确保生成内容的准确性。

### 5. 轻量多模态输出
讲义、思维导图、代码、练习题等多种输出形式，满足不同学习需求。

## 演示截图

### 首页
![首页](docs/screenshots/dashboard.png)

### 学习画像
![学习画像](docs/screenshots/profile.png)

### 资源中心
![资源中心](docs/screenshots/resources.png)

### 学习路径
![学习路径](docs/screenshots/path.png)

### 智能辅导
![智能辅导](docs/screenshots/tutor.png)

## 开发团队

- 项目负责人：[你的名字]
- 开发时间：2026 年

## 许可证

本项目仅用于学术研究和竞赛目的。

## 致谢

- SiliconFlow - LLM API 服务
- FastAPI - 后端框架
- marked.js - Markdown 渲染
- Mermaid.js - 图表渲染
