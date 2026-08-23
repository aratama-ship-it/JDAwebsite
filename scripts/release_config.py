"""JDA本部サイトの公開候補に含める範囲を一元管理する。"""

from __future__ import annotations


ROOT_FILES = (
    "index.html",
    "performer.html",
    "workshop.html",
    "marquee-updates.txt",
)

COPY_TREES = (
    "css",
    "js",
    "images/champions",
    "images/logo",
    "images/pickup",
    "images/poker",
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
)

# 制作リポジトリではローカルミラーを確認できる一方、本番候補では既存の
# 大会サイトを触らず、現在の本番URLへリンクする。
LIVE_LINK_REPLACEMENTS = {
    "external/AJDC/index.html": "/AJDC/",
    "external/OIDC/index.html": "/OIDC/",
    "external/TIDC/jp/index.html": "/TIDC/jp/",
    "../AJDC/index.html": "/AJDC/",
    "../OIDC/index.html": "/OIDC/",
    "../TIDC/jp/index.html": "/TIDC/jp/",
}

PRESERVED_LIVE_PREFIXES = ("/AJDC/", "/OIDC/", "/TIDC/")
FORBIDDEN_DIRECTORY_NAMES = {"AJDC", "OIDC", "TIDC", "wp", "champions-poker"}
FORBIDDEN_SUFFIXES = {".php", ".sql"}
FORBIDDEN_FILE_NAMES = {".htaccess", ".user.ini", "web.config"}
