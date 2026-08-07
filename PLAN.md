# Persona Library — 完整系统方案

> 一个开放的写作 Persona 模板库：可创建、管理、组合，并应用于文本改写的写作人格模板库。

---

## 一、项目定位

**Persona Library** 是一个开放的写作 Persona 模板集合，核心能力：

1. 浏览现有 Persona
2. 选择 Persona 改写文本
3. 从样本文本自动创建新的 Persona
4. 手动编辑 Persona
5. 混合多个 Persona
6. 对改写结果进行内容保真与风格匹配评估
7. 导出到 ChatGPT、Claude、Codex、OpenCode 等工具

### 与 `agency-agents` 的区别

| | agency-agents | 本项目 |
|---|---|---|
| 关注点 | 这个 Agent **会做什么工作** | 这个 Persona **如何表达同一段内容** |
| 模板重点 | Mission、交付物、工作流、指标 | 视角、语言/句法特征、修辞习惯、改写约束 |
| 复用机制 | 按 division 安装 Agent | 按类别/标签组合 Persona |

### 借鉴继承（模板规范层）

- 一个 Persona 一个 Markdown 文件
- Frontmatter 管理元数据（可被脚本解析）
- Markdown 正文保存 Persona Prompt（人机都友好，可转 JSON/YAML/TOML，可直接注入 system prompt）
- 提供转换与安装脚本

---

## 二、核心体验

### 应用体验

```text
选择一个 Persona
        ↓
输入原始文本
        ↓
调整风格强度
        ↓
生成符合该 Persona 的版本
```

### 创建体验

```text
输入作者样本文本
        ↓
分析语言风格
        ↓
生成 Persona 草稿
        ↓
用户编辑确认
        ↓
保存为 Persona 模板
```

---

## 三、Persona 文件规范（PERSONA_SPEC）

### 3.1 文件结构

一个 Persona = 一个 Markdown 文件 = Frontmatter（元数据）+ 正文（规格）。

```markdown
---
id: pragmatic-tech-founder
name: Pragmatic Tech Founder
description: 直接、清晰、以产品结果为导向的科技创业者表达方式
category: founder
language:
  - en
  - zh
emoji: 🚀
version: 1.0.0
author: community
license: MIT
tags:
  - concise
  - product-focused
  - analytical
source_type: archetype        # archetype | user-created | sample-derived | brand | inspired
style_strength_default: 0.7
---

# Pragmatic Tech Founder

## Identity
## Perspective
## Voice Summary
## Tone Dimensions
## Sentence Style
## Paragraph Style
## Vocabulary（Prefer / Avoid）
## Rhetorical Patterns
## Signature Moves
## Anti-Patterns
## Content Preservation Rules
## Transformation Rules
## Positive Examples（Input → Output）
## Negative Examples（+ Reason）
## Context Adaptation（Social Post / Long-form Article / Email）
## Evaluation Rubric
```

### 3.2 三层架构

| 层 | 内容 | 用途 |
|---|---|---|
| **Metadata** | id、name、category、tags、languages、version | 搜索、展示、过滤 |
| **Style Profile** | tone 数值维度、句式/段落特征、偏好与禁止模式 | 量化、混合、对比 |
| **Runtime Instructions** | 保真规则、改写规则、反模式 | 真正执行改写 |

三层可分别演进：Metadata 可搜索，Style Profile 可量化，Runtime Instructions 可执行。

### 3.3 命名规范

不使用「Steve Jobs Persona」，使用描述性名称：`Keynote Product Visionary`、`First-Principles Tech Founder`。

- 避免暗示可精确复制真人
- 避免输出虚构的个人经历/观点
- 便于抽象成可复用表达方法

公共领域历史作者可保留人物参考，但需标注：

```yaml
source_type: inspired
disclaimer: >
  This persona captures broad stylistic characteristics and does not
  represent or speak on behalf of the referenced individual.
```

### 3.4 分类系统

