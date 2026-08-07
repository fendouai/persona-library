# Contributing

感谢你愿意为 Persona Library 贡献 Persona！规范请先阅读 [PERSONA_SPEC.md](PERSONA_SPEC.md)。

## 提交流程

1. 在 `personas/<category>/` 下新建 `<persona-id>.md`，文件名即 id（kebab-case）
2. 本地校验通过后再提 PR：

```bash
python scripts/lint_personas.py personas/<category>/<persona-id>.md
python scripts/check_originality.py personas/<category>/<persona-id>.md
python scripts/test_persona.py <persona-id>
```

3. 在 PR 描述中附上完整 Checklist（见下）

## Persona PR Checklist

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

## 评审标准

- **拒绝**：泛化的「换皮」模板；把作者题材误当风格；只有口头禅没有结构特征；无法通过 lint。
- **接受**：风格特征可辨识、有示例证据、内容保真规则完整、与现有 Persona 有显著差异。

## 命名

- 使用描述性名称（`Keynote Product Visionary`），**不要**使用真人姓名。
- 如需致敬公共历史作者：`source_type: inspired` + `disclaimer`。

## 其他贡献

- 修 bug / 加功能：在 `src/persona_lib/` 下修改，补 `tests/` 测试
- Prompt 改进：编辑 `prompts/*.md`
- 文档：README.md / PERSONA_SPEC.md / 本文件

## CI（建议）

```yaml
steps:
  - run: python scripts/lint_personas.py
  - run: python scripts/check_originality.py personas/**/*.md
  - run: python -m pytest tests/ -q
```
