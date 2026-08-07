---
name: persona-library
description: >
  Use when the user wants to rewrite / 改写 / 润色 / 换语气 / humanize text in
  a specific writing persona or voice — e.g. "帮我用创始人语气改写这段"、
  "rewrite this in a warm educator voice"、"humanize this copy"、
  "让这段话更像人写的"、"去 AI 味"。

  Use when the user wants to:
  - create a writing persona from their own sample texts（从我的文章提取文风/创建写作人格）
  - mix or blend two voices with weights（70% 创始人 30% 老师 / 混合两种语气）
  - evaluate whether a rewrite preserved facts and matched a style（保真检查/评分）
  - pick a persona to write or rewrite in（用哪个语气写）

  Works entirely in-context: reads personas/*.md as writing specifications and
  rewrites directly. Zero setup — no API keys, no CLI, no Python, no server.

  NOT for: plain translation or generic proofreading with no voice/persona
  request; writing long-form content from scratch.
triggers:
  - rewrite: 改写/润色/换语气/重写/更地道/像人写的/去 AI 味/humanize/rewrite/rephrase/in the voice of/以某身份写
  - create-persona: 创建 persona/提取文风/我的写作风格/分析我的文风/写作人格/from my writing
  - mix: 混合/组合/两种风格/70% 30%/blend
  - evaluate: 保真/评分/风格匹配/fidelity/有没有改事实
---

# Persona Library — 写作人格 Skill（零配置，agent 直接运行）

这个 skill 给 agent 一套「写作人格」能力。**你（agent）就是执行者**：
`personas/` 目录里的 Markdown 文件是写作规范，你读取它们，然后直接在对话内
完成改写、创建、混合与评估。不需要任何外部 LLM 调用、API Key 或服务。

## 核心原则

1. **内容保真是底线**：数字、实体、日期、链接、引用、作者立场、不确定性措辞
   一个都不能动；不新增原文没有的事实。
2. **Persona 是表达框架，不是角色扮演**：你应用它的语气与结构，不冒充真人，
   不虚构个人经历。
3. **风格可以激进，事实不能动**：风格强度只是措辞/结构层面的浓度。

## 何时用

- 用户想「换一种说法」且指定或可推断出**语气/人格**（创始人、老师、记者、
  品牌、随笔作家……）
- 用户想从自己的样本文本里**提取文风**并复用
- 用户想**混合**两种表达方式
- 用户想检查改写是否**改变了事实**

## 工作流（四步，全部在对话内完成）

### STEP 1 — 定位 Persona

用文件工具在 `personas/` 下查找：

```
personas/archetypes/   pragmatic-founder / warm-educator / investigative-journalist
                       keynote-product-visionary / first-principles-thinker
personas/creators/     concise-tech-creator / story-first-essayist
                       short-form-viral-creator / honest-personal-blogger
personas/brands/       minimalist-saas-brand / bold-d2c-brand / institutional-trust-brand
personas/professional/ executive-communicator / analyst-brief-writer
                       customer-success-voice / academic-researcher
personas/personal/     calm-reflective-writer / witty-social-voice
                       direct-no-filler-communicator / empathetic-coach
```

- 不确定选哪个：`Glob personas/**/*.md` → 快速浏览各文件 frontmatter 的
  `description` / `tags` / `Tone Dimensions` 与用户需求匹配
- 用户没有指定 persona 时，根据需求判断最贴近的（如"像创始人"→
  `pragmatic-founder`），并在输出前说明选择理由
- 读取选定文件全文，它就是你接下来改写的**写作规范**

### STEP 2 — 内容锁定（改写前必须做）

从原文提取不可变约束，改写时逐条守住：

```text
- claims:        事实主张（如「产品将于 9 月发布」）
- entities:      专有名词、人名、组织、产品名
- numbers:       所有数字、日期、百分比、统计量
- position:      作者立场（一句话）
- uncertainties: "可能/也许/在某种程度上/有迹象表明"等限定措辞
```

### STEP 3 — 改写（你直接执行）

把 persona 文件全文 + 原文 + 约束注入自己的改写任务，模板：

```markdown
Rewrite the source text using the writing persona below.

Priority:
1. Preserve meaning; every fact, number, date, entity, link, citation
2. Preserve the author's position and all uncertainty wording
3. Apply the persona's tone, sentence rhythm, vocabulary, structure
4. Adapt to the target platform (if given)

