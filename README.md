# Persona Library — 写作人格 Skill

> 零配置的 AI Agent 写作人格 Skill：把仓库装进 agent 的 skills 目录，agent 就能
> 浏览 Persona、按人格改写文本、从你的文章提取文风、混合多种语气——**事实一个都不许动**。

这个项目是一个 **Agent Skill**（`SKILL.md` 是入口，`personas/` 是数据源）。
**不需要配置 LLM、不需要 API Key、不需要 Python、不需要起服务**——你的
agent（Codex / Claude Code / opencode 等）本身就是 LLM，它读取
`personas/*.md` 作为写作规范，在对话内直接完成所有工作。

```text
用户：「帮我用创始人语气改写这段话」
  ↓
agent 读取 SKILL.md → 定位 pragmatic-founder → 内容锁定 → 直接改写 → 保真自评
  ↓
输出：改写结果 + 保真/风格评分
```

## 一、安装（30 秒，零依赖）

把本仓库链接到你 agent 的 skills 目录，**目录名必须叫 `persona-library`**
（与 SKILL.md 的 frontmatter name 一致）：

```bash
git clone <本仓库地址> persona-library && cd persona-library

# 任选其一（按你用的 agent）：
ln -s "$PWD" ~/.agents/skills/persona-library          # opencode 通用目录
ln -s "$PWD" ~/.config/opencode/skills/persona-library # opencode
ln -s "$PWD" ~/.claude/skills/persona-library          # Claude Code
ln -s "$PWD" ~/.codex/skills/persona-library           # Codex
ln -s "$PWD" .opencode/skills/persona-library          # 项目级（跟随仓库走）
```

> Windows 用 `mklink /J` 目录链接，或直接复制目录。
> 安装后**重启 agent**，让 skill 被扫描加载。

### 验证

新开一个 agent 会话，输入：

```
用 pragmatic-founder 的语气改写：「这个产品很好用。」
```

预期：agent 读取 SKILL.md → 找到 `personas/archetypes/pragmatic-founder.md`
→ 直接改写并报告保真/风格评分。无任何环境报错即安装成功。

## 二、用法示例（全部由 agent 直接执行）

| 你想做什么 | 对 agent 说 | 行为 |
|---|---|---|
| 按人格改写 | 「帮我用 warm-educator 的语气把这段产品介绍改写得更亲切」 | 读 persona → 锁定事实 → 改写 → 评分 |
| 去 AI 味 | 「humanize 这段，别让它像 AI 写的」 | 匹配 `concise-tech-creator` 或 `honest-personal-blogger` → 改写 |
| 提取文风 | 「这是我 3 篇专栏，帮我提取我的写作风格存成 persona」 | 六步抽取 → 生成 `personas/custom/<id>.md` → 报告置信度 |
| 混合语气 | 「70% 创始人口气 + 30% 老师的语气，改写这段话」 | 读取两个 persona → 加权合成 Profile → 改写 |
| 保真检查 | 「看看这次改写有没有改掉事实」 | 对照原文逐项核数字/实体/日期 → 评分 |

### 示例对话

**改写：**
```
你：帮我把这封邮件改得像一个温暖的老师写的。
agent：我选择 warm-educator（温暖/比喻/循序渐进）。
      改写结果：……
      评分：meaning 0.97 · style 0.86 · readability 0.92
      数字与日期原样保留，风格强度 0.7，需要更浓可以调高。
```

**提取文风：**
```
你：这是我的 3 篇文章，提取我的文风。
agent：已生成 personas/custom/my-voice.md。
      置信度：句长 0.91（高）· 直接度 0.88（高）
             幽默 0.42（低）· 长文结构 0.40（低）
      建议：多提供几篇 500 词以上的长文，可提升低置信维度。
```

## 三、工作流（agent 遵循 SKILL.md 执行）

```text
STEP 1 定位 Persona   用文件工具浏览 personas/**/*.md 的 frontmatter 与 Tone Dimensions
STEP 2 内容锁定       提取事实主张/实体/数字/立场/不确定性——改写前必做
STEP 3 改写           persona 文件全文作为写作规范注入，直接执行（见 SKILL.md 内联模板）
STEP 4 评估           final = 0.45×保真 + 0.30×风格 + 0.15×可读 + 0.10×平台
```

**铁律**：数字/实体/日期/链接/引用不动 · 不新增事实 · 不改立场 ·
不删不确定性 · 不虚构个人经历 · 不口头禅堆砌 · 长度 ±20%。

## 四、仓库内容

```text
├── SKILL.md              # skill 入口：description / 触发词 / 四步工作流 / 内联改写模板 / 铁律
├── PERSONA_SPEC.md       # Persona 文件规范（agent 创建/编辑 persona 时遵循）
├── personas/             # 20 个写作规范源文件（Markdown，即 skill 的数据源）
│   ├── archetypes/       #   pragmatic-founder / warm-educator / investigative-journalist…
│   ├── creators/         #   concise-tech-creator / story-first-essayist / viral-creator…
│   ├── brands/           #   minimalist-saas-brand / bold-d2c-brand / institutional-trust…
│   ├── professional/     #   executive / analyst / customer-success / academic-researcher…
│   └── personal/         #   calm-reflective / witty-social / direct / empathetic-coach…
├── CONTRIBUTING.md       # 贡献新 persona 的检查清单
├── prompts/              # LLM Prompt 模板（供进阶工具复用）
├── schemas/              # JSON Schema
├── src/persona_lib/      # 进阶工具：Python CLI（可选，非必需）
├── app/main.py           # 进阶工具：FastAPI（可选）
├── web/                  # 进阶工具：Next.js 界面（可选）
├── scripts/              # 进阶工具：lint / build-index / originality-check
├── tests/                # 进阶工具：pytest（24 项）
└── dist/                 # 进阶工具：构建索引
```

## 五、进阶工具（可选，skill 核心用法不需要）

### CLI

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
persona list                          # 浏览
persona show warm-educator            # 详情
persona extract --from samples.txt --name "My Voice" --save
persona rewrite article.md --persona pragmatic-founder --strength 0.8 --platform x
persona mix mix.json
persona export pragmatic-founder --tool claude
```

> CLI/API 的抽取与改写走 OpenAI 兼容接口，需要 `OPENAI_API_KEY`。
> 这是**可选增强**——skill 本体在对话内直接完成，与它无关。

### Web

```bash
.venv/bin/uvicorn app.main:app --port 8000     # 后端
cd web && npm install && npm run dev           # 前端 http://localhost:3000
```

## 六、贡献

- 新增 Persona：在 `personas/<category>/` 下写 Markdown，遵循
  [PERSONA_SPEC.md](PERSONA_SPEC.md)（16 章节 + frontmatter），对照
  [CONTRIBUTING.md](CONTRIBUTING.md) 的检查清单
- 校验：`python scripts/lint_personas.py`、`python scripts/check_originality.py <文件>`
- 你的 Persona 会被所有安装了本 skill 的 agent 直接使用——**质量要求：风格特征有
  证据支撑、正反例具体、与现有 Persona 有可辨识差异**

## License

MIT
