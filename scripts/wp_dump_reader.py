#!/usr/bin/env python3
"""phpMyAdmin が出力した SQL ダンプから、指定テーブルの行を読み出す。

DBへ復元せずにダンプを直接読むための最小限のパーサ。
- 対象は phpMyAdmin 4.0 系が出す `INSERT INTO ... VALUES (...),(...);` 形式。
- 値は数値・NULL・シングルクォート文字列（バックスラッシュエスケープ）のみを想定する。
  想定外の並びに当たったら黙って読み飛ばさず例外にする（欠落に気づけるようにするため）。
"""

from __future__ import annotations

import re
from pathlib import Path

INSERT_HEAD = re.compile(
    r"INSERT INTO `(?P<table>[^`]+)` \((?P<columns>[^)]*)\) VALUES\s*",
)

UNESCAPE = {
    "0": "\0",
    "b": "\b",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "Z": "\x1a",
    "\\": "\\",
    "'": "'",
    '"': '"',
    "%": "\\%",  # MySQL は \% \_ をそのまま残す
    "_": "\\_",
}


def _read_string(text: str, index: int) -> tuple[str, int]:
    """text[index] が開始クォートである前提で、文字列リテラルを1つ読む。"""
    assert text[index] == "'"
    index += 1
    parts: list[str] = []
    while True:
        char = text[index]
        if char == "\\":
            escaped = text[index + 1]
            parts.append(UNESCAPE.get(escaped, escaped))
            index += 2
        elif char == "'":
            if text[index + 1 : index + 2] == "'":  # '' も終端ではなく引用符
                parts.append("'")
                index += 2
            else:
                return "".join(parts), index + 1
        else:
            parts.append(char)
            index += 1


def _read_tuple(text: str, index: int) -> tuple[list, int]:
    assert text[index] == "("
    index += 1
    values: list = []
    while True:
        while text[index] in " \t\r\n":
            index += 1
        char = text[index]
        if char == "'":
            value, index = _read_string(text, index)
            values.append(value)
        elif char == ")":
            return values, index + 1
        else:
            match = re.compile(r"(NULL|-?[0-9]+(?:\.[0-9]+)?(?:e-?[0-9]+)?)", re.IGNORECASE).match(text, index)
            if not match:
                raise ValueError(f"解釈できない値: {text[index:index + 40]!r}")
            token = match.group(1)
            values.append(None if token.upper() == "NULL" else token)
            index = match.end()
        while text[index] in " \t\r\n":
            index += 1
        if text[index] == ",":
            index += 1
        elif text[index] == ")":
            return values, index + 1
        else:
            raise ValueError(f"区切りが不正: {text[index:index + 40]!r}")


def read_table(dump_text: str, table: str) -> list[dict]:
    """指定テーブルの全行を dict のリストで返す。"""
    rows: list[dict] = []
    for head in INSERT_HEAD.finditer(dump_text):
        if head.group("table") != table:
            continue
        columns = [name.strip().strip("`") for name in head.group("columns").split(",")]
        index = head.end()
        while True:
            while dump_text[index] in " \t\r\n":
                index += 1
            if dump_text[index] != "(":
                raise ValueError(f"{table}: タプルの開始が見つからない: {dump_text[index:index + 40]!r}")
            values, index = _read_tuple(dump_text, index)
            if len(values) != len(columns):
                raise ValueError(f"{table}: 列数が一致しない ({len(values)} != {len(columns)})")
            rows.append(dict(zip(columns, values)))
            while dump_text[index] in " \t\r\n":
                index += 1
            if dump_text[index] == ",":
                index += 1
                continue
            if dump_text[index] == ";":
                break
            raise ValueError(f"{table}: 文の終端が不正: {dump_text[index:index + 40]!r}")
    return rows


def load_dump(path: Path) -> str:
    """ダンプ全体を読む。

    Wordfence の IP ログなど一部のテーブルに生バイナリが入っており UTF-8 として不正なので、
    surrogateescape で読み込んで壊さずに素通しする（wp1_/wp2_ の本文には影響しない）。
    出力時は clean_text() で除去すること。
    """
    return path.read_text(encoding="utf-8", errors="surrogateescape")


def clean_text(value: str) -> str:
    """surrogateescape で残った非UTF-8バイトを除去する。"""
    return value.encode("utf-8", "replace").decode("utf-8")