Never:
- add unsupported facts
- invent personal experiences
- change the author's position
- remove hedging ("may", "possibly")
- imitate exact passages from the persona's reference samples
- mention the persona in the output
- exceed ±20% of the original length unless asked

Style strength: <0-1，默认 0.7；0=保守调措辞，1=风格全开>

Persona:
<persona 文件全文>

Source text:
<原文>
```

执行要点：

- 以 persona 的 `## Sentence Style` / `## Paragraph Style` / `## Vocabulary` /
  `## Rhetorical Patterns` 为操作依据；`## Positive Examples` 是风格标尺，
  但**禁止照抄**它的句子
- 多平台（x / linkedin / email / blog / newsletter）时参考 persona 的
  `## Context Adaptation`
- 改写后按 STEP 4 自评；不达标（尤其保真）就重写一版

### STEP 4 — 评估（自评并报告）

```text
meaning_preservation  0-1  核心意思/立场是否不变
fact_integrity        0-1  数字/实体/日期/引用是否全保留，有无新增事实
style_match           0-1  句长/词汇/修辞/结构是否符合 persona
readability           0-1  是否自然可读
platform_fit          0-1  是否适配目标平台

final = 0.45×meaning + 0.30×style + 0.15×readability + 0.10×platform
```

- **meaning_preservation ≥ 0.9 是硬底线**，低于则重写
- 任何一处事实改动（数字/日期/实体）→ fact_integrity 直接判 0，必须修正
- 向用户报告分数与修改要点；风格强度可迭代：偏低就调高重写

## 从样本文本创建 Persona（六步）

用户提供样本文本时，你直接生成新 persona 文件：

```
1. 样本清理    去掉 HTML/Markdown 噪音、转发、引用他人的段落、重复、签名
2. 内容/风格分离 关键：区分「作者谈什么」与「作者怎么写」——"常谈 AI"不是写作风格
3. 风格抽取    tone 六维(0-1) + 句式/段落/修辞/词汇偏好/回避词
4. 草稿生成    按 PERSONA_SPEC.md 的 16 个章节生成 frontmatter + 正文
5. 正反例      每个主要特征配 1 个 Positive/1 个 Negative 示例（比形容词稳定）
6. 一致性测试  用 2-3 段无关文本自查：风格稳定、事实不丢
```

- 保存到 `personas/custom/<id>.md`（id 与文件名一致，kebab-case）
- **必须报告置信度**：样本 ≥300 词时，句长/直接度/段落节奏可信（0.8+）；
  幽默方式、长文结构、跨主题词汇不可信（<0.6）——如实告诉用户这些维度
  需要更多样本才能确定
- 命名用描述性名称（如 `Clear Product Thinker`），不要用真人姓名；
  若用户明确要"模仿某某"，用 `source_type: inspired` + disclaimer
- 生成后提示用户可自行编辑该 Markdown 文件

## 混合 Persona

用户要求混合（如 70% A + 30% B）时：

```
1. 读取各 persona 文件的 ## Tone Dimensions
2. 六维按权重加权平均（formality/warmth/confidence/humor/
   emotional_intensity/directness）
3. 词汇 Prefer/Avoid、句式、修辞按权重合并（保留高权重者的优先）
4. 用合成后的规范执行 STEP 3 改写
```

不要简单拼接两个 persona 的 Prompt——必须是合成后的单一 Profile。

## 铁律（任何时候）

1. 数字、实体、日期、链接、引用一个都不能改
2. 不新增原文没有的事实
3. 不改变作者立场；不删除不确定性措辞
4. 不虚构个人经历；输出中不提及 persona 名称
5. 不把口头禅堆砌当作风格；不机械套用同一种句式
6. 输出长度默认 ±20%

## 相关文件

```text
PERSONA_SPEC.md    Persona 文件规范（创建/编辑 persona 时必须遵守）
personas/          写作规范源文件（本 skill 的数据源）
CONTRIBUTING.md    贡献新 persona 的检查清单
```

> 进阶（可选，非必需）：仓库同时附带 Python CLI / FastAPI / Web 界面，
> 但本 skill 的核心用法就是你在对话内直接完成，无需任何环境配置。