一级类别：`Archetypes` `Founders` `Educators` `Writers` `Creators` `Journalists` `Marketers` `Brands` `Professional` `Social` `Academic` `Custom`

多维标签：

```yaml
tone:       [concise, warm, authoritative]
structure:  [story-driven, analytical, list-driven]
platform:   [x, linkedin, email, blog, academic]
```

按「人物类型」或「表达需求」两种路径均可查找。

---

## 四、数据模型

以 Markdown 为源文件、JSON 为运行时格式。

```python
from typing import Literal
from pydantic import BaseModel, Field


class ToneDimensions(BaseModel):
    formality: float = Field(ge=0, le=1)
    warmth: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    directness: float = Field(ge=0, le=1)
    humor: float = Field(ge=0, le=1)
    emotional_intensity: float = Field(ge=0, le=1)


class StyleProfile(BaseModel):
    voice_summary: str
    tone: ToneDimensions
    sentence_patterns: list[str]
    paragraph_patterns: list[str]
    rhetorical_patterns: list[str]
    preferred_vocabulary: list[str]
    avoided_vocabulary: list[str]
    signature_moves: list[str]
    anti_patterns: list[str]
    positive_examples: list[dict[str, str]]
    negative_examples: list[dict[str, str]]


class Persona(BaseModel):
    id: str
    name: str
    description: str
    category: str
    languages: list[str]
    version: str
    source_type: Literal["archetype", "user-created", "sample-derived", "brand", "inspired"]
    profile: StyleProfile
    content_preservation_rules: list[str]
    transformation_rules: list[str]
```

---

## 五、系统架构

### 5.1 Persona 创建 Pipeline（六步）

```text
用户样本文本
    ↓
1. 样本清理        （去 HTML/Markdown 噪音、转发、引文、重复、签名）
    ↓
2. 内容与风格分离   （区分「作者谈什么」与「作者怎么写」——关键步骤）
    ↓
3. 风格特征抽取     （tone / syntax / structure / rhetoric / lexicon / content_behavior）
    ↓
4. Persona 草稿生成 （按统一规范输出 Markdown）
    ↓
5. 正反例生成       （Positive / Negative / Before-After 示例，比抽象形容词更稳定）
    ↓
6. 一致性测试       （5–10 段不同体裁文本改写，检查风格稳定、原意不变、无乱加事实）
```

**置信度机制（差异化能力）**：300 字样本足以判断句长、直接度，但不足以判断幽默方式、长文结构。系统必须显式输出：

```text
High confidence:  Sentence length / Directness / Paragraph rhythm
Low confidence:   Humor pattern / Long-form structure / Topic-independent vocabulary
```

### 5.2 改写 Pipeline（三阶段）

MVP 可退化为单次调用，正式版使用三阶段：

```text
Source Text
    ↓
① Content Extractor      → Semantic Constraints（claims / entities / numbers / position / uncertainties）
    ↓
② Persona Rewriter × N  → 2–4 个候选（输入：原文 + 内容约束 + Persona + 风格强度 + 输出平台）
    ↓
③ Judges                → Style Judge + Meaning Judge（保真 / 风格 / 可读性 / 平台适配）
    ↓
Best Candidate
```

### 5.3 Persona 混合

不做 Prompt 拼接，先加权合成临时 Profile（tone 取加权均值、pattern 按权重合并），再执行改写。

```json
{ "personas": [ { "id": "pragmatic-founder", "weight": 0.7 },
                { "id": "warm-educator", "weight": 0.3 } ] }
```

---

## 六、Prompt 设计

### 6.1 Persona 抽取 Prompt

