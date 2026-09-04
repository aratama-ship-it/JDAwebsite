# JDA旧サーバー 読み取り監査

監査日: 2026-08-22

## 結論

旧docrootは丸ごと移行しない。新しい空のJDA本体docrootは`deploy/jda-app.allowlist`と`deploy/jda-legacy-assets.allowlist`だけから生成する。AJDC/OIDC/TIDCは本体パッケージへ混ぜず、現行環境に隔離して残すか、別の承認済みスナップショットとサーバー側ルーティングで保全する。

## 調査したスナップショット

ローカルの隣接フォルダ`JDA web`を読み取り専用で確認した。これは現行サーバーの完全・最新スナップショットであることをまだ管理画面側で照合していない。

- 総ファイル数: 50,245
- PHP: 26,725
- HTML: 399
- symlink: 0
- world-writable file: 0
- 主なPHP配置: OIDC 17,613、AJDC 4,599、`test/` 2,832、`wp/` 1,674
- WordPress本体の版表示: AJDC 6.4.8、OIDC 6.2.9、`wp/` 4.9.26、`test/test/` 6.4.8

版番号だけで侵害有無は断定しない。ただし複数のWordPress本体、テスト環境、旧設定、バックアップ用領域が同居しており、新しい静的サイトの公開元として信頼できる構成ではない。

## 確認した問題

### 1. 不審なsitemap

旧`/sitemap.xml`は960,834 bytes、2018-01-04更新、4,773 URLを含む。全URLが`http://diabolo.jp/`配下の無関係な英単語深層パスで、正規のJDAページを含まない。SEOスパムまたは過去の侵害残骸として扱い、新環境へコピーしない。正規URLだけの新sitemapへ置換する。

### 2. 旧メール送信PHP

ルート`/send.php`は未検証のPOST値をメール件名と`From`ヘッダーへ連結して送信する。TIDCの4本の`send.php`も入力メールアドレスを`From`と確認メール送信先に使い、入力検証・レート制限・CAPTCHAが見当たらない。新JDA本体へコピーしない。TIDCを残す間も、これらの処理は公開継続の必要性を確認し、代替フォームへ置換するまで隔離・監視する。

### 3. 旧資産の内容同一性

従来の公開ビルドはPDFの`%PDF-`、MP3のMIMEだけを確認していた。形式を保った改変を検知できないため、`deploy/jda-legacy-assets.sha256`と`scripts/check-jda-legacy-integrity.py`でSHA-256の一致を必須にした。

19 PDFと1 MP3は、暗号化、PDF添付、`/JavaScript`、`/OpenAction`、`/Launch`、`/RichMedia`の簡易検査で該当なし。最新4 PDFは全ページをPNGへレンダリングし、文字切れ・重なり・黒塗り・判読不能な文字がないことも確認した。これは完全なマルウェア鑑定ではなく、ハッシュは確認済み内容を固定するためのもの。

### 4. 最新PDFの取得

ローカル旧バックアップには次の4本がなく、古い合格者一覧だけがあった。

- `certification/grade_1_list(20260813).pdf`
- `certification/grade_2_list(20260813).pdf`
- `certification/grade_3_list(20260813).pdf`
- `certification/grade_4_list(20260813).pdf`

2026-08-22に公式`https://diabolo.jp/certification/`からHTTPSで取得し、A4・各1ページ・暗号化なし・添付なし・能動コンテンツなしを確認してSHA-256を登録した。承認済み資産は`work/jda-approved-legacy-docroot/`へまとめ、旧バックアップ全体を公開ビルドの入力にしない。

内容上の注意として、3級・4級PDFは2026-08-13の合格者を追加している一方、見出し下の日付が`2026/3/26現在`のままになっている。公式公開物を改変せずそのまま保全したが、内容更新工程で原本修正の要否を確認する。

## 移行時の扱い

| 対象 | 扱い |
|---|---|
| 新JDA本体 | allowlistから新しい空のdocrootを生成 |
| 規則・検定PDF、1分MP3 | 個別allowlist＋SHA-256一致時のみ取り込み |
| AJDC/OIDC/TIDC | 本体と混ぜず現行環境で隔離保全、または別スナップショット＋ルーティング |
| 旧記事HTML | 依存資産を個別棚卸し後に保全または301 |
| `send.php`、`test/`、`wp/`、旧`sitemap.xml` | 新docrootへコピーしない |
| `wp-config.php`、DB、未知のPHP、旧`.htaccess` | 新docrootへコピーしない。必要な大会環境内だけで隔離 |

既知の非移行パスは`deploy/jda-legacy-never-copy.txt`に記録した。このリストは削除指示ではなく、旧環境の保全と新環境への混入防止を分けるためのもの。

## 本番切替前の管理画面確認

1. 実際のdocument rootと、このスナップショットの差分・更新日時を照合する。
2. vhost、サブドメイン、cron、PHPハンドラー、メール送信処理、DB、`.htaccess`を棚卸しする。
3. 新JDA本体docrootではPHP実行を無効化し、生成済みrelease以外を置かない。
4. AJDC/OIDC/TIDCを残すルーティングとロールバック方法を決める。
5. 旧`sitemap.xml`を隔離し、正規HTTPS URLだけのsitemapへ置換する。
6. Search Consoleで不審URL、登録sitemap、セキュリティ問題を確認する。

管理画面・Search Consoleへの認証済み確認と、Security Traffic Analysisは今回未実施。旧docrootの丸ごと移行禁止という判断には影響しないが、侵害の有無を最終確定するには別途必要。
