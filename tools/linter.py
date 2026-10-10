#!/usr/bin/env python3
"""
Linus 好品味检查器
==================
输入一段 Python 代码字符串，检查其嵌套层级是否超过 3 层。
两条检查路径互为补充，一条看缩进，一条看语法结构：
1. tokenize：按 INDENT/DEDENT 流统计真实语法缩进，括号内换行对齐不会误判；
2. ast：定位嵌套最深的块（重点盯 if 嵌套），elif 链不额外计层。
任一路径发现层级超标，即输出固定拒绝文案并以非零码退出；
若代码根本无法解析为 Python，则如实报告解析失败——不谎称"缩进过深"。

用法：
    python linter.py --file path/to/code.py
    python linter.py --code "code string"
    type code.py | python linter.py        # Windows
    cat code.py | python linter.py         # Unix
"""

from __future__ import annotations

import argparse
import ast
import io
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

# SSOT：嵌套层级上限只在此声明一次，两条检查路径共用
MAX_DEPTH = 3
# 层级超标的固定拒绝文案，调用方据此匹配
TASTE_ERROR = "代码没有 Linus 的好品味，缩进过深，请重构并消除嵌套"

# 会在语法上引入新一层缩进的块节点
_BLOCK_NODES = (
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
    ast.For, ast.AsyncFor, ast.While, ast.If,
    ast.With, ast.AsyncWith, ast.Try, ast.ExceptHandler,
)


@dataclass
class LintResult:
    """检查结果：ok 为 True 表示通过，否则 message 给出违规定位。"""

    ok: bool
    message: str = ""


def check_token_indent(code: str) -> LintResult:
    """用词法分析器的 INDENT/DEDENT 流统计真实语法缩进深度。"""
    try:
        return _scan_indent(tokenize.generate_tokens(io.StringIO(code).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        return LintResult(False, f"代码无法通过词法解析：{exc}")


def _scan_indent(token_stream) -> LintResult:
    """边遍历 token 边维护当前深度，一旦超标立即定位并返回。"""
    depth = 0
    for token in token_stream:
        depth = _next_depth(depth, token)
        if depth > MAX_DEPTH:
            return LintResult(False, _too_deep(token.start[0], depth, "缩进"))
    return LintResult(True)


def _next_depth(depth: int, token) -> int:
    """INDENT 加一层，DEDENT 减一层；非法代码可能减到负数，钳到 0 容错。"""
    if token.type == tokenize.INDENT:
        return depth + 1
    if token.type == tokenize.DEDENT:
        return max(0, depth - 1)
    return depth


def _too_deep(lineno: int, depth: int, what: str) -> str:
    """层级超标的统一文案：固定拒绝语 + 精确定位。"""
    return f"{TASTE_ERROR}\n第 {lineno} 行附近{what}达 {depth} 层"


def check_ast_depth(code: str) -> LintResult:
    """遍历 AST 找出最深嵌套块；elif 是 if.orelse 中的单个 If，不另计层级。"""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return LintResult(False, f"代码无法解析（语法错误）：{exc}")
    depth, lineno = _walk(tree, depth=0, deepest=(0, 0))
    if depth > MAX_DEPTH:
        return LintResult(False, _too_deep(lineno, depth, "块嵌套"))
    return LintResult(True)


def _walk(node: ast.AST, depth: int, deepest: tuple[int, int]) -> tuple[int, int]:
    """深度优先遍历，维护并返回 (目前最深层级, 对应行号)。"""
    for child in ast.iter_child_nodes(node):
        child_depth = depth + _block_increment(node, child)
        if child_depth > deepest[0] and getattr(child, "lineno", 0):
            deepest = (child_depth, child.lineno)
        deepest = _walk(child, child_depth, deepest)
    return deepest


def _block_increment(parent: ast.AST, child: ast.AST) -> int:
    """子块是否引入新缩进层；父 if 的唯一 orelse 子节点是 elif，不增层。"""
    if not isinstance(child, _BLOCK_NODES):
        return 0
    is_elif = (
        isinstance(parent, ast.If)
        and len(parent.orelse) == 1
        and parent.orelse[0] is child
    )
    return 0 if is_elif else 1


def lint(code: str) -> LintResult:
    """检查主入口：词法缩进与 AST 嵌套任一不过，即判定没有好品味。"""
    for check in (check_token_indent, check_ast_depth):
        result = check(code)
        if not result.ok:
            return result
    return LintResult(True, "通过：结构扁平，有 Linus 的好品味")


def _read_code(args: argparse.Namespace) -> str:
    """按 --code 优先、--file 次之、stdin 兜底的顺序取得待检查代码。"""
    if args.code is not None:
        return args.code
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    return sys.stdin.read()


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：检查通过返回 0，拒绝返回 1，便于接入提交钩子。"""
    parser = argparse.ArgumentParser(description="Linus 好品味缩进检查器")
    parser.add_argument("--file", "-f", help="待检查的源码文件路径")
    parser.add_argument("--code", "-c", help="直接传入待检查的代码字符串")
    args = parser.parse_args(argv)

    result = lint(_read_code(args))
    print(result.message)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
