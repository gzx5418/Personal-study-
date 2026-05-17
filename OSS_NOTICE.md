# Open Source And Tooling Notice

本项目在开发与运行中使用了以下开源项目或工具。提交比赛材料时，建议将本文件与 README 一并附上。

| 名称 | 用途 | 来源 | 协议 |
|---|---|---|---|
| FastAPI | 后端 Web API 框架 | https://fastapi.tiangolo.com/ | MIT |
| Uvicorn | ASGI 服务运行 | https://www.uvicorn.org/ | BSD-3-Clause |
| Pydantic | 数据校验与模型定义 | https://docs.pydantic.dev/ | MIT |
| OpenAI Python SDK | 调用兼容 OpenAI 的大模型接口 | https://github.com/openai/openai-python | Apache-2.0 |
| LlamaIndex | RAG 检索与向量索引框架 | https://www.llamaindex.ai/ | MIT |
| ChromaDB | 向量存储 | https://www.trychroma.com/ | Apache-2.0 |
| NetworkX | 知识图谱与 DAG 路径计算 | https://networkx.org/ | BSD |
| marked.js | Markdown 渲染 | https://marked.js.org/ | MIT |
| highlight.js | 代码高亮 | https://highlightjs.org/ | BSD-3-Clause |
| Mermaid | 图表与思维导图渲染 | https://mermaid.js.org/ | MIT |
| JSZip | 文档预览依赖 | https://stuk.github.io/jszip/ | MIT or GPLv3 |
| PyPDF2 | PDF 文本提取 | https://pypdf2.readthedocs.io/ | BSD-3-Clause |
| Mammoth | DOCX 到 HTML/Markdown 内容提取 | https://github.com/mwilliamson/python-mammoth | BSD-2-Clause |
| markdownify | HTML 到 Markdown 转换 | https://github.com/matthewwithanm/python-markdownify | MIT |
| python-pptx | PPTX 文件生成 | https://python-pptx.readthedocs.io/ | MIT |
| PPT Master | SVG 到原生可编辑 PPTX 导出管线 | ./ppt-master-main | MIT |
| svglib / ReportLab | PPT Master 兼容导出依赖 | https://github.com/deeplook/svglib / https://www.reportlab.com/ | LGPL-3.0 / BSD |
| Pillow | PPT Master 图片处理依赖 | https://python-pillow.org/ | HPND |
| docx-preview | DOCX 页面预览 | https://github.com/VolodymyrBaydalka/docxjs | Apache-2.0 |

## 外部 AI 能力说明

- 本项目通过兼容 OpenAI 协议的大模型接口完成对话、资源生成、画像抽取和安全审查。
- 第一阶段未直接接入视频生成模型；赛题中的多模态资源以 `PPT Master 原生可编辑 PPTX`、`动画分镜脚本`、`思维导图`、`代码案例`、`拓展阅读` 和结构化讲义实现。
