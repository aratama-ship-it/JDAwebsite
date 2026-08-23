# AGENTS.md

このプロジェクトではコンテキストを重視してください。まず `PROJECT_NOTES.md` を読んで、既存の方針・未対応事項・キャッシュバージョンを確認してから作業します。

## 作業ルール

- わからないこと、不明瞭な点があれば質問してください。
- 共通CSS/JSを変更したら、各HTMLの `style.css?v=` / `main.js?v=` を揃えて更新してください。
- AJDC/OIDC/TIDC の既存ミラーページは、後日別途作り直す予定です。現時点では欠損アセットや古いHTMLの修復対象にしません。
- 画像の元PNG/PSDや未使用素材は、明示的な削除指示がない限り削除しません。現行サイトで使わない素材は `archive/unused-assets/` に退避します。
- Codex、Claude Codeなど複数ツールで触る前提なので、作業前後に `git status --short` を確認し、関係ない変更を巻き戻さないでください。
- 制作途中は作業ブランチを使い、`main`へ直接pushしません。GitHubへのpushとCyberduckによる本番反映を別工程として扱ってください。
- 本番候補は手作業で寄せ集めず、`./scripts/prepare_release.sh` で `release-candidate/` に再生成します。このコマンドはアップロードを行いません。
- `release-candidate/public/` に `AJDC/`、`OIDC/`、`TIDC/`、`wp/`、`.htaccess` が含まれる状態では本番作業を中止してください。
