# 智学助手 - 设计系统

## 设计理念："墨与琥珀"

温暖、专注、学术感。界面应像安静房间里一盏温暖的学习台灯，而非冷冰冰的企业仪表盘。

## 色彩系统

所有颜色使用 OKLCH 色彩空间，定义在 `css/tokens.css` 中。

| 角色 | 令牌 | 值 | 说明 |
|------|------|-----|------|
| 主文字 | `--color-ink` | `oklch(0.22 0.02 30)` | 温暖炭色 |
| 次文字 | `--color-ink-mid` | `oklch(0.35 0.02 30)` | 辅助文字 |
| 背景 | `--color-paper` | `oklch(0.97 0.005 80)` | 暖白纸色 |
| 强调色 | `--color-amber` | `oklch(0.72 0.16 75)` | 金琥珀色 |
| 成功 | `--color-sage` | `oklch(0.68 0.08 155)` | 柔和绿色 |
| 警告 | `--color-rose` | `oklch(0.65 0.14 15)` | 温暖玫瑰色 |

### 禁用

- 紫色渐变 `#667eea → #764ba2`
- `#000` 纯黑和 `#fff` 纯白
- `background-clip: text` 渐变文字
- 玻璃拟态作为默认效果

## 排版

| 元素 | 字体 | 字号 |
|------|------|------|
| 标题 h1-h4 | Noto Serif SC | hero / 2rem / 1.5rem / 1.25rem |
| 正文 | PingFang SC / system-ui | 1rem |
| 代码 | JetBrains Mono | 0.875rem |

标题衬线体 + 正文无衬线体形成自然层级对比。

## 布局

- 最大宽度 1200px 居中
- 无永久侧边栏，全宽内容区
- 每个模块有独立的布局"形状"

## 组件

- 按钮：`.btn-primary`（琥珀实心）、`.btn-ghost`（描边）
- 标签：`.tag`（描边）、`.tag-filled`（实心）
- 进度条：`.bar-track` + `.bar-fill`
- Toast 通知：替代 `alert()`

## 动效

| 类型 | 时长 | 缓动 |
|------|------|------|
| 微交互（hover/focus） | 150ms | ease-out |
| 过渡（模块切换） | 300ms | cubic-bezier(0.4, 0, 0.2, 1) |
| 入场动画 | 500ms | ease-out-expo |
