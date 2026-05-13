# 智学助手 - 高等教育个性化学习智能体系统

面向高等教育个性化学习场景的多智能体学习系统。项目围绕学生画像、个性化资源生成、学习路径规划、智能辅导和学习效果评估，提供完整可演示的系统链路。

## 核心能力

### 多智能体协同架构
- **画像智能体**：对话式动态画像构建，支持引导式冷启动与自动更新
- **资源规划智能体**：基于画像和知识图谱推荐个性化资源类型
- **资源生成智能体**：支持讲义、练习题、思维导图、代码案例等多种资源类型
- **安全校验智能体**：内容安全审查与防幻觉机制
- **路径规划智能体**：基于知识图谱和掌握度生成阶段化学习路径
- **评估智能体**：支持选择题、填空题、代码题的结构化评估与掌握度更新

### 文档预览
- **PDF 文件**：浏览器内置 PDF 查看器直接预览，保留原始排版
- **Word 文件**：自动转换为结构化 Markdown（保留标题层级、粗体斜体、表格），前端渲染展示
- **代码文件**：语法高亮展示，支持 Python/Java/C++ 等 20+ 语言

### 个性化学习
- 对话式画像构建与动态更新
- 基于掌握度的自适应学习路径推荐
- 多类型资源 AI 生成（`lecture`、`quiz`、`mindmap`、`code_lab`、`ppt_outline`、`extended_reading`）
- RAG 检索增强生成，支持来源展示与安全双校验
- 多课程框架：课程选择器、课程知识库、课程知识图谱

## 技术栈

### 后端
- **FastAPI** — 异步 Web 框架
- **SQLite** — 轻量数据持久化（WAL 模式）
- **OpenAI Compatible API** — LLM 接入
- **LlamaIndex + ChromaDB** — RAG 检索增强
- **NetworkX** — 知识图谱构建与路径规划
- **PyPDF2** — PDF 文本提取
- **python-docx** — Word 文档解析

### 前端
- **原生 JavaScript SPA** — 零框架依赖
- **marked.js** — Markdown 渲染
- **highlight.js** — 代码语法高亮
- **Mermaid.js** — 思维导图与流程图渲染
- **OKLCH 色彩系统** — 现代 CSS 设计系统

## 目录结构

```
├── index.html                  # 前端入口
├── css/                        # 样式文件（设计系统 + 各模块样式）
├── js/
│   ├── api.js                  # API 调用层
│   ├── app.js                  # SPA 路由与框架
│   └── modules/                # 功能模块
│       ├── dashboard.js        # 首页仪表盘
│       ├── profile.js          # 学习画像
│       ├── resources.js        # 资源中心（含文档预览）
│       ├── path.js             # 学习路径
│       ├── evaluation.js       # 学习评估
│       └── tutor.js            # 智能辅导
├── backend/
│   ├── main.py                 # 服务入口
│   ├── config.py               # 配置管理
│   ├── api/                    # API 路由
│   ├── agents/                 # 多智能体实现
│   ├── services/               # 业务服务层
│   └── prompts/                # Prompt 模板
├── data/                       # 数据存储
│   ├── zhixue.db               # SQLite 数据库
│   ├── knowledge_bases/        # 课程知识库
│   └── uploads/                # 上传文件存储
└── docs/                       # 项目文档
```

## 快速启动

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `backend/.env`：

```env
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
LLM_HOST=https://api.openai.com/v1
COURSE_ID=python_programming
```

### 3. 启动后端服务

```bash
cd backend
python main.py
```

后端运行在 `http://localhost:8001`

### 4. 启动前端

```bash
python -m http.server 3782
```

访问 `http://localhost:3782`

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 流式对话（SSE） |
| POST | `/api/profile/build` | 构建学习画像 |
| GET | `/api/profile/{user_id}` | 获取画像 |
| POST | `/api/resources/generate` | 生成资源（流式） |
| POST | `/api/resources/upload-file` | 上传文档（PDF/DOCX/代码） |
| GET | `/api/resources/file/{user_id}/{id}` | 获取原始 PDF 文件 |
| GET | `/api/resources/list/{user_id}` | 资源列表 |
| POST | `/api/path/plan` | 学习路径规划 |
| POST | `/api/evaluation/submit` | 提交练习结果 |
| GET | `/api/evaluation/mastery/{user_id}` | 获取掌握度 |

完整 API 文档：`http://localhost:8001/docs`

## 设计特点

- **OKLCH 色彩系统**：基于感知均匀色彩空间的 Modern Scholar 设计风格
- **Glassmorphism UI**：磨砂玻璃质感头部栏与面板
- **响应式布局**：适配桌面与移动端
- **安全防护**：资源 ID 正则校验、路径遍历防护、XSS 转义、SQL 参数化查询

## 开源协议

见 [OSS_NOTICE.md](./OSS_NOTICE.md)
