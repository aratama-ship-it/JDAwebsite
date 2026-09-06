#!/usr/bin/env python3
"""2012-2016年の日本ディアボロ協会公式ブログを、SQLダンプから読めるHTMLへ書き出す。

背景: このブログのファイルはサーバーから削除済みで、記事本文はデータベースの
wp1_/wp2_ テーブルにしか残っていない（2026-09-06 に旧サイト保全50,380ファイルと
本番URLを調べて確認）。DBへ復元しなくても読める形にして保全するのが目的。

入力: backups/2026-09-06_wp5-drop/LAA0217648-test.sql（Git非追跡）
出力: archive/2012-2016-jda-blog/（Git追跡。本番の公開候補には入らない）

使い方: python3 scripts/build_blog_archive.py [--skip-images]
"""

from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wp_dump_reader import clean_text, load_dump, read_table  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DUMP = REPO_ROOT / "backups" / "2026-09-06_wp5-drop" / "LAA0217648-test.sql"
OUTPUT = REPO_ROOT / "archive" / "2012-2016-jda-blog"

BLOGS = {
    "wp2_": {"label": "公式ブログ", "path": "/Weblog", "note": "2013年7月に移行した後継ブログ。過去記事も取り込まれている。"},
    "wp1_": {"label": "旧公式ブログ", "path": "/JDA_Weblog", "note": "最初のブログ。2013年7月に /Weblog へ移行して役目を終えた。"},
}

# 本文で実際に使われていたタグだけを通す（実測: b, img, div, wbr, span, a, em, strong）。
ALLOWED_TAGS = {
    "a", "b", "blockquote", "br", "div", "em", "h2", "h3", "h4", "i",
    "img", "li", "ol", "p", "span", "strong", "u", "ul", "wbr",
}
ALLOWED_ATTRS = {"href", "src", "alt", "title", "width", "height"}

WAYBACK_API = "https://archive.org/wayback/available?url="


