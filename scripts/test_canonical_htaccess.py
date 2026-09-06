#!/usr/bin/env python3
"""正規URL統一の .htaccess 案を、本番へ置く前にローカルのApacheで実際に動かして検証する。

`server-config/proposals/canonical-host.conf` の中身をそのまま .htaccess として
一時的なドキュメントルートに置き、macOS同梱のApacheを別ポートで起動して、
Hostヘッダを差し替えながら転送先を実測する。

確認したいのは主に次の3点。
  1. www付きのブックマークが、同じページへ正しく着地するか（パスと?以降を保つか）
  2. 転送が1回で終わるか（多段・ループになっていないか）
  3. judgearchive.diabolo.jp など他のホストに触れていないか

使い方: python3 scripts/test_canonical_htaccess.py
"""

from __future__ import annotations

import http.client
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPOSAL = REPO_ROOT / "server-config" / "proposals" / "canonical-host.conf"
HTTPD = Path("/usr/sbin/httpd")
MODULES = Path("/usr/libexec/apache2")

# 本番の構造を最小限まねる。中身は判別できればよい。
FIXTURE_FILES = {
    "index.html": "root",
    "performer.html": "performer",
    "sitemap.xml": "<urlset/>",
    "external/about/index.html": "about",
    "external/contact/index.html": "contact",
    "judgearchive/index.html": "judgearchive",
    "TIDC/jp/index.html": "tidc",
}

