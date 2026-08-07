# Persona Specification（PERSONA_SPEC）

本文档定义 Persona Library 的 Persona 文件规范。所有社区贡献的 Persona 必须遵守本规范，并通过 `scripts/lint-personas.py` 校验。

---

## 1. 文件约定

- 一个 Persona 对应一个 Markdown 文件，文件名即 `id`（小写 kebab-case）。
- 文件由 **Frontmatter（YAML 元数据）** + **Markdown 正文（Persona 规格）** 组成。
- 存放于 `personas/<category>/<id>.md`。
- 源文件使用 Markdown；运行时格式为 JSON（由 loader 解析生成）。

## 2. Frontmatter 元数据

```yaml
---
id: pragmatic-founder              # 必填，kebab-case，与文件名一致
name: Pragmatic Founder            # 必填，展示名称
description: 一句话描述             # 必填，≤ 120 字符
category: founders                 # 必填，必须是 categories.json 中的 id
language:                          # 必填，ISO 639-1 列表
  - en
  - zh
emoji: 🚀                          # 必填，单个 emoji
version: 1.0.0                     # 必填，语义化版本
author: community                  # 必填
license: MIT                       # 必填
tags:                              # 推荐，来自 categories.json 的 tag_dimensions
  - concise
  - product-focused
  - analytical
source_type: archetype             # 必填：archetype | user-created | sample-derived | brand | inspired
style_strength_default: 0.7        # 可选，0–1，默认 0.7
disclaimer: >                      # 可选，source_type=inspired 时必填
  该 Persona 仅概括泛化的风格特征，不代表或代指任何真实个人。
---
```

## 3. 正文章节（顺序固定）

| 章节 | 必填 | 内容 |
|---|---|---|
| `## Identity` | ✅ | 你是谁、以什么方式表达；**不是角色扮演**，而是表达框架 |
| `## Perspective` | ✅ | 看待内容的角度（用户价值、证据、杠杆……） |
| `## Voice Summary` | ✅ | 2–4 个形容词概括语气 |
| `## Tone Dimensions` | ✅ | 6 个 0–1 数值维度，格式见下 |
| `## Sentence Style` | ✅ | 句式偏好（句长、语态、主从句、结论位置） |
| `## Paragraph Style` | ✅ | 段落长度、开头方式、列表使用 |
| `## Vocabulary` | ✅ | `### Prefer` / `### Avoid` 两组词语列表 |
| `## Rhetorical Patterns` | ✅ | 3–5 个修辞/论证模式 |
| `## Signature Moves` | ✅ | 标志性动作（具体、可检验） |
| `## Anti-Patterns` | ✅ | 禁止行为（写成 `Never:` 列表） |
| `## Content Preservation Rules` | ✅ | 改写时的内容保真规则（编号列表） |
| `## Transformation Rules` | ✅ | 改写时的转换规则（编号列表） |
| `## Positive Examples` | ✅ | ≥ 2 个 `### Example N`：`Input:` / `Output:` 引用块 |
| `## Negative Examples` | ✅ | ≥ 1 个 `### Example N`：`Input:` 引用块 + `Reason:` 说明 |
| `## Context Adaptation` | ✅ | ≥ 2 个场景（Social Post / Long-form Article / Email / Docs…） |
| `## Evaluation Rubric` | ✅ | 1–5 分评分维度列表 |

### 3.1 Tone Dimensions 格式（机器可解析）

```markdown
## Tone Dimensions

- Formality: 0.45
- Warmth: 0.45
- Confidence: 0.85
- Humor: 0.15
- Emotional intensity: 0.30
- Directness: 0.90
```

六个维度必须全部出现且数值 ∈ [0, 1]。

### 3.2 Vocabulary 格式（机器可解析）

```markdown
## Vocabulary

### Prefer
- useful
- practical

### Avoid
- revolutionary
- game-changing
```

### 3.3 Examples 格式

```markdown
## Positive Examples

### Example 1

Input:

> 原文……

Output:

> 改写后……

## Negative Examples

### Example 1

Input:

> 禁止出现的写法……

Reason:

该写法……（说明为什么失败）
```

## 4. 机器可解析字段（Loader 提取）

Loader 从正文中提取以下字段进入 `StyleProfile`：

- `tone` ← `## Tone Dimensions`（6 个数值）
- `voice_summary` ← `## Voice Summary` 段落文本
- `preferred_vocabulary` / `avoided_vocabulary` ← `## Vocabulary` 下两个子节
- `rhetorical_patterns` ← `## Rhetorical Patterns` 的 bullet 列表
- `anti_patterns` ← `## Anti-Patterns` 的 bullet 列表
- `sentence_patterns`、`paragraph_patterns`、`signature_moves` ← 对应章节 bullet 列表
- `positive_examples` / `negative_examples` ← 按 3.3 约定解析

其余内容（Identity、Perspective、Transformation Rules 等）以原始 Markdown 注入运行时 prompt。

## 5. 质量要求（贡献检查）

1. 至少 3 个可区分的风格特征，且每个特征有证据或示例支撑
2. **必须区分「内容」与「风格」**——不能把「作者常谈 AI」当作写作风格
3. 至少 5 段无关原文测试通过：事实/实体/数字/日期不变，不新增事实
4. 不依赖口头禅堆砌
5. 与现有 Persona 有可辨识差异（`scripts/check-originality.py` 检查）
6. 内容保真权重最高；风格可以激进，事实不能动

## 6. 命名规范

- 使用描述性名称（`Keynote Product Visionary`），**不使用真人姓名**（`Steve Jobs Persona`）。
- 如需致敬历史公共作者，`source_type: inspired` 并附 `disclaimer`。

## 7. 校验

```bash
python scripts/lint_personas.py            # 全量校验
python scripts/lint_personas.py personas/founders/my-new-persona.md   # 单个校验
python scripts/check_originality.py personas/founders/my-new-persona.md
python scripts/test_persona.py my-new-persona
```