```text
You are a writing-style analyst.

Analyze the supplied writing samples and create a reusable persona profile.
Separate topic-specific content from topic-independent writing style.

Extract:
1. Voice summary  2. Tone dimensions  3. Sentence patterns
4. Paragraph structure  5. Vocabulary preferences  6. Rhetorical patterns
7. Opening and closing patterns  8. Signature techniques
9. Anti-patterns  10. Content-preservation rules
11. Positive examples  12. Negative examples

For every major conclusion:
- provide supporting evidence from the samples
- estimate confidence from 0 to 1

Do not identify or speculate about protected personal characteristics.
Do not invent biographical information.
Do not treat the author's subject matter as writing style.
Return valid structured JSON.
```

### 6.2 改写 Prompt

```text
Rewrite the source text using the supplied persona.

Priority order:
1. Preserve meaning
2. Preserve facts, entities, numbers, citations, and uncertainty
3. Apply the persona's structural patterns
4. Apply sentence rhythm and vocabulary
5. Adapt to the requested platform

Do not:
- add unsupported facts
- invent personal experiences
- change the author's position
- imitate exact passages from reference samples
- exaggerate stylistic quirks
- mention the persona in the output

Style strength: {{style_strength}}
Target platform: {{platform}}
Target length: {{target_length}}

Persona:
{{persona}}

Source text:
{{source_text}}
```

---

## 七、质量评估体系（项目成败关键）

防退化（「在所有句子里加口头禅」）的三类检查：

| 评分 | 检查项 |
|---|---|
| **内容保真** | 数字/实体/日期不变、观点不变、不确定性未删、无新增事实 |
| **风格匹配** | 句长、段落、词汇层级、语气、修辞模式、开头/结尾、无禁止表达 |
| **过度模仿** | 无固定口头禅重复、无机械句式、无虚构个人故事、无模板化结构、可读性未受损 |

```text
Final Score =
  0.45 × Meaning Preservation
+ 0.30 × Style Match
+ 0.15 × Readability
+ 0.10 × Platform Fit
```

内容保真权重最高，是硬底线。

---

## 八、API 设计

```http
POST /v1/personas/extract      # 样本创建（返回 draft + confidence + warnings）
POST /v1/personas              # 手动创建
GET  /v1/personas              # 列表（category/tags 过滤）
GET  /v1/personas/{id}         # 详情
POST /v1/rewrite
```

```json
// POST /v1/rewrite
{
  "persona_id": "my-founder-voice",
  "text": "Original text...",
  "style_strength": 0.75,
  "platform": "x",
  "preserve_length": true,
  "candidate_count": 3
}

// 响应
{
  "output": "Rewritten text...",
  "scores": { "meaning_preservation": 0.96, "style_match": 0.84, "readability": 0.89 },
  "alternatives": []
}
```

---

## 九、CLI 设计

```bash
persona list                        # 查看 Persona
persona list --category founder     # 按类别
persona show pragmatic-founder      # 详情
persona create --from samples.txt   # 从样本创建
persona create --interactive        # 手动创建
persona rewrite article.md --persona pragmatic-founder --strength 0.8
persona rewrite article.md --persona pragmatic-founder --output rewritten.md
persona export pragmatic-founder --tool claude | --tool codex | --format json
persona install pragmatic-founder --tool claude | --tool codex
```

---

## 十、仓库结构

```text
persona-library/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── PERSONA_SPEC.md
├── categories.json
├── personas/
│   ├── archetypes/
│   │   ├── pragmatic-founder.md
│   │   ├── warm-educator.md
│   │   └── investigative-journalist.md
│   ├── creators/
│   ├── brands/
│   ├── professional/
│   └── personal/
├── schemas/
│   ├── persona.schema.json
│   ├── style-profile.schema.json
│   └── rewrite-request.schema.json
├── prompts/
│   ├── extract-persona.md
│   ├── rewrite-with-persona.md
│   ├── evaluate-style.md
│   └── evaluate-fidelity.md
├── examples/
│   ├── samples/
│   └── rewrite-results/
├── src/
│   ├── loader.py
│   ├── extractor.py
│   ├── rewriter.py
│   ├── evaluator.py
│   ├── registry.py
│   └── cli.py
├── tests/
│   ├── test_schema.py
│   ├── test_rewrite_fidelity.py
│   └── test_persona_consistency.py
├── scripts/
│   ├── lint-personas.py
│   ├── build-index.py
│   ├── check-originality.py
│   ├── test-persona.py
│   └── convert.py
└── dist/
    ├── personas.json
    └── registry.json
```