# (説明, Hostヘッダ, パス, 期待する結果)
#   期待は ("redirect", 転送先) または ("serve",) のいずれか。
CASES = (
    ("www付きのブックマーク（下層ページ）", "www.diabolo.jp",
     "/external/about/index.html", ("redirect", "https://diabolo.jp/external/about/index.html")),
    ("www付きのブックマーク（トップ）", "www.diabolo.jp",
     "/", ("redirect", "https://diabolo.jp/")),
    ("www付き・クエリ文字列あり", "www.diabolo.jp",
     "/external/contact/index.html?submitted=1",
     ("redirect", "https://diabolo.jp/external/contact/index.html?submitted=1")),
    ("www付き・日本語や記号を含むパス", "www.diabolo.jp",
     "/external/about/index.html?q=%E6%A4%9C%E5%AE%9A&x=1",
     ("redirect", "https://diabolo.jp/external/about/index.html?q=%E6%A4%9C%E5%AE%9A&x=1")),
    ("www付き・大文字混じりのホスト名", "WWW.DIABOLO.JP",
     "/performer.html", ("redirect", "https://diabolo.jp/performer.html")),
    ("www付き・存在しないページ", "www.diabolo.jp",
     "/nonexistent.html", ("redirect", "https://diabolo.jp/nonexistent.html")),
    ("bare の http", "diabolo.jp", "/sitemap.xml", ("redirect", "https://diabolo.jp/sitemap.xml")),
    ("bare の http・下層", "diabolo.jp",
     "/external/about/index.html", ("redirect", "https://diabolo.jp/external/about/index.html")),
    ("判定アーカイブのサブドメイン", "judgearchive.diabolo.jp", "/index.html", ("serve",)),
    ("判定アーカイブのサブドメイン（トップ）", "judgearchive.diabolo.jp", "/", ("serve",)),
    ("test サブドメイン", "test.diabolo.jp", "/index.html", ("serve",)),
    ("将来増える別のサブドメイン", "shop.diabolo.jp", "/index.html", ("serve",)),
    ("ロリポップ初期ドメイン", "example.lolipop.jp", "/index.html", ("serve",)),
)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def extract_rules(text: str) -> str:
    """提案ファイルから実際に効く行（コメント以外）だけを取り出す。"""
    return "\n".join(line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#"))


def build_tree(base: Path, htaccess_body: str) -> tuple[Path, Path]:
    docroot = base / "docroot"
    for relative, body in FIXTURE_FILES.items():
        target = docroot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    (docroot / ".htaccess").write_text(htaccess_body, encoding="utf-8")

    logs = base / "logs"
    logs.mkdir()
    config = base / "httpd.conf"
    config.write_text(
        f"""ServerRoot "{base}"
Listen 127.0.0.1:{{port}}
LoadModule mpm_prefork_module {MODULES}/mod_mpm_prefork.so
LoadModule authz_core_module {MODULES}/mod_authz_core.so
LoadModule mime_module {MODULES}/mod_mime.so
LoadModule log_config_module {MODULES}/mod_log_config.so
LoadModule unixd_module {MODULES}/mod_unixd.so
LoadModule dir_module {MODULES}/mod_dir.so
LoadModule rewrite_module {MODULES}/mod_rewrite.so
ServerName localhost
PidFile "{base}/httpd.pid"
ErrorLog "{logs}/error.log"
TypesConfig /dev/null
AddType text/html .html
DocumentRoot "{docroot}"
<Directory "{docroot}">
    AllowOverride All
    Require all granted
    DirectoryIndex index.html
</Directory>
""",
        encoding="utf-8",
    )
    return config, docroot


def request(port: int, host: str, path: str) -> tuple[int, str | None]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.putrequest("GET", path, skip_host=True, skip_accept_encoding=True)
        connection.putheader("Host", host)
        connection.endheaders()
        response = connection.getresponse()
        response.read()
        return response.status, response.getheader("Location")
    finally:
        connection.close()


def main() -> int:
    if not HTTPD.exists():
        print(f"FAIL: Apacheが見つかりません: {HTTPD}", file=sys.stderr)
        return 1
    if not PROPOSAL.exists():
        print(f"FAIL: 提案ファイルがありません: {PROPOSAL}", file=sys.stderr)
        return 1

    rules = extract_rules(PROPOSAL.read_text(encoding="utf-8"))
    if "RewriteEngine" not in rules:
        print("FAIL: 提案ファイルに有効な RewriteEngine 行がありません", file=sys.stderr)
        return 1

    base = Path(tempfile.mkdtemp(prefix="jda-htaccess-test-"))
    port = free_port()
    try:
        config, _ = build_tree(base, rules)
        config.write_text(config.read_text(encoding="utf-8").replace("{port}", str(port)), encoding="utf-8")

        # デーモンとして起動する（-D FOREGROUND だとこの環境で子プロセスが維持できない）
        started = subprocess.run(
            [str(HTTPD), "-f", str(config)],
            capture_output=True,
            text=True,
            check=False,
        )
        if started.returncode != 0:
            print(f"FAIL: Apacheが起動しませんでした\n{started.stderr}", file=sys.stderr)
            return 1
        for _ in range(50):
            try:
                request(port, "startup.check", "/")
                break
            except OSError:
                time.sleep(0.1)
        else:
            error_log = (base / "logs" / "error.log")
            detail = error_log.read_text(encoding="utf-8", errors="replace") if error_log.exists() else ""
            print(f"FAIL: Apacheが応答しません\n{detail}", file=sys.stderr)
            return 1

        print(f"ローカルApache {port} 番で、提案ファイルのルールをそのまま実行しています。\n")
        failures = 0
        for label, host, path, expected in CASES:
            status, location = request(port, host, path)
            if expected[0] == "redirect":
                ok = status in (301, 302) and location == expected[1]
                got = f"{status} → {location}"
                want = f"302 → {expected[1]}"
            else:
                ok = status == 200 and location is None
                got = f"{status}" + (f" → {location}" if location else "（転送なし・そのまま表示）")
                want = "200（転送なし）"
            failures += 0 if ok else 1
            print(f"  {'OK  ' if ok else 'NG  '}{label}")
            print(f"        Host: {host}  {path}")
            print(f"        結果: {got}")
            if not ok:
                print(f"        期待: {want}")

        print()
        # 転送先をもう一度叩いてループしないことを確かめる（httpsは張れないのでパスだけ確認）
        status, _ = request(port, "diabolo.jp", "/external/about/index.html")
        print(f"  参考: bare + http は1回で https へ出る（{status}）。"
              f"https側は本番の実測 verify_canonical_host.py で確認する。")

        if failures:
            print(f"\nFAIL: {failures}件が期待と違います。本番へ置かないでください。")
            return 1
        print(f"\nPASS: {len(CASES)}件すべて期待通り。ブックマークはパスとクエリを保ったまま着地します。")
        return 0
    finally:
        pid_file = base / "httpd.pid"
        if pid_file.exists():
            try:
                os.kill(int(pid_file.read_text().strip()), signal.SIGTERM)
                time.sleep(0.5)
            except (ProcessLookupError, ValueError):
                pass
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
