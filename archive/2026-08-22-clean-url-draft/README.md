# 2026-08-22 クリーンURL版の下書き

2026-08-22に、下層ページを `/external/about/` から **`/about/`** のようなクリーンURLへ
移す構成で作られた一式。ルート直下に10フォルダを置いていた。

## なぜ退避したか

**本番も制作の正本も `external/` 構成のまま進んだため、この一式は使われないまま古くなった。**

- キャッシュ番号が `style.css?v=60` / `main.js?v=37` で止まっている（現行は v=75 / v=42）
- 2026年8月末以降の変更（WDC 2026のヒーロー演出、チャンピオン写真の差し替え、
  アクセシビリティ対応）がすべて入っていない
- Git管理外のまま置かれていたため、`prepare_release.sh --require-clean` が常に失敗していた

## 固有の価値は残っていない

この版だけが持っていた `meta description`・favicon・`theme-color`・スキップリンク・
`<main>` は、2026-09-04にPR #11で現行の `external/*` へ移植済み（8ページすべてで一致を確認）。
`aria-expanded` は現行版のほうが多い（11箇所 対 10箇所）。

`docs/JDA_RELEASE_REVIEW.md` は当時「動きを停止/再開」ボタンを実装済みと記録しているが、
**この下書きにも現行版にも実装は存在しない**（2026-09-04に両方をgrepして確認）。記録側の誤り。

## クリーンURLへ移る場合

この古いHTMLを使わず、現行の `external/*` から作り直すこと。移行の計画自体は残してある。

- URL対応表: `docs/JDA_URL_REDIRECT_MAP.md`
- 301転送の案: `server-config/proposals/clean-url-cutover.conf`
- 本番の公開ルートの状態: `server-config/production-state.json`

旧デプロイ系（`deploy/jda-app.allowlist`、`scripts/build-jda-release.sh` 等）も
このクリーンURL構成を前提にしている。現行の公開は `scripts/prepare_release.sh` を使う。
