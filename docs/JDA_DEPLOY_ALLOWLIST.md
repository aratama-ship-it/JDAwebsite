# JDA本体 公開allowlist

確定日: 2026-08-22  
サーバー設定方針更新: 2026-09-03

## 目的

リポジトリ全体や旧docroot全体を公開せず、第1段階のJDA本体に必要なファイルだけを再現可能に抽出する。内部資料、作業データ、CHAMPIONS POKER、大会ミラー、未知のPHPや設定ファイルは公開候補へ混ぜない。

## 構成

- `deploy/jda-app.allowlist`: このリポジトリから公開するJDA本体HTML・CSS・JS・画像。
- `deploy/jda-legacy-assets.allowlist`: 検査済みの旧docrootから取り込むPDF 19本とMP3 1本。
- `deploy/jda-legacy-assets.sha256`: 内容確認済みの旧資産を固定するSHA-256。allowlistと1対1でなければ公開ビルドを止める。
- `deploy/jda-preserve-paths.txt`: パッケージには入れないが、切替時に消してはいけない大会・過去記事・現行サービスURL。
- `deploy/jda-legacy-never-copy.txt`: 旧環境には存在しても新JDA本体docrootへコピーしない既知のPHP・テスト環境・不審ファイル。
- `deploy/jda-denylist.txt`: 公開候補に混在したら検査を失敗させる内部資料、作業フォルダ、危険な拡張子。
- `scripts/check-jda-allowlist.py`: HTML/CSS/CHAMPIONS JSONと同一ドメインPDF/MP3を走査し、実行時依存がallowlistから漏れていないか確認する。
- `scripts/check-jda-legacy-integrity.py`: 旧資産allowlistとSHA-256の1対1対応、および実ファイルの内容一致を確認する。
- `scripts/build-jda-release.sh`: 2つのallowlistだけを新しい空の公開候補へコピーする。
- `scripts/verify-jda-release.sh`: 公開候補がallowlistと完全一致し、denylist・symlink・偽PDF/MP3を含まないことを検査する。

## 使い方

まずリポジトリ側の公開ファイルがすべて存在するか確認する。

```bash
scripts/build-jda-release.sh --check
```

本番サーバー調査後、承認済みの旧docrootスナップショットを用意して公開候補を作る。

```bash
scripts/build-jda-release.sh build/jda-release /path/to/approved-legacy-docroot
```

出力先が既に存在する場合は上書きせず停止する。旧docrootからはallowlist記載のPDF/MP3しかコピーしない。必要ファイルの不足、symlink、拡張子と実体の不一致、SHA-256不一致、予期しないファイル混在があれば失敗する。

最新の検定合格者PDF 4本は2026-08-22に公式`https://diabolo.jp/certification/`から取得し、構造・レンダリング・内容を確認してSHA-256を登録済み。旧資産allowlist 20本はすべてハッシュ照合対象になっている。

## 公開対象

- トップと通常下層10ページ。
- 共通CSS/JS、更新帯テキスト。
- ページから使用するロゴ、PICK UP、CHAMPIONS画像のみ。
- 静的フォールバック2ページ。`.htaccess` は通常公開から除外し、将来案を `server-config/proposals/clean-url-cutover.conf` に保管する。
- 新ページから参照する規則PDF、検定PDF、1分トラックMP3。

## 明示的な除外

- `PROJECT_NOTES.md`、`AGENTS.md`、`docs/`、各種メンテナンス資料。
- `work/`、`archive/`、`bfaseed-mock/`、成績CSV、PSD、ログ、`.DS_Store`。
- `external/`全体。CHAMPIONS POKERと大会ミラーを第1段階の本体パッケージに混ぜない。
- `OIDCphotos/`、POKER専用の選手JPEG、未使用素材。
- PHP、SQL、環境ファイル、未知のサーバー設定。
- `.htaccess`。新設・変更は通常公開とは分け、`server-config/README.md` に従う専用作業として扱う。

## 保全対象との関係

AJDC/OIDC/TIDC、過去イベント記事、オンラインコーチング等は、この本体パッケージから削除する対象ではない。`deploy/jda-preserve-paths.txt`に記録し、現行サーバー調査と安全性確認後に別途保全する。新しい空のdocrootへ切り替える場合、これらの保全が終わる前に本体パッケージだけで切り替えてはいけない。

過去イベントHTMLは画像・PDF等の依存関係が未棚卸しのため、今回の旧資産allowlistへ安易に追加していない。現行docrootを丸ごとコピーせず、次のサーバー調査で依存ファイルと安全性を確認してから個別に追加する。旧サーバーの読み取り監査結果は`docs/JDA_LEGACY_SERVER_AUDIT.md`を参照する。
