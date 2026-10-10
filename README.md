# code-as-linus

> "Bad programmers worry about the code. Good programmers worry about data structures and their relationships."
> — Linus Torvalds

一个 AI Agent Skill：让大语言模型像 Linus Torvalds 一样写代码——极简、务实、直击本质。

## 核心信条

- **数据结构至上**：数据结构选对了，代码自己会长对。
- **好品味**：不写处理边界的 `if/else`，而是设计让边界不存在的数据结构。特例归零。
- **拒绝过度抽象**：不要工厂，不要包装层，嵌套最多 3 层，贴近金属。
- **Fail-fast**：错误前置、提前 return、清理集中。
- **少废话**：Talk is cheap. Show me the code.

## 目录

| 路径 | 作用 |
| --- | --- |
| `skill.yaml` | 模型参数、提示词与工具的统一配置 |
| `prompts/system_prompt.md` | Linus 风格系统提示词，强制三段式输出 |
| `prompts/language_rules/python_rules.md` | Python 专属降级与约束 |
| `examples/linked_list.md` | Few-shot：链表删除的 Bad Taste vs Good Taste |
| `tools/linter.py` | 嵌套缩进检查器，上限 3 层 |

## 使用

将 `prompts/system_prompt.md` 作为 system prompt 加载；按目标语言追加 `language_rules/` 下的规则；用 `examples/` 中的示例做 few-shot。

提交代码前运行品味检查：

```bash
python tools/linter.py --file your_code.py
# 或直接传入代码字符串
python tools/linter.py --code $'def f():\n    if x:\n        ...'
# 或从标准输入
cat your_code.py | python tools/linter.py
```

检查通过退出码为 0；缩进超过 3 层时拒绝通过，退出码为 1，并输出固定文案：

> 代码没有 Linus 的好品味，缩进过深，请重构并消除嵌套

检查器以 Python 语法为准（`tokenize` 与 `ast` 两条路径）：非 Python 源码解析不了时，它如实报告解析失败，而不是谎称"缩进过深"。

## Linus 名言

- "Talk is cheap. Show me the code." —— Linus Torvalds
- "Bad programmers worry about the code. Good programmers worry about data structures and their relationships." —— Linus Torvalds
- "if you need more than 3 levels of indentation, you're screwed anyway, and should fix your program." —— 《Linux kernel coding style》第 1 章，本技能 3 层上限的出处
