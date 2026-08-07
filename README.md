# 🎭 Persona Library — 20 个写作人格，即装即用

> **一个仓库 = 一支写作团队。** 内置 20 个精心打磨的 AI 写作人格：创始人、教育者、
> 记者、品牌官、社媒创作者……装进你的 agent 就能用；拿你的文章给它，还能
> 提炼出**只属于你的文风**。改写文本时**事实一个都不许动**。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![Personas](https://img.shields.io/badge/Personas-20-8A2BE2)](#-内置人格花名册)
[![Agents](https://img.shields.io/badge/Compatible-Codex%20·%20Claude%20Code%20·%20opencode-00ADD8)](https://opencode.ai)

---

## 🚀 这是什么？

**Persona Library 是一个 Agent Skill**：`SKILL.md` 是入口，`personas/*.md` 是数据源。

- **⚡ 安装即用**：一条 `ln -s` 装进 skills 目录，重启 agent 就能用——不需要
  API Key、不需要 Python、不需要起服务、不需要写配置（agent 本身就是 LLM）
- **🎯 内置 20 个写作人格**：5 大分类，覆盖创始人 / 教育 / 记者 / 品牌 / 创作者 /
  职场 / 个人等场景，每个都是正反例俱全的完整写作规范
- **🧩 根据你的文本定制**：丢给它 3 篇你的文章，就能提取你的文风，生成
  `custom/<your-id>.md` 专属人格；还能按比例混合多种语气（70% 创始人 + 30% 老师）
- **✅ 事实锁定**：改写铁律——数字 / 实体 / 日期 / 引用一律不动，输出附
  保真 / 风格 / 可读性评分

**可以理解为**：把一支随叫随到的专业写作团队，装进你的 agent。

---

## ⚡ 快速开始（30 秒，零依赖）

### 方式一：Skills CLI（推荐）

跨 agent 的官方 skills CLI，一条命令装到所有项目：

```bash
# 全局安装，所有 agent / 所有项目可用
npx skills add fendouai/persona-library --global

# 只装到指定 agent（opencode / claude-code / codex …）
npx skills add fendouai/persona-library --global --agent <agent-name>

# 项目级安装（可提交到仓库，与协作者共享）
npx skills add fendouai/persona-library
```

更新到最新版：

```bash
npx skills update persona-library --global
```

### 方式二：手动 clone

任意 agent 直接把仓库放进它的 skills 目录（目录名保持 `persona-library`，
与 SKILL.md frontmatter 一致）：

```bash
# opencode（用户级，所有项目可用）
git clone https://github.com/fendouai/persona-library ~/.config/opencode/skills/persona-library

# opencode（项目级，跟随仓库走）
git clone https://github.com/fendouai/persona-library .opencode/skills/persona-library

# Claude Code
git clone https://github.com/fendouai/persona-library ~/.claude/skills/persona-library

# Codex
git clone https://github.com/fendouai/persona-library ~/.codex/skills/persona-library
```

> 两种方式任选其一，安装后**重启 agent**（或重新加载 skills）即可生效。

### 验证

新开一个会话，对 agent 说：

```
/persona-library
用 pragmatic-founder 的语气改写：「这个产品很好用。」
```

预期：agent 定位 `personas/archetypes/pragmatic-founder.md` → 改写 →
附保真/风格评分。无任何环境报错即安装成功。

---

## 🎬 交互方式（全部直接对 agent 说）

### 粘贴模式（默认）

```
/persona-library

用 warm-educator 的语气把这段产品介绍改写得更亲切：
[粘贴你的文本]
```

或直接请求：

```
请 humanize 这段，别让它像 AI 写的：[粘贴你的文本]
```

agent 走完整流程：定位 persona → 锁定事实 → 改写 → 附保真/风格/可读性评分。

### 文件模式（原地改写文件）

```
把 docs/launch-post.md 改成创始人口气
```

agent 读取文件 → 原地改写（只动正文散文，代码块 / frontmatter / 数据不动）
→ 对话中只报告改动摘要，不贴全文。

### 嵌入式（大任务的一环）

在 PR 描述、commit message、发布文案等更大任务里顺带要求：
agent 只输出最终文本，不附草稿和评分。

### 文风校准（用你的文风改写）

**① 轻量校准**——不创建文件，只按你的样本改写这一次：

```
/persona-library

这是我写的样本（用来匹配文风）：
[粘贴 2-3 段你自己的文章]

现在用这个文风 humanize 这段 AI 味很重的文本：
[粘贴要改写的文本]
```

agent 先分析你的句长、用词、段落节奏、标点习惯，再按你的习惯改写——
你爱用的口头禅和怪癖会保留，而不是被抹平成"标准好文"。

**② 持久化**——明确要求创建 persona，生成长久可复用的人格：

```
这是我 3 篇文章，提取我的文风存成 persona。
```

agent 六步抽取 → 生成 `personas/custom/my-voice.md` → 报告各维度置信度
（句长 0.91 高 · 幽默 0.42 低，低置信维度会如实告诉你）。

### 更多用法

| 你想做什么 | 对 agent 说 | 行为 |
|---|---|---|
| 按人格改写 | 「用 warm-educator 的语气把这段产品介绍改写得更亲切」 | 读 persona → 锁定事实 → 改写 → 评分 |
| 去 AI 味 | 「humanize 这段，别让它像 AI 写的」 | 匹配 `concise-tech-creator` → 改写 |
| 提取文风 | 「这是我 3 篇专栏，提取我的写作风格存成 persona」 | 六步抽取 → 生成 `personas/custom/<id>.md` → 报告置信度 |
| 混合语气 | 「70% 创始人口气 + 30% 老师的语气，改写这段话」 | 读两个 persona → 加权合成 → 改写 |
| 保真检查 | 「看看这次改写有没有改掉事实」 | 对照原文逐项核数字 / 实体 / 日期 → 评分 |

**改写示例：**

```
你：帮我把这封邮件改得像一个温暖的老师写的。
agent：我选择 warm-educator（温暖 / 比喻 / 循序渐进）。
      改写结果：……
      评分：meaning 0.97 · style 0.86 · readability 0.92
      数字与日期原样保留，风格强度 0.7，需要更浓可以调高。
```

**铁律**：数字 / 实体 / 日期 / 链接 / 引用不动 · 不新增事实 · 不改立场 ·
不删不确定性 · 不虚构个人经历 · 长度 ±20%。

---

## 🎨 内置人格花名册（20 个）

### 🎭 Archetypes — 经典原型

| Persona | 适用场景 |
|---------|----------|
| [pragmatic-founder](personas/archetypes/pragmatic-founder.md) | 创始人视角：直接、落地、可执行 |
| [warm-educator](personas/archetypes/warm-educator.md) | 教育者：温暖、比喻、循序渐进 |
| [investigative-journalist](personas/archetypes/investigative-journalist.md) | 记者：求证、克制、讲证据 |
| [keynote-product-visionary](personas/archetypes/keynote-product-visionary.md) | 发布会级愿景叙事 |
| [first-principles-thinker](personas/archetypes/first-principles-thinker.md) | 第一性原理：拆解、重建、严谨 |

### ✍️ Creators — 内容创作者

| Persona | 适用场景 |
|---------|----------|
| [concise-tech-creator](personas/creators/concise-tech-creator.md) | 技术博主：短句、去 AI 味 |
| [story-first-essayist](personas/creators/story-first-essayist.md) | 长文：故事驱动、有钩子 |
| [short-form-viral-creator](personas/creators/short-form-viral-creator.md) | 短视频文案：高密度、强钩子 |
| [honest-personal-blogger](personas/creators/honest-personal-blogger.md) | 个人博客：真诚、不端着 |

### 🏷️ Brands — 品牌声音

| Persona | 适用场景 |
|---------|----------|
| [minimalist-saas-brand](personas/brands/minimalist-saas-brand.md) | 极简 SaaS：克制、清晰 |
| [bold-d2c-brand](personas/brands/bold-d2c-brand.md) | 消费品牌：大胆、有态度 |
| [institutional-trust-brand](personas/brands/institutional-trust-brand.md) | 机构品牌：可信、稳健 |

### 💼 Professional — 职场沟通

| Persona | 适用场景 |
|---------|----------|
| [executive-communicator](personas/professional/executive-communicator.md) | 高管汇报：结论先行、有决策依据 |
| [analyst-brief-writer](personas/professional/analyst-brief-writer.md) | 分析师简报：数据导向 |
| [customer-success-voice](personas/professional/customer-success-voice.md) | 客户成功：共情 + 解决问题 |
| [academic-researcher](personas/professional/academic-researcher.md) | 学术写作：严谨、有引用 |

### 🪴 Personal — 个人表达

| Persona | 适用场景 |
|---------|----------|
| [calm-reflective-writer](personas/personal/calm-reflective-writer.md) | 沉稳反思：安静、有分量 |
| [witty-social-voice](personas/personal/witty-social-voice.md) | 社交文案：机智、有梗 |
| [direct-no-filler-communicator](personas/personal/direct-no-filler-communicator.md) | 直给沟通：零废话 |
| [empathetic-coach](personas/personal/empathetic-coach.md) | 教练式：倾听、鼓励、引导 |

> 想要谁？把 agent 切换到任意 persona，或提出你的场景，让 agent 按
> [PERSONA_SPEC.md](PERSONA_SPEC.md) 帮你定制一个。

---

## 🧰 进阶工具（可选，核心用法不需要）

skill 本体在对话内完成一切；以下为可选增强：

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
persona list                                    # 浏览人格
persona show warm-educator                      # 查看详情
persona extract --from samples.txt --name "My Voice" --save   # 文本提取文风
persona rewrite article.md --persona pragmatic-founder --strength 0.8 --platform x
persona mix mix.json                            # 混合人格
persona export pragmatic-founder --tool claude  # 导出给其他工具
```

> CLI / API 的抽取与改写走 OpenAI 兼容接口，需要 `OPENAI_API_KEY`。
> **仅此部分需要** —— skill 本体零依赖。

---

## 📁 仓库结构

```text
├── SKILL.md              # skill 入口：触发词 / 四步工作流 / 内联改写模板 / 铁律
├── PERSONA_SPEC.md       # Persona 文件规范
├── personas/             # 20 个写作人格（Markdown，即 skill 的数据源）
│   ├── archetypes/  creators/  brands/  professional/  personal/
├── CONTRIBUTING.md       # 贡献新 persona 的检查清单
├── prompts/              # LLM Prompt 模板
├── schemas/              # JSON Schema
├── src/persona_lib/      # 进阶：Python CLI
├── app/ · web/           # 进阶：FastAPI / Next.js
├── scripts/ · tests/ · dist/
```

---

## 🤝 贡献

- 新增 Persona：在 `personas/<category>/` 下写 Markdown，遵循
  [PERSONA_SPEC.md](PERSONA_SPEC.md)，对照 [CONTRIBUTING.md](CONTRIBUTING.md) 检查清单
- 校验：`python scripts/lint_personas.py`、`python scripts/check_originality.py <文件>`
- 你的 Persona 会被所有安装了本 skill 的 agent 直接使用

## License

MIT
