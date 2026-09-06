#!/usr/bin/env python3
"""diabolo.jp の正規URL統一を、適用の前後で同じ手順で実測する。

`server-config/proposals/canonical-host.conf` を .htaccess として設置する前と後に
実行し、出力を比べる。判定は「転送先が https://diabolo.jp に1回で着地するか」と
「壊してはいけない経路が壊れていないか」の2点。

使い方:
    python3 scripts/verify_canonical_host.py                 # 画面に出す
    python3 scripts/verify_canonical_host.py --save before   # 結果をJSONで残す
    python3 scripts/verify_canonical_host.py --compare before/after のJSON2つ
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULT_DIR = REPO_ROOT / "server-config" / "measurements"

CANONICAL = "https://diabolo.jp"

# 正規化の対象。すべて https://diabolo.jp/... へ寄るのが正解。
ORIGINS = (
    "http://diabolo.jp",
    "https://diabolo.jp",
    "http://www.diabolo.jp",
    "https://www.diabolo.jp",
)
PATHS = (
    "/",
    "/external/about/index.html",
    "/external/contact/index.html",
    "/performer.html",
    "/sitemap.xml",
    "/robots.txt",
)

# 壊してはいけない経路。転送先ホストが変わらないこと・200で着地することを見る。
MUST_NOT_BREAK = (
    ("https://diabolo.jp/AJDC/", "https://diabolo.jp/AJDC/"),
    ("https://diabolo.jp/OIDC/", "https://diabolo.jp/OIDC/"),
    ("https://diabolo.jp/TIDC/jp/", "https://diabolo.jp/TIDC/jp/"),
    ("https://judgearchive.diabolo.jp/", "https://judgearchive.diabolo.jp/"),
    ("http://judgearchive.diabolo.jp/", None),  # 転送されてもホストは判定アーカイブのまま
)

MAX_HOPS = 10
TIMEOUT = 15


class _Recorder(urllib.request.HTTPRedirectHandler):
    """転送の連鎖を記録するだけのハンドラ。"""

    def __init__(self) -> None:
        self.chain: list[tuple[int, str]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        self.chain.append((code, newurl))
        if len(self.chain) > MAX_HOPS:
            raise urllib.error.HTTPError(newurl, code, "転送が多すぎます（ループの疑い）", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def trace(url: str) -> dict:
    recorder = _Recorder()
    opener = urllib.request.build_opener(recorder)
    opener.addheaders = [("User-Agent", "jda-canonical-check/1.0")]
    try:
        with opener.open(url, timeout=TIMEOUT) as response:
            return {
                "url": url,
                "status": response.status,
                "final": response.geturl(),
                "hops": len(recorder.chain),
                "chain": [{"code": code, "to": to} for code, to in recorder.chain],
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "status": exc.code,
            "final": exc.url,
            "hops": len(recorder.chain),
            "chain": [{"code": code, "to": to} for code, to in recorder.chain],
            "error": str(exc.reason),
        }
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"url": url, "status": None, "final": None, "hops": 0, "chain": [], "error": str(exc)}


def run() -> dict:
    canonical_results = []
    for path in PATHS:
        for origin in ORIGINS:
            result = trace(origin + path)
            expected = CANONICAL + path
            result["expected"] = expected
            already_canonical = origin == CANONICAL
            result["ok"] = (
                result["final"] == expected
                and result["status"] == 200
                and result["hops"] <= (0 if already_canonical else 1)
            )
            canonical_results.append(result)
            time.sleep(0.15)

    preserved = []
    for url, expected_final in MUST_NOT_BREAK:
        result = trace(url)
        result["expected"] = expected_final
        host_kept = bool(result["final"]) and (
            expected_final is None
            or result["final"] == expected_final
        )
        if expected_final is None and result["final"]:
            host_kept = "judgearchive.diabolo.jp" in result["final"]
        result["ok"] = result["status"] == 200 and host_kept
        preserved.append(result)
        time.sleep(0.15)

    return {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "canonical": CANONICAL,
        "unification": canonical_results,
        "preserved": preserved,
    }


def show(report: dict) -> int:
    print(f"測定 {report['measured_at']} / 正規URL {report['canonical']}")
    print("\n## 正規化（すべて https://diabolo.jp へ1回で着地するのが正解）")
    unified = 0
    for item in report["unification"]:
        mark = "OK  " if item["ok"] else "NG  "
        if item["ok"]:
            unified += 1
        detail = f"{item['status']} hops={item['hops']} → {item['final']}"
        print(f"  {mark}{item['url']}\n        {detail}")

    print("\n## 壊してはいけない経路")
    intact = 0
    for item in report["preserved"]:
        mark = "OK  " if item["ok"] else "NG  "
        if item["ok"]:
            intact += 1
        print(f"  {mark}{item['url']}\n        {item['status']} hops={item['hops']} → {item['final']}")

    total_u, total_p = len(report["unification"]), len(report["preserved"])
    print(f"\n正規化: {unified}/{total_u}   維持: {intact}/{total_p}")
    if intact < total_p:
        print("FAIL: 壊してはいけない経路に異常があります。直ちに .htaccess を削除してください。")
        return 2
    if unified < total_u:
        print("未達: まだ統一されていない経路があります（適用前ならこれが正常）。")
        return 1
    print("PASS: 統一済み・維持も問題なし。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", metavar="NAME", help="結果をJSONで保存する（before / after 等）")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"), help="保存済みの2件を比較する")
    args = parser.parse_args()

    if args.compare:
        before, after = (json.loads(Path(p).read_text(encoding="utf-8")) for p in args.compare)
        print("## 変化した経路")
        index = {item["url"]: item for item in before["unification"] + before["preserved"]}
        changed = 0
        for item in after["unification"] + after["preserved"]:
            old = index.get(item["url"])
            if old and (old["final"], old["status"]) != (item["final"], item["status"]):
                changed += 1
                print(f"  {item['url']}")
                print(f"    前: {old['status']} → {old['final']}")
                print(f"    後: {item['status']} → {item['final']}")
        if not changed:
            print("  変化なし")
        return 0

    report = run()
    if args.save:
        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        target = RESULT_DIR / f"{args.save}.json"
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"saved: {target.relative_to(REPO_ROOT)}\n")
    return show(report)


if __name__ == "__main__":
    sys.exit(main())
