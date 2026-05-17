# Tasks

## 阶段一：核心架构优化（基础层）

- [x] Task 1: 重构 Agent 基类，支持插件化注册
  - [x] SubTask 1.1: 设计 Agent 能力声明接口（capability manifest）
  - [x] SubTask 1.2: 实现 Agent 注册表（registry）和自动发现机制
  - [x] SubTask 1.3: 修改 `backend/core/agent.py`，添加 `capabilities` 属性
  - [x] SubTask 1.4: 更新 `backend/core/orchestrator.py`，使用注册表调度 Agent

- [x] Task 2: 实现 LangGraph 风格工作流引擎
  - [x] SubTask 2.1: 设计 Workflow、Node、Edge 数据结构
  - [x] SubTask 2.2: 实现工作流执行器（支持条件分支和循环）
  - [x] SubTask 2.3: 实现状态持久化和恢复机制
  - [x] SubTask 2.4: 将 DeepSolve 迁移为工作流定义

- [x] Task 3: 统一上下文管理器
  - [x] SubTask 3.1: 增强 `UnifiedContext`，添加共享状态存储
  - [x] SubTask 3.2: 实现跨 Agent 的数据传递机制
  - [x] SubTask 3.3: 添加上下文序列化和反序列化

## 阶段二：RAG 增强（检索层）

- [x] Task 4: 多级 RAG 检索实现
  - [x] SubTask 4.1: 集成 BM25 关键词检索（参考 098765d/AI_Tutor）
  - [x] SubTask 4.2: 增强语义向量检索，支持多 Embedding 模型
  - [x] SubTask 4.3: 实现检索结果融合和排序算法
  - [x] SubTask 4.4: 添加检索缓存机制

- [x] Task 5: 防幻觉机制实现
  - [x] SubTask 5.1: 实现引用溯源系统（source_id 追踪）
  - [x] SubTask 5.2: 添加置信度评分算法
  - [x] SubTask 5.3: 实现知识库校验 Agent（参考 edu-agent 的 0% 幻念率）
  - [x] SubTask 5.4: 更新 Generator Agent，强制引用来源

- [ ] Task 6: 知识库版本管理
  - [ ] SubTask 6.1: 实现知识库增量更新机制
  - [ ] SubTask 6.2: 添加知识库版本号管理
  - [ ] SubTask 6.3: 实现向量索引的自动重建

## 阶段三：学习路径优化（规划层）

- [x] Task 7: 自适应学习路径算法
  - [x] SubTask 7.1: 实现掌握度分析模块（参考 arun3676/ai-learning-path-generator）
  - [x] SubTask 7.2: 设计前置知识依赖图
  - [x] SubTask 7.3: 实现路径动态调整算法
  - [x] SubTask 7.4: 集成间隔重复调度（Spaced Repetition）

- [ ] Task 8: 学习路径可视化数据接口
  - [ ] SubTask 8.1: 设计路径节点数据结构
  - [ ] SubTask 8.2: 实现时间线视图数据 API
  - [ ] SubTask 8.3: 实现图谱视图数据 API

## 阶段四：题库生成增强（评估层）

- [x] Task 9: 多题型生成引擎
  - [x] SubTask 9.1: 设计题目数据模型（参考 csv610/mcq_generator）
  - [x] SubTask 9.2: 实现 MCQ 生成器（单选/多选）
  - [x] SubTask 9.3: 实现判断题生成器
  - [x] SubTask 9.4: 实现填空题生成器
  - [x] SubTask 9.5: 实现简答题生成器
  - [x] SubTask 9.6: 实现编程题生成器

- [x] Task 10: 难度分级和智能组卷
  - [x] SubTask 10.1: 实现题目难度评估算法
  - [x] SubTask 10.2: 实现基于掌握度的题目推荐
  - [x] SubTask 10.3: 实现题目缓存和去重
  - [x] SubTask 10.4: 实现定向组卷功能

## 阶段五：持久化记忆系统（数据层）

- [ ] Task 11: 用户学习画像持久化
  - [ ] SubTask 11.1: 增强 ProfileService，支持自动更新
  - [ ] SubTask 11.2: 实现对话历史智能压缩（参考 DeepTutor 的持久化记忆）
  - [ ] SubTask 11.3: 添加学习进度追踪表

- [x] Task 12: 跨会话连续性
  - [x] SubTask 12.1: 实现会话摘要生成
  - [x] SubTask 12.2: 实现历史数据快速加载
  - [x] SubTask 12.3: 实现个性化推荐引擎

## 阶段六：前端交互优化（展示层）

- [x] Task 13: 学习路径可视化组件
  - [x] SubTask 13.1: 实现时间线视图组件
  - [x] SubTask 13.2: 实现图谱视图组件（使用 Mermaid 或 D3.js）
  - [x] SubTask 13.3: 添加路径节点交互（点击展开详情）

- [x] Task 14: 资源卡片交互优化
  - [x] SubTask 14.1: 实现资源预览弹窗
  - [x] SubTask 14.2: 添加资源评分和反馈
  - [x] SubTask 14.3: 优化资源加载动画

- [x] Task 15: 移动端响应式优化
  - [x] SubTask 15.1: 优化导航栏移动端布局
  - [x] SubTask 15.2: 优化对话界面移动端体验
  - [x] SubTask 15.3: 测试并修复移动端兼容性问题

## 阶段七：测试和文档（质量层）

- [x] Task 16: 单元测试编写
  - [x] SubTask 16.1: 编写 Agent 基类测试
  - [x] SubTask 16.2: 编写工作流引擎测试
  - [x] SubTask 16.3: 编写 RAG 服务测试
  - [x] SubTask 16.4: 编写题库生成测试

- [x] Task 17: 集成测试和文档
  - [x] SubTask 17.1: 编写 API 集成测试
  - [x] SubTask 17.2: 更新 README 文档
  - [x] SubTask 17.3: 编写架构设计文档

# Task Dependencies

- Task 2 depends on Task 1（工作流引擎依赖 Agent 插件化）
- Task 4 depends on Task 1（多级检索依赖 Agent 注册）
- Task 5 depends on Task 4（防幻觉依赖多级检索）
- Task 7 depends on Task 3（自适应路径依赖上下文管理）
- Task 9 depends on Task 1（多题型生成依赖 Agent 注册）
- Task 11 depends on Task 3（持久化记忆依赖上下文管理）
- Task 13 depends on Task 8（可视化依赖数据接口）
- Task 16 depends on Task 1-15（测试依赖所有功能实现）

# Parallelizable Work

- Task 4 和 Task 7 可并行（RAG 增强和学习路径优化互不依赖）
- Task 9 和 Task 11 可并行（题库生成和持久化记忆互不依赖）
- Task 13 和 Task 14 可并行（路径可视化和资源卡片优化互不依赖）
