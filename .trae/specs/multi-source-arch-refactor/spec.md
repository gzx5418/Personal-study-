# 多源架构优化重构 Spec

## Why

当前项目（智学助手）虽然功能完整，但存在以下问题：
1. **架构耦合度高**：Agent、服务、API 之间依赖关系复杂，难以独立测试和扩展
2. **RAG 能力有限**：仅支持简单文本检索，缺乏向量检索的防幻觉机制
3. **学习路径规划简单**：基于静态知识图谱，缺乏自适应调整能力
4. **题库生成单一**：仅支持基本题型，缺乏多难度、多题型的智能生成
5. **缺少持久化记忆**：用户学习画像和对话历史缺乏跨会话的持久化机制
6. **前端交互性不足**：缺少实时协作、可视化学习路径等高级交互

参考以下 7 个 GitHub 项目的最佳实践进行优化：
- **A-R007/Multi-Agent-Study-Assistant**：多智能体协作架构
- **HKUDS/DeepTutor**：Agent-Native 架构、持久化记忆、统一工作空间
- **StudentTraineeCenter/edu-agent**：LangGraph + RAG、主动式 AI 辅导
- **arun3676/ai-learning-path-generator**：学习路径生成、任务队列
- **098765d/AI_Tutor**：RAG 防幻觉、课程资料问答
- **csv610/mcq_generator**：多题型智能生成、难度分级
- **Ebimsv/AITutorAgent**：LangGraph 工作流、结构化教程

## What Changes

### 架构层优化
- 引入 LangGraph 风格的状态机工作流，替代简单的 Agent 调度
- 实现 Agent 插件化机制，支持动态注册和能力发现
- 添加统一的 Context Manager，管理跨 Agent 的共享状态

### RAG 增强
- 实现多级检索策略：关键词检索 + 语义检索 + 知识图谱检索
- 添加防幻觉机制：引用溯源、置信度评分、知识库校验
- 支持增量式知识库更新和版本管理

### 学习路径优化
- 实现自适应学习路径算法，基于掌握度动态调整
- 添加前置知识依赖分析
- 集成间隔重复（Spaced Repetition）算法

### 题库生成增强
- 支持多种题型：MCQ、判断题、填空题、简答题、编程题
- 实现难度分级系统：简单、中等、困难
- 添加题目缓存和去重机制
- 支持基于知识点的定向组卷

### 持久化记忆系统
- 实现用户学习画像的持久化存储
- 添加对话历史的智能压缩和摘要
- 支持跨会话的学习进度追踪

### 前端交互增强
- 添加学习路径可视化（时间线 + 图谱视图）
- 实现资源卡片的交互式预览
- 优化移动端响应式布局

## Impact

### Affected Specs
- 多智能体调度系统
- RAG 检索服务
- 学习路径规划
- 题库生成系统
- 用户画像系统
- 前端交互模块

### Affected Code
- `backend/core/orchestrator.py` - 调度器重构
- `backend/core/agent.py` - Agent 基类增强
- `backend/services/rag_service.py` - RAG 服务增强
- `backend/services/mastery_service.py` - 掌握度服务增强
- `backend/agents/` - 所有 Agent 实现
- `backend/api/` - API 层适配
- `js/modules/` - 前端模块优化
- `css/` - 样式优化

## ADDED Requirements

### Requirement: LangGraph 风格工作流引擎
系统 SHALL 提供基于状态机的工作流引擎，支持：
- 节点（Node）定义和边（Edge）路由
- 条件分支和循环
- 状态持久化和恢复
- 并行执行和错误处理

#### Scenario: 复杂问题求解
- **WHEN** 用户提交复杂问题
- **THEN** 系统启动 Plan → Solve → Write 工作流
- **AND** 每个阶段可以调用不同的 Agent
- **AND** 支持中间结果的流式输出

### Requirement: Agent 插件化机制
系统 SHALL 支持 Agent 的动态注册和发现：
- Agent 通过配置文件声明能力（capability）
- 调度器根据用户意图自动选择 Agent
- 支持 Agent 的热加载和卸载

#### Scenario: 新增 Agent
- **WHEN** 开发者创建新的 Agent 类
- **THEN** 只需在配置中注册即可使用
- **AND** 无需修改调度器代码

### Requirement: 多级 RAG 检索
系统 SHALL 提供多级检索策略：
- 第一级：关键词匹配（BM25）
- 第二级：语义向量检索（Embedding）
- 第三级：知识图谱遍历
- 结果融合和排序

#### Scenario: 课程资料问答
- **WHEN** 用户上传课程资料并提问
- **THEN** 系统从三个级别检索相关内容
- **AND** 返回带引用来源的答案
- **AND** 标注置信度评分

### Requirement: 防幻觉机制
系统 SHALL 实现防幻觉机制：
- 所有生成内容必须有知识库来源支撑
- 无法从知识库获取的内容必须明确标注
- 提供置信度评分（0-100%）

#### Scenario: 无来源内容处理
- **WHEN** 用户问题无法从知识库找到答案
- **THEN** 系统明确告知"当前知识库中没有找到相关内容"
- **AND** 建议用户上传相关资料或缩小问题范围

### Requirement: 自适应学习路径
系统 SHALL 基于掌握度动态调整学习路径：
- 分析薄弱知识点
- 生成个性化学习计划
- 支持间隔重复调度

#### Scenario: 薄弱知识点强化
- **WHEN** 用户在某知识点掌握度低于 60%
- **THEN** 系统自动将其加入学习路径
- **AND** 安排间隔重复练习

### Requirement: 多题型智能生成
系统 SHALL 支持多种题型的智能生成：
- MCQ（单选/多选）
- 判断题
- 填空题
- 简答题
- 编程题

#### Scenario: 难度分级生成
- **WHEN** 用户请求生成练习题
- **THEN** 系统根据掌握度选择合适难度
- **AND** 生成 5-10 道题目
- **AND** 提供详细解析

### Requirement: 持久化学习记忆
系统 SHALL 实现用户学习记忆的持久化：
- 学习画像自动更新
- 对话历史智能压缩
- 学习进度跨会话追踪

#### Scenario: 跨会话连续性
- **WHEN** 用户开始新会话
- **THEN** 系统自动加载历史学习画像
- **AND** 基于历史数据提供个性化推荐

## MODIFIED Requirements

### Requirement: 多智能体调度器
现有调度器 SHALL 增强为支持：
- 工作流定义和执行
- 状态管理和持久化
- 错误恢复和重试

### Requirement: LLM 服务
现有 LLM 服务 SHALL 增强为支持：
- 多模型路由（文本/推理/视觉）
- Token 使用统计和限制
- 请求缓存和去重

### Requirement: 前端交互
现有前端 SHALL 增强为支持：
- 学习路径可视化
- 资源卡片交互预览
- 实时流式输出优化

## REMOVED Requirements

### Requirement: 简单文本检索
**Reason**: 被多级 RAG 检索替代
**Migration**: 现有知识库数据将迁移到新的向量存储

### Requirement: 静态学习路径
**Reason**: 被自适应学习路径替代
**Migration**: 现有知识图谱将作为自适应算法的输入
