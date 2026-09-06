"""JDA本部サイトの公開候補に含める範囲を一元管理する。"""

from __future__ import annotations


ROOT_FILES = (
    "index.html",
    "performer.html",
    "workshop.html",
    "marquee-updates.txt",
    "sitemap.xml",
    "robots.txt",
)

COPY_TREES = (
    "css",
    "js",
    "images/champions",
    "external/about",
    "external/access",
    "external/certification",
    "external/champions",
    "external/contact",
    "external/dispatch",
    "external/news",
    "external/otp2",
    "external/records",
    "external/rule",
)

IMAGE_FILES = (
    "images/diaicon-white.png",
    "images/image-specs.txt",
    "images/logo/final_logo_emblem_v3.png",
    # champions.json に写真が無い年度のカード裏面。poker用のJPEGは公開しない。
    "images/poker/cardback.webp",
    "images/logo/midd.webp",
    "images/logo/wdc2026-logo-v2-light.png",
    "images/pickup/howtogo.webp",
    "images/pickup/oidc.webp",
    "images/pickup/regu.webp",
    "images/pickup/wdc2026-taipei-hero-bg.webp",
    "images/pickup/wdc2026-taipei-rain.webp",
)

# 制作リポジトリではローカルミラーを確認できる一方、本番候補では既存の
# 大会サイトを触らず、現在の本番URLへリンクする。
LIVE_LINK_REPLACEMENTS = {
    # 絶対URLにしておくことで、本番だけでなくGitHub Pagesや
    # release-candidateのローカル確認サーバーからも既存大会サイトへ到達できる。
    "external/AJDC/index.html": "https://diabolo.jp/AJDC/",
    "external/OIDC/index.html": "https://diabolo.jp/OIDC/",
    "external/TIDC/jp/index.html": "https://diabolo.jp/TIDC/jp/",
    "../AJDC/index.html": "https://diabolo.jp/AJDC/",
    "../OIDC/index.html": "https://diabolo.jp/OIDC/",
    "../TIDC/jp/index.html": "https://diabolo.jp/TIDC/jp/",
}

PRESERVED_LIVE_PREFIXES = ("/AJDC/", "/OIDC/", "/TIDC/")
FORBIDDEN_DIRECTORY_NAMES = {"AJDC", "OIDC", "TIDC", "wp", "champions-poker"}
FORBIDDEN_SUFFIXES = {".php", ".sql"}
FORBIDDEN_FILE_NAMES = {".htaccess", ".user.ini", "web.config"}
