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

### 工作流引擎
- **状态机架构**：支持节点定义、边路由、条件分支和循环
- **深度求解**：Plan → Solve → Write 三阶段工作流
- **状态持久化**：支持工作流状态的保存和恢复
- **错误恢复**：内置最大步数保护和异常处理

### 插件化 Agent 系统
- **能力声明**：Agent 通过 `capabilities` 属性声明支持的能力
- **自动注册**：使用 `@register_agent` 装饰器自动注册
- **动态发现**：调度器根据用户意图自动选择 Agent
- **热加载**：支持 Agent 的动态加载和卸载

### 多级 RAG 检索
- **关键词检索**：BM25 算法进行文本匹配
- **语义检索**：向量 Embedding 相似度搜索
- **结果融合**：RRF 算法融合多级检索结果
- **检索缓存**：5 分钟 TTL 缓存机制

### 防幻觉机制
- **引用溯源**：所有生成内容标注知识库来源
- **置信度评分**：0-100% 置信度计算（一致性、相关性、匹配度）
- **知识库校验**：自动检测无来源支撑的内容
- **低置信度警告**：置信度 < 30% 时自动提示用户

### 自适应学习路径
- **掌握度分析**：识别薄弱知识点（<60%）
- **遗忘曲线**：艾宾浩斯遗忘曲线计算保留率
- **间隔重复**：SM-2 算法调度复习计划
- **前置依赖**：知识图谱依赖关系分析

### 多题型生成
- **MCQ**：单选/多选题生成，支持干扰项
- **判断题**：正误判断，附判断依据
- **填空题**：关键概念提取，多可接受答案
- **简答题**：开放式问题，附参考答案和评分标准
- **难度分级**：基于认知层次的难度评估
- **智能组卷**：根据掌握度分配题目难度比例

### 持久化记忆
- **画像自动更新**：从对话中提取学习偏好和知识水平
- **对话压缩**：智能压缩历史对话，保留关键信息
- **会话摘要**：自动生成会话摘要（主题、问题、成果）
- **跨会话连续性**：新会话自动加载历史画像和学习进度

### 文档预览
- **PDF 文件**：浏览器内置 PDF 查看器直接预览，保留原始排版
- **Word 文件**：自动转换为结构化 Markdown，前端渲染展示
- **代码文件**：语法高亮展示，支持 20+ 语言
- **资源预览弹窗**：支持全屏查看、评分和反馈

### 学习路径可视化
- **时间线视图**：按阶段展示学习进度
- **图谱视图**：Mermaid 渲染知识依赖图
- **推荐面板**：个性化学习推荐和原因
- **间隔重复计划**：待复习知识点和时间安排

### 移动端响应式
- **汉堡菜单**：移动端导航栏折叠
- **触摸优化**：最小触摸目标 44px
- **自适应布局**：768px 和 480px 两档断点
- **滚动优化**：防止水平滚动，优化滚动行为

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
- **Mermaid.js** — 思维导图、流程图、知识图谱渲染
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
│       ├── path.js             # 学习路径（含可视化）
│       ├── evaluation.js       # 学习评估
│       └── tutor.js            # 智能辅导
├── backend/
│   ├── main.py                 # 服务入口
│   ├── config.py               # 配置管理
│   ├── core/                   # 核心框架
│   │   ├── agent.py            # Agent 基类 + 注册表
│   │   ├── orchestrator.py     # 调度器
│   │   ├── context.py          # 统一上下文
│   │   ├── workflow.py         # 工作流引擎
│   │   └── stream_bus.py       # 流式事件总线
│   ├── api/                    # API 路由
│   │   ├── chat.py             # 对话 API
│   │   ├── profile.py          # 画像 API
│   │   ├── resources.py        # 资源 API（含评分）
│   │   ├── path.py             # 路径 API
│   │   ├── evaluation.py       # 评估 API
│   │   ├── learning_path.py    # 学习路径可视化 API
│   │   └── knowledge.py        # 知识库版本管理 API
│   ├── agents/                 # 多智能体实现
│   │   ├── chat_agent.py       # 对话智能体
│   │   ├── generator.py        # 资源生成智能体
│   │   ├── path_planner.py     # 路径规划智能体
│   │   ├── evaluator.py        # 评估智能体
│   │   └── safety.py           # 安全校验智能体
│   ├── services/               # 业务服务层
│   │   ├── llm_service.py      # LLM 服务
│   │   ├── rag_service.py      # RAG 检索服务
│   │   ├── mastery_service.py  # 掌握度服务
│   │   ├── profile_service.py  # 画像服务
│   │   ├── session_service.py  # 会话服务
│   │   ├── question_service.py # 题目生成服务
│   │   ├── confidence_service.py # 置信度服务
│   │   ├── spaced_repetition_service.py # 间隔重复服务
│   │   └── database.py         # 数据库服务
│   ├── scripts/                # 辅助脚本
│   │   ├── total_md_split.py   # Markdown 分割
│   │   └── svg_to_pptx/        # SVG 转 PPTX
│   ├── prompts/                # Prompt 模板
│   └── tests/                  # 单元测试（100 个）
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
python -m http.server 8080
```

访问 `http://localhost:8080`

## API 接口

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 流式对话（SSE） |
| POST | `/api/chat/sync` | 同步对话 |
| POST | `/api/profile/build` | 构建学习画像 |
| GET | `/api/profile/{user_id}` | 获取画像 |
| POST | `/api/resources/generate` | 生成资源（流式） |
| POST | `/api/resources/upload-file` | 上传文档（PDF/DOCX/代码） |
| POST | `/api/resources/rate` | 资源评分（1-5 星） |
| GET | `/api/resources/list/{user_id}` | 资源列表 |
| GET | `/api/resources/file/{user_id}/{id}` | 获取原始文件 |
| POST | `/api/path/plan` | 学习路径规划 |
| POST | `/api/evaluation/submit` | 提交练习结果 |
| GET | `/api/evaluation/mastery/{user_id}` | 获取掌握度 |

### 学习路径可视化接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/learning-path/timeline/{user_id}` | 时间线视图数据 |
| GET | `/api/learning-path/graph/{user_id}` | 图谱视图数据 |
| GET | `/api/learning-path/recommendations/{user_id}` | 个性化推荐 |
| GET | `/api/learning-path/spaced-repetition/{user_id}` | 间隔重复计划 |

### 知识库管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/list` | 列出所有知识库 |
| GET | `/api/knowledge/{kb_name}/versions` | 版本历史 |
| POST | `/api/knowledge/{kb_name}/update` | 更新知识库 |
| POST | `/api/knowledge/{kb_name}/rollback` | 回滚版本 |

完整 API 文档：`http://localhost:8001/docs`

## 测试

```bash
cd backend
python -m pytest tests/ -v
```

测试覆盖：
- 工作流引擎测试（17 个）
- 上下文管理器测试（18 个）
- 题目服务测试（38 个）
- 置信度服务测试（27 个）

## 设计特点

- **OKLCH 色彩系统**：基于感知均匀色彩空间的 Modern Scholar 设计风格
- **Glassmorphism UI**：磨砂玻璃质感头部栏与面板
- **响应式布局**：适配桌面与移动端（768px/480px 断点）
- **安全防护**：资源 ID 正则校验、路径遍历防护、XSS 转义、SQL 参数化查询
- **中文支持**：完整的中文文件名和内容处理支持

## 开源协议

见 [OSS_NOTICE.md](./OSS_NOTICE.md)