def sanitize(content: str) -> str:
    """許可したタグ・属性だけを残す。style と target は落とし、危険なURLは無効化する。"""

    def replace_tag(match: re.Match) -> str:
        closing, name, rest = match.group(1), match.group(2).lower(), match.group(3)
        if name not in ALLOWED_TAGS:
            return ""
        if closing:
            return f"</{name}>"
        attributes = []
        for attr in re.finditer(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"', rest):
            key, value = attr.group(1).lower(), attr.group(2)
            if key not in ALLOWED_ATTRS:
                continue
            if key in {"href", "src"} and not re.match(r"^(https?:|mailto:|images/|#)", value.strip(), re.I):
                continue
            attributes.append(f'{key}="{html.escape(value, quote=True)}"')
        selfclose = "/" if name in {"br", "img", "wbr"} else ""
        return f"<{name}{' ' if attributes else ''}{' '.join(attributes)}{selfclose}>"

    cleaned = re.sub(r"<\s*(/?)\s*([a-zA-Z0-9]+)([^>]*)>", replace_tag, content)
    return cleaned


def wpautop(content: str) -> str:
    """WordPressの表示と同じく、空行を段落・単独改行を <br> にする。"""
    text = content.replace("\r\n", "\n").strip()
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    paragraphs = []
    for block in blocks:
        if re.match(r"^\s*<(div|p|ul|ol|blockquote|h[234])\b", block, re.I):
            paragraphs.append(block)
        else:
            paragraphs.append("<p>" + block.replace("\n", "<br />\n") + "</p>")
    return "\n".join(paragraphs)


def normalize_title(title: str) -> str:
    return re.sub(r"[\s　\-–—]+", "", title).lower()


def collect(dump: str) -> dict:
    result = {}
    for prefix in BLOGS:
        posts = read_table(dump, prefix + "posts")
        terms = {t["term_id"]: clean_text(t["name"]) for t in read_table(dump, prefix + "terms")}
        taxonomy = {
            t["term_taxonomy_id"]: (t["taxonomy"], terms.get(t["term_id"], ""))
            for t in read_table(dump, prefix + "term_taxonomy")
        }
        categories: dict[str, list[str]] = {}
        for link in read_table(dump, prefix + "term_relationships"):
            kind, name = taxonomy.get(link["term_taxonomy_id"], ("", ""))
            if kind in {"category", "post_tag"} and name:
                categories.setdefault(link["object_id"], []).append(name)
        published = []
        for post in posts:
            if post["post_status"] != "publish" or post["post_type"] not in {"post", "page"}:
                continue
            published.append(
                {
                    "source": prefix,
                    "id": post["ID"],
                    "date": clean_text(post["post_date"]),
                    "title": clean_text(post["post_title"]).strip(),
                    "type": post["post_type"],
                    "categories": sorted(set(categories.get(post["ID"], []))),
                    "url": clean_text(post["guid"]),
                    "content": clean_text(post["post_content"]),
                }
            )
        published.sort(key=lambda item: item["date"])
        result[prefix] = published
    return result


def pair_old_versions(entries: dict) -> list[dict]:
    """後継ブログ(wp2_)を本編とし、旧ブログ(wp1_)の同じ記事を別版として紐づける。"""
    remaining = list(entries["wp1_"])
    timeline = []
    for post in entries["wp2_"]:
        same_day = [old for old in remaining if old["date"][:10] == post["date"][:10]]
        best = None
        if same_day:
            best = max(
                same_day,
                key=lambda old: difflib.SequenceMatcher(
                    None, normalize_title(old["title"]), normalize_title(post["title"])
                ).ratio(),
            )
            ratio = difflib.SequenceMatcher(
                None, normalize_title(best["title"]), normalize_title(post["title"])
            ).ratio()
            if ratio < 0.6:
                best = None
        record = dict(post)
        if best is not None:
            remaining.remove(best)
            record["old_version"] = best if best["content"].strip() != post["content"].strip() else None
            record["also_in_old_blog"] = True
        else:
            record["old_version"] = None
            record["also_in_old_blog"] = False
        timeline.append(record)
    for leftover in remaining:  # 後継ブログへ移らなかった記事（固定ページ等）
        record = dict(leftover)
        record["old_version"] = None
        record["also_in_old_blog"] = False
        timeline.append(record)
    timeline.sort(key=lambda item: item["date"])
    return timeline


def fetch_wayback_images(timeline: list[dict], skip: bool) -> dict:
    """本文が参照する画像を Wayback Machine から取得し、ローカルへ保存する。"""
    sources: list[str] = []
    for post in timeline:
        for text in (post["content"], (post["old_version"] or {}).get("content", "")):
            sources.extend(re.findall(r'<img[^>]+src="([^"]+)"', text))
    unique = sorted(set(sources))
    mapping: dict[str, dict] = {}
    if skip:
        return {url: {"status": "未取得", "local": None} for url in unique}
    image_dir = OUTPUT / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    for url in unique:
        local_name = re.sub(r"[^A-Za-z0-9._-]", "_", url.split("/")[-1]) or "image.jpg"
        target = image_dir / local_name
        if target.exists() and target.stat().st_size > 0:
            mapping[url] = {"status": "取得済み(既存)", "local": f"images/{local_name}"}
            continue
        try:
            with urllib.request.urlopen(WAYBACK_API + url, timeout=30) as response:
                snapshot = json.load(response).get("archived_snapshots", {}).get("closest")
        except (urllib.error.URLError, ValueError, TimeoutError):
            snapshot = None
        if not snapshot:
            mapping[url] = {"status": "元URL・アーカイブとも消失", "local": None}
            continue
        # id_ を付けると Wayback の枠を挟まない原本が返る
        raw = snapshot["url"].replace("/http", "id_/http", 1)
        try:
            with urllib.request.urlopen(raw, timeout=60) as response:
                data = response.read()
        except (urllib.error.URLError, TimeoutError):
            mapping[url] = {"status": "アーカイブ取得失敗", "local": None, "wayback": snapshot["url"]}
            continue
        if not data.startswith((b"\xff\xd8", b"\x89PNG", b"GIF8")):
            mapping[url] = {"status": "画像として不正", "local": None, "wayback": snapshot["url"]}
            continue
        target.write_bytes(data)
        mapping[url] = {
            "status": "Wayback Machineから復元",
            "local": f"images/{local_name}",
            "wayback": snapshot["url"],
            "captured": snapshot.get("timestamp", ""),
            "bytes": len(data),
        }
        time.sleep(0.4)
    return mapping


def rewrite_images(content: str, mapping: dict) -> str:
    def replace(match: re.Match) -> str:
        tag, url = match.group(0), match.group(1)
        info = mapping.get(url)
        if info and info.get("local"):
            return tag.replace(url, info["local"])
        return tag
    return re.sub(r'<img[^>]+src="([^"]+)"', replace, content)


def render_body(post: dict, mapping: dict) -> str:
    return wpautop(sanitize(rewrite_images(post["content"], mapping)))


JP_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def japanese_date(value: str) -> str:
    match = JP_DATE.match(value)
    if not match:
        return value
    year, month, day = match.groups()
    return f"{year}年{int(month)}月{int(day)}日"


def render_html(timeline: list[dict], mapping: dict, generated: str) -> str:
    years = sorted({post["date"][:4] for post in timeline})
    nav = "\n".join(
        f'          <li><a href="#y{year}">{year}<span aria-hidden="true">年</span></a></li>' for year in years
    )
    articles = []
    current_year = None
    for post in timeline:
        year = post["date"][:4]
        if year != current_year:
            current_year = year
            articles.append(f'      <h2 class="year" id="y{year}">{year}<span class="year-suffix">年</span></h2>')
        blog = BLOGS[post["source"]]
        categories = "".join(
            f'<span class="tag">{html.escape(name)}</span>' for name in post["categories"] if name != "未分類"
        )
        old = ""
        if post.get("old_version"):
            old = (
                '\n        <details class="old-version">'
                f'\n          <summary>旧ブログ（{html.escape(BLOGS["wp1_"]["path"])}）の版を見る'
                "<span>— 移行時に本文が書き換えられています</span></summary>"
                f'\n          <div class="post-body">{render_body(post["old_version"], mapping)}</div>'
                "\n        </details>"
            )
        page_badge = '<span class="badge">固定ページ</span>' if post["type"] == "page" else ""
        articles.append(
            f"""      <article class="post" id="post-{post['source']}{post['id']}">
        <div class="meta">
          <time datetime="{post['date'][:10]}">{japanese_date(post['date'])}</time>
          <span class="origin">{html.escape(blog['path'])}</span>{page_badge}
        </div>
        <h3 class="post-title">{html.escape(post['title'])}</h3>
        {f'<div class="tags">{categories}</div>' if categories else ''}
        <div class="post-body">{render_body(post, mapping)}</div>{old}
      </article>"""
        )
    restored = sum(1 for info in mapping.values() if info.get("local"))
    image_rows = "\n".join(
        f"          <tr><td><code>{html.escape(url)}</code></td><td>{html.escape(info['status'])}</td></tr>"
        for url, info in sorted(mapping.items())
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>日本ディアボロ協会 公式ブログ アーカイブ 2012–2016</title>
<style>
:root {{
  --bg: #ffffff;
  --bg-soft: #f6f6f7;
  --rule: #e3e3e6;
  --text: #15151a;
  --muted: #55555d;
  --red: #db0a40;
  --red-deep: #c8103a;
  --font: 'Helvetica Neue', 'Hiragino Sans', 'Yu Gothic', Arial, sans-serif;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{ background: var(--bg); color: var(--text); font-family: var(--font); line-height: 1.9; }}
a {{ color: var(--red-deep); }}
.skip-link {{ position: absolute; left: 16px; top: -100px; z-index: 20; background: var(--red); color: #fff;
  padding: 12px 20px; border-radius: 0 0 6px 6px; text-decoration: none; font-weight: 700; }}
.skip-link:focus {{ top: 0; }}
.page {{ max-width: 1080px; margin: 0 auto; padding: 0 24px 96px; }}
header.hero {{ padding: 72px 0 40px; border-bottom: 2px solid var(--text); }}
.kicker {{ font-size: 13px; letter-spacing: .18em; color: var(--red-deep); font-weight: 700; }}
h1 {{ font-size: clamp(28px, 5vw, 44px); line-height: 1.35; margin: 12px 0 20px; letter-spacing: .01em; }}
.lede {{ color: var(--muted); font-size: 15px; max-width: 62ch; }}
.facts {{ display: flex; flex-wrap: wrap; gap: 8px 32px; margin-top: 28px; font-size: 14px; }}
.facts div {{ min-width: 128px; }}
.facts dt {{ color: var(--muted); font-size: 12px; letter-spacing: .08em; }}
.facts dd {{ font-weight: 700; font-size: 19px; }}
.layout {{ display: grid; grid-template-columns: 148px minmax(0, 1fr); gap: 48px; margin-top: 48px; }}
nav.rail {{ position: sticky; top: 24px; align-self: start; font-size: 14px; }}
nav.rail p {{ font-size: 12px; letter-spacing: .1em; color: var(--muted); margin-bottom: 12px; }}
nav.rail ul {{ list-style: none; }}
nav.rail a {{ display: block; padding: 7px 0; border-bottom: 1px solid var(--rule); text-decoration: none;
  color: var(--text); font-weight: 700; }}
nav.rail a:hover, nav.rail a:focus {{ color: var(--red-deep); }}
nav.rail span {{ font-weight: 400; font-size: 12px; color: var(--muted); margin-left: 2px; }}
.year {{ font-size: 34px; letter-spacing: .02em; margin: 64px 0 8px; padding-bottom: 8px;
  border-bottom: 2px solid var(--red); }}
.year:first-of-type {{ margin-top: 0; }}
.year-suffix {{ font-size: 15px; color: var(--muted); margin-left: 6px; }}
.post {{ padding: 36px 0; border-bottom: 1px solid var(--rule); }}
.meta {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; font-size: 13px; color: var(--muted); }}
.origin {{ background: var(--bg-soft); padding: 2px 8px; border-radius: 3px; font-size: 12px; }}
.badge {{ background: var(--red-deep); color: #fff; padding: 2px 8px; border-radius: 3px; font-size: 12px; }}
.post-title {{ font-size: 22px; line-height: 1.5; margin: 8px 0 12px; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }}
.tag {{ font-size: 12px; color: var(--red-deep); border: 1px solid var(--rule); border-radius: 999px; padding: 2px 12px; }}
.post-body {{ font-size: 16px; }}
.post-body p, .post-body div {{ margin-bottom: 1em; }}
.post-body img {{ max-width: 100%; height: auto; margin: 12px 0; border: 1px solid var(--rule); }}
.old-version {{ margin-top: 20px; background: var(--bg-soft); border-left: 3px solid var(--rule); padding: 12px 18px; }}
.old-version summary {{ cursor: pointer; font-size: 14px; font-weight: 700; }}
.old-version summary span {{ font-weight: 400; color: var(--muted); margin-left: 6px; }}
.old-version .post-body {{ margin-top: 16px; font-size: 15px; color: var(--muted); }}
.notes {{ margin-top: 72px; padding: 28px 32px; background: var(--bg-soft); font-size: 14px; }}
.notes h2 {{ font-size: 17px; margin-bottom: 14px; }}
.notes h3 {{ font-size: 14px; margin: 20px 0 6px; }}
.notes ul {{ margin-left: 20px; }}
.notes table {{ border-collapse: collapse; margin-top: 8px; width: 100%; font-size: 13px; }}
.notes td {{ border-bottom: 1px solid var(--rule); padding: 6px 8px; vertical-align: top; }}
.notes code {{ font-size: 12px; word-break: break-all; }}
footer {{ margin-top: 40px; font-size: 13px; color: var(--muted); }}
@media (max-width: 760px) {{
  .layout {{ grid-template-columns: 1fr; gap: 24px; }}
  nav.rail {{ position: static; }}
  nav.rail ul {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  nav.rail a {{ border: 1px solid var(--rule); border-radius: 999px; padding: 8px 16px; min-height: 44px;
    display: flex; align-items: center; }}
}}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
</style>
</head>
<body>
<a class="skip-link" href="#archive">記事一覧へ移動</a>
<div class="page">
  <header class="hero">
    <p class="kicker">保全アーカイブ・非公開</p>
    <h1>日本ディアボロ協会 公式ブログ<br>2012–2016</h1>
    <p class="lede">サーバーからファイルが失われ、データベースにだけ残っていた協会公式ブログの記事を、
    読める形に復元したものです。大会告知、採点規則の改定、アジアカップの結果報告など、
    現行サイトの「更新情報」より前の活動記録にあたります。</p>
    <dl class="facts">
      <div><dt>記事数</dt><dd>{len(timeline)}</dd></div>
      <div><dt>期間</dt><dd>{timeline[0]['date'][:4]}–{timeline[-1]['date'][:4]}</dd></div>
      <div><dt>復元した画像</dt><dd>{restored} / {len(mapping)}</dd></div>
      <div><dt>作成日</dt><dd>{generated}</dd></div>
    </dl>
  </header>
  <div class="layout">
    <nav class="rail" aria-label="年で移動">
      <p>年で移動</p>
      <ul>
{nav}
      </ul>
    </nav>
    <main id="archive">
{chr(10).join(articles)}
      <section class="notes">
        <h2>このアーカイブについて</h2>
        <h3>出典</h3>
        <ul>
          <li>データベース <code>LAA0217648-test</code> の全体エクスポート（2026年9月6日 01:13 取得）に含まれる
              <code>wp1_posts</code>・<code>wp2_posts</code> ほかのテーブル。</li>
          <li>公開状態（<code>publish</code>）の投稿と固定ページだけを収録し、下書き・ゴミ箱・リビジョンは除いた。</li>
        </ul>
        <h3>2つのブログの関係（確認済みの事実）</h3>
        <ul>
          <li><code>/JDA_Weblog</code>（<code>wp1_</code>／「日本ディアボロ協会公式ブログ」）が最初のブログ。</li>
          <li>2013年7月8日の記事「ブログを移行しました」により <code>/Weblog</code>（<code>wp2_</code>）へ移り、
              過去記事も日付を保ったまま取り込まれた。以後2016年6月まで更新されている。</li>
          <li>移行時に本文が書き直された記事があるため、差分がある場合は旧版も各記事内に併記した。</li>
        </ul>
        <h3>画像の状態</h3>
        <p>本文が参照していた画像は、元のURLではすべて消失していた（404もしくは配信停止）。
        Wayback Machine に残っていたものを取得して <code>images/</code> に保存し、本文の参照先を差し替えている。</p>
        <table>
{image_rows}
        </table>
        <h3>表示のために加えた処理</h3>
        <ul>
          <li>本文は実際に使われていたタグ（<code>a, b, div, em, img, span, strong, wbr</code>）だけを通し、
              <code>style</code> 属性と未知のタグは除いた。内容の文字は変えていない。</li>
          <li>WordPress と同じく、空行を段落・単独改行を改行タグとして表示している。</li>
        </ul>
        <h3>未解決の注意点</h3>
        <ul>
          <li><code>wp2_users</code> に <code>wp.service.controller.LNook</code> ・
              <code>wp.service.controller.AzORp</code> という管理者権限のアカウントが2つある。
              メールアドレスが空、登録日時が <code>0000-00-00</code> で、通常の作成手順では生まれない。
              <strong>このブログが第三者に侵入されていた可能性が高い（未確定）。</strong>
              稼働中の <code>/AJDC/</code>・<code>/OIDC/</code> には同種のアカウントは無いことを確認済み。</li>
          <li>記事本文には外部への不審なリンクは含まれていなかった（全リンクの宛先を確認済み）。</li>
        </ul>
      </section>
      <footer>
        <p>このファイルはローカル確認用です。本番サイトへは公開されません。
        機械可読の正本データは同じフォルダの <code>posts.json</code>、生成手順は
        <code>scripts/build_blog_archive.py</code>。</p>
      </footer>
    </main>
  </div>
</div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-images", action="store_true", help="Wayback Machineへの取得を行わない")
    args = parser.parse_args()

    if not DUMP.exists():
        print(f"FAIL: ダンプが見つかりません: {DUMP}", file=sys.stderr)
        return 1

    dump = load_dump(DUMP)
    entries = collect(dump)
    timeline = pair_old_versions(entries)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    mapping = fetch_wayback_images(timeline, args.skip_images)

    generated = time.strftime("%Y年%-m月%-d日")
    (OUTPUT / "index.html").write_text(render_html(timeline, mapping, generated), encoding="utf-8")
    (OUTPUT / "posts.json").write_text(
        json.dumps(
            {
                "source": "LAA0217648-test.sql (2026-09-06 01:13 取得)",
                "tables": ["wp1_posts", "wp2_posts"],
                "images": mapping,
                "posts": timeline,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("PASS: ブログアーカイブを生成しました")
    print(f"output: {OUTPUT}")
    print(f"posts: {len(timeline)}（旧版併記 {sum(1 for p in timeline if p.get('old_version'))}件）")
    print(f"images: {sum(1 for i in mapping.values() if i.get('local'))}/{len(mapping)} 復元")
    return 0


if __name__ == "__main__":
    sys.exit(main())