---

## 十一、社区贡献机制

借鉴 `agency-agents` 的验收思路：拒绝泛化、换皮式模板。

### Persona PR Checklist

```markdown
## Persona Information
**Name**:
**Category**:
**Language**:
**Intended Use**:

## Evidence
- [ ] Includes at least 3 style characteristics
- [ ] Includes evidence or examples for each major characteristic
- [ ] Separates subject matter from writing style
- [ ] Includes positive examples
- [ ] Includes negative examples
- [ ] Includes anti-patterns
- [ ] Includes content-preservation rules

## Testing
- [ ] Tested on at least 5 unrelated source texts
- [ ] Preserves facts and entities
- [ ] Does not add fictional personal experiences
- [ ] Does not rely only on catchphrases
- [ ] Is meaningfully different from existing personas
```

配套脚本：`lint-personas.py`（规范校验）、`check-originality.py`（与现有 Persona 查重）、`test-persona.py`（一致性测试）。

---

## 十二、技术栈与 MVP

### 技术栈

```text
Backend:   FastAPI + Pydantic
Frontend:  Next.js
Storage:   Git repository + SQLite（FTS / tag 索引）
LLM:       OpenAI / Anthropic / Gemini 兼容接口
Parser:    Python frontmatter + Markdown
```

### MVP 功能（六个，不做重）

1. 20 个高质量 Persona Markdown 模板
2. Persona 浏览与搜索
3. 从文本抽取 Persona
4. Persona 编辑器
5. 文本改写
6. 内容保真与风格评分

### MVP 流程

```text
用户粘贴样本文本 → Extractor 生成 JSON Profile → 转 Markdown Persona
→ 用户编辑 → 保存 → 应用到其他文本
```

---

## 十三、演进路线

| 版本 | 能力 | 说明 |
|---|---|---|
| **V1 Prompt Persona** | 结构化 Prompt | 实现最快、模型无关、易开源易贡献 |
| **V2 Persona Embedding** | 风格向量 | 相似搜索、重复检测、聚类、混合、自动推荐 |
| **V3 小模型风格迁移** | LoRA / Adapter / Prompt tuning | 用用户样本生成训练数据；后期能力，非 MVP 起点 |

---

## 十四、里程碑规划

| 阶段 | 内容 | 验收标准 |
|---|---|---|
| **M1 规范与库** | PERSONA_SPEC、分类系统、20 个 Persona、lint/索引脚本 | schema 校验全绿，20 个 Persona 通过一致性测试 |
| **M2 核心流水线** | loader / extractor / rewriter / evaluator + CLI | 从 3 段样本生成 Persona；改写不改变事实 |
| **M3 API + 前端** | FastAPI + Next.js，浏览/编辑/改写界面 | MVP 六项功能可用 |
| **M4 评估与社区** | 评分体系落地、PR Checklist、CI | 保真度 0.45 权重的综合评分上线 |
| **M5 混合与导出** | Persona 混合、export/install 到各工具 | 混合 Profile 合成正确 |

---

## 十五、最终原则

产品结构 = 借鉴（模板规范、目录分类、Frontmatter、安装转换、社区贡献、版本管理）
          + 创新（Persona Style Schema、样本风格抽取、自动创建、保真评估、风格一致评估、Persona 混合）

**三件最优先做扎实的事：**

1. **Persona 文件规范** —— 一切的基础
2. **从样本自动生成 Persona** —— 差异化所在
3. **不改变原意的前提下应用 Persona** —— 成败关键

这三部分稳定后，扩充数量、社区贡献、桌面应用与多工具安装都是自然延伸。比收集 500 个 Persona 更重要。
