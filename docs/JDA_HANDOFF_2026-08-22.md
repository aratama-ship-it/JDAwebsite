# JDA本体公開作業 引き継ぎ

更新日: 2026-08-22

> **履歴資料:** この文書の件数と検証結果は2026-08-22時点のスナップショット。2026-09-03の確認では本番公開ルートに `.htaccess` は存在せず、通常公開から除外する方針へ更新した。現行方針は `server-config/README.md` を参照する。

## 再開時に最初にすること

1. Codexのロリポップログイン画面を開く。
2. パスワード等はチャットへ書かず、ユーザーが画面上で直接ログインする。
3. ログイン後、チャットに「ログインしました」と送る。
4. Codexは設定を変更せず、下記の「管理画面で読み取る項目」だけを確認する。

現在のロリポップ管理画面はログアウト状態。本番サーバー、DNS、独自ドメイン、公開フォルダ、FTP、DBにはまだ変更を加えていない。

## 現在地

JDA本体の静的コード、公開対象の抽出、安全な公開パッケージ生成までは完了。公開判定はまだNO-GO。現在進めているのは「本番サーバーの保全、バックアップ、切替・ロールバック方法の確定」。

### 完了済み

- 通常ページを`/about/`等のクリーンURLへ整理。
- 既知の旧URL301を`.htaccess`へ実装。
- JDA本体54ファイル＋旧静的資産20ファイルのallowlistを作成。
- PHP、内部資料、作業フォルダ、大会ミラー等を公開候補から除外。
- 旧docrootを丸ごとコピーしない方針を確定。
- 旧サーバーバックアップ約50,245ファイル、PHP約26,725本を読み取り調査。
- 不審な旧`sitemap.xml`、旧`send.php`、`test/`、`wp/`を新JDA本体へ持ち込まない方針を確定。
- 最新の検定合格者PDF 4本を公式`diabolo.jp`から取得。
- 旧資産19 PDF＋1 MP3のSHA-256を登録し、ビルド前後の照合を必須化。
- 74ファイルだけの公開パッケージ生成試験に合格。
- ロリポップ向け切替・ロールバック手順を作成。

### 直近の検証結果

```text
OK: verified SHA-256 for 20 legacy assets
OK: allowlists cover runtime dependencies (54 app files, 20 legacy assets)
OK: SHA-256 manifest covers 20 legacy assets
OK: release matches the allowlist (74 files)
```

承認済み旧資産の入力場所:

```text
work/jda-approved-legacy-docroot/
```

## 管理画面で読み取る項目

変更や保存ボタンは押さず、表示内容を確認する。

- 契約プランと契約期限
- Web・メール・DBの使用量と空き容量
- `diabolo.jp`の現在の公開（アップロード）フォルダ
- `www.diabolo.jp`の設定と公開フォルダ
- サブドメイン一覧と各公開フォルダ
- FTPSサーバー名と接続元IP制限の有無
- バックアップオプションの契約状態と復元可能日
- MySQLデータベース一覧とAJDC/OIDCに対応するDB
- cron、PHPバージョン、WAF、アクセス制限

アカウント名、パスワード、DBパスワード、秘密鍵等は資料やチャットへ転記しない。

## 管理画面確認後の順番

1. 現行WebファイルとAJDC/OIDCのDBを同じ時点でバックアップ。
2. 現行バックアップとローカル`JDA web`の差分を確認。
3. 新しい公開候補フォルダ名を決定。
4. AJDC/OIDC/TIDCと過去記事を同URLで残す保全方法を決定。
5. 74ファイルのJDA本体releaseと、承認済み保全パッケージを新フォルダへ配置。
6. 一時URLで検証してから公開フォルダだけを切り替える。
7. 問題時は旧公開フォルダへ戻す。

独自ドメイン設定の解除、DNS変更、メール設定変更は行わない。

## その後に残る公開前作業

1. HTTPからHTTPSへの転送と正規ホスト統一。
2. 正規`sitemap.xml`、`robots.txt`、canonicalの整備。
3. FormSubmitの有効化、実送信、個人情報案内。
4. GitHub Pagesをrelease限定公開へ変更。
5. 実ブラウザでスマホ・PC・キーボード・フォームの最終回帰試験。
6. 終了済みイベント、WDC2026、オンラインコーチング等の内容確認。
7. 最終GO/NO-GO判定。

## 既知の内容確認

`grade_3_list(20260813).pdf`と`grade_4_list(20260813).pdf`は、2026-08-13の合格者を含む一方、見出しが`2026/3/26現在`のまま。公式PDFを改変せず保全している。公開前の内容確認時に原本修正の要否を決める。

## 再開用コマンド

リポジトリの状態確認:

```bash
git status --short
```

公開対象とハッシュの事前確認:

```bash
scripts/build-jda-release.sh --check
python3 scripts/check-jda-legacy-integrity.py work/jda-approved-legacy-docroot
```

新しい出力先へ公開候補を生成:

```bash
scripts/build-jda-release.sh work/jda-release-candidate work/jda-approved-legacy-docroot
```

出力先が既に存在する場合は上書きせず停止する。既存候補を削除して作り直す操作は、対象パスを確認してから行う。

## 関連資料

- `docs/JDA_RELEASE_REVIEW.md`: 全体レビューと公開ブロッカー
- `docs/JDA_DEPLOY_ALLOWLIST.md`: 公開ファイルの生成・検証
- `docs/JDA_LEGACY_SERVER_AUDIT.md`: 旧サーバー読み取り監査
- `docs/JDA_LOLIPOP_CUTOVER_RUNBOOK.md`: ロリポップ切替とロールバック
- `docs/JDA_URL_REDIRECT_MAP.md`: URLと301対応表
- `deploy/jda-preserve-paths.txt`: 消してはいけないURL
- `deploy/jda-legacy-never-copy.txt`: 新JDA本体へコピーしない旧パス

## 作業上の注意

- ワークツリーには他ツール・ユーザーの未コミット変更が多数ある。関係ない変更を戻さない。
- CSS/JSを変更した場合は全対象HTMLのキャッシュ番号を揃える。
- AJDC/OIDC/TIDCの現行公開を、本体切替と同時に無断上書きしない。
- 旧docroot、WordPress、DB、元画像を削除しない。
- 本番変更前にバックアップとロールバック確認を完了する。
