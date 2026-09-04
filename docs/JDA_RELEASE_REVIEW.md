# JDA本体サイト 公開前レビュー

最終確認日: 2026-08-22

> **履歴資料:** 以下は2026-08-22時点の全面切替レビューであり、現在の本番状態ではない。2026-09-03の確認では公開ルートに `.htaccess` は存在せず、通常公開から除外する方針へ更新した。現行方針は `server-config/README.md` を参照する。

## 結論

JDA本体の静的ページは、ローカル環境で確認できた表示・操作・リンク・フォーム実装の主な不具合を修正済みです。通常ページの公開URLは `/about/` などのルート直下へ整理し、既知の旧URLに対する301転送も実装しました。公開allowlistと検証付きの公開候補生成処理も実装済みです。ただし、**現時点では本番公開不可**です。残っている理由は、大会・過去記事等の保全元となる現行サーバーの安全性、本番フォーム、個人情報方針、現行サーバーの不審なsitemapの扱いが未確定だからです。

第1段階の対象は、トップと通常下層10ページです。`external/champions-poker/` は除外し、AJDC/OIDC/TIDCは現行の `/AJDC/`、`/OIDC/`、`/TIDC/jp/` を維持します。

## 今回修正した項目

- 全11ページの大会リンクとサイト内検索を、ローカルミラーではなく現行のAJDC/OIDC/TIDC公開URLへ統一。
- 検定合格者PDF 4本を、404だった旧版から `grade_1_list(20260813).pdf`〜`grade_4_list(20260813).pdf` へ更新。
- トップと更新一覧へ2026-07-05の検定更新を反映。
- 終了済みのOIDC 2026とOTP2を過去形にし、OTP2の閉鎖済み申込フォームを「受付終了」表示へ変更。
- デスクトップ大会メニューのキーボード開閉、Escape、外側クリック、モバイルからPC幅へ戻した時の状態リセットを修正。
- モバイルメニューを低い画面でも縦スクロール可能にし、320px検索欄とロゴの重なりを解消。
- 閉じた検索欄をTab順とアクセシビリティツリーから外し、開閉状態、結果領域、検索先を修正。
- 全ページへスキップリンク、`main`、適切な見出し階層、検索/メニューのARIA、meta description、faviconを追加。
- 自動スライド、更新帯、CHAMPIONSへ一括の「動きを停止/再開」操作と `prefers-reduced-motion` 対応を追加。
- CHAMPIONSと更新帯の複製要素を支援技術から除外。
- 問い合わせ確認画面のDOM XSSを解消し、入力値を `textContent` で表示する方式へ変更。
- FormSubmitのAjax URLを `/ajax/info@diabolo.jp` へ修正し、添付上限を公式仕様どおり合計10MBへ統一。
- 問い合わせ/動画ダイアログへdialog属性、Escape、フォーカス移動・復元・逸脱防止を追加。
- 氏名/メールのautocomplete、ファイル選択を含むフォーカス表示、フォーム境界、文字色コントラストを修正。
- iframeへtitleと遅延読み込みを追加し、HTML属性内の未エスケープ `&` を修正。
- 通常下層10ページを `/external/.../` から `/about/` などのルート直下へ移し、内部リンク、検索インデックス、相対アセット参照、CHAMPIONSデータ取得を新URLへ統一。
- 既知の旧URLを新URLへ送る301ルールと、静的プレビュー用の転送ページを追加。対応表は `docs/JDA_URL_REDIRECT_MAP.md` に記録。
- 共通CSS/JSのキャッシュ番号を全11ページで `style.css?v=60` / `main.js?v=37` に統一。

## 自動・ブラウザ検証結果

以下は合格しています。

- 対象11ページ × 5画面幅（1440 / 1024 / 768 / 375 / 320px）で横スクロールなし。
- コンソール例外、page error、ローカルrequest failure、表示済み画像の読み込み失敗なし。
- 各ページに `main` 1個、H1 1個、重複IDなし。
- モバイルメニューは開閉・大会展開・内部スクロールが可能。
- 768pxで開いたメニューを1024pxへ広げた時、モバイル表示と `aria-expanded` が正常に解除。
- 320pxで検索欄とロゴ/ハンバーガーの重なりなし。
- 大会メニューはEnterで開き、Escapeで閉じてトリガーへ戻る。
- 検索は開閉時にTab状態が同期し、「AJDC」検索が `https://diabolo.jp/AJDC/` を返す。
- 自動モーションは停止中にヒーロー・更新帯・CHAMPIONSが停止し、再開後に動作。
- 問い合わせ確認画面へHTML文字列を入力しても要素やスクリプトとして解釈されない。
- 検定動画はYouTube埋め込みURLと動的titleを設定し、Escapeで閉じて元リンクへ復帰。
- HTML/JS構文、ローカル参照、CSS参照、target blankのnoopener、共通キャッシュ番号は整合。

Googleカレンダー、Google Maps、YouTube内部操作、FormSubmitのPOSTは、外部サービスを遮断した自動巡回では完全検証していません。本番前の手動確認対象です。

## P0: 公開前に必須

### 1. 公開URLと既知の旧URL転送 — 完了

通常ページは `/about/`、`/access/`、`/certification/`、`/champions/`、`/contact/`、`/dispatch/`、`/news/`、`/otp2/`、`/records/`、`/rule/` に確定しました。内部リンク、`SITE_ROOT`、検索インデックス、CHAMPIONSデータ取得、問い合わせURLパラメータを新構成へ更新済みです。

旧 `about_us.html`、`access.html`、`records.html`、`rule.html`、`inquiry.html`、`performer.html`、`workshop.html`、`about_OTP2.html` と旧 `/external/.../` URLは、ルート `.htaccess` でHTTP 301転送します。未確定の歴史ページとサービスURLは誤転送を避けて保留し、`docs/JDA_URL_REDIRECT_MAP.md` に理由と次の判断事項を記録しています。canonicalは正規ホストを決める「4. 正規オリジンとSEO設定」で追加します。

### 2. 公開allowlistを作る — 完了

`deploy/jda-app.allowlist`に新サイト54ファイル、`deploy/jda-legacy-assets.allowlist`に旧サイトから取り込むPDF 19本とMP3 1本を完全な相対パスで定義しました。`scripts/build-jda-release.sh`は、この74ファイルだけを新しい空の公開候補へコピーし、出力先の上書きや旧docrootの丸ごとコピーを行いません。

`scripts/verify-jda-release.sh`は、公開候補がallowlistと完全一致すること、余分なファイル/ディレクトリ、symlink、内部資料、`external/`、PHP/SQL/環境ファイル等を含まないこと、PDF/MP3の実体が拡張子と一致することを確認します。2026-08-22に現行公開資産を一時取得した組み立て試験で74ファイル完全一致、ページ実行時のローカル依存漏れ0件を確認しました。詳細は`docs/JDA_DEPLOY_ALLOWLIST.md`を参照してください。

ニュースが参照する過去イベント、オンラインコーチング、現行AJDC/OIDC/TIDC等は削除対象ではありませんが、本体パッケージへ無検査で混ぜません。`deploy/jda-preserve-paths.txt`に保全対象として固定し、次の現行サーバー調査で依存関係と安全性を確認します。

### 3. 現行サーバーを調査し、旧docrootを丸ごとコピーしない

現行の `https://diabolo.jp/sitemap.xml` は、確認時点で960,834 bytes、4,773 URLを含み、すべて無関係な深いHTTP URLでした。正規ページは0件です。過去のSEOスパムまたは侵害残骸の可能性があるため、未知のPHP、`.htaccess`、深いディレクトリ、sitemapを新環境へ持ち込みません。

必要資産だけをallowlistで抽出し、サーバーファイルとSearch Consoleを調査します。新sitemapは正規HTTPS URLだけで生成し、旧不審URLが404/410になることを確認します。

### 4. 正規オリジンとSEO設定を決める

現行は `http/https × www有無` の4オリジンが200で応答します。HTTPSの正規ホストを決め、他をHTTP 301で統一します。公開URL確定後にabsolute canonical、OGP、Twitter Card、robots.txt、正常なsitemap.xmlを生成します。

GitHub Pagesの検証サイトでは `PROJECT_NOTES.md`、`AGENTS.md`、`external/champions-poker/` が公開され、robots/noindexもありません。本番allowlistと同じ配備物へ切り替えるか、検証サイトを停止/非公開化してください。

### 5. 問い合わせフォームを運用可能にする

FormSubmitは初回送信後、`info@diabolo.jp` に届く確認メールで有効化が必要です。本番オリジンからテストし、受信、返信先、画像添付、captcha、失敗表示を確認します。このレビューでは実メールを送信していません。

氏名、メール、自由記述、画像をFormSubmitへ外部送信するため、公開前に利用目的、外部サービス利用、保持/削除、問い合わせ窓口を示すプライバシー方針と送信前の同意導線を確定します。

### 6. バックアップとロールバックを準備する

現行ファイル、WordPressデータベース、公開フォルダ設定をバックアップし、空き容量と復元手順を確認します。独自ドメイン設定は解除せず、新しい公開候補フォルダで検証してから切り替えます。問題時に旧公開フォルダへ戻す担当と手順を決めます。

## P1: 内容・運用の確認

- World Diabolo Contest 2026（2026-11-05〜08、台湾）をトップのどこへ掲載するか決定し、適切な画像と導線を追加。
- 現行で受付中のオンラインコーチングを継続するか決定。継続なら内容・料金・講師PDF・申込導線を移行し、終了なら旧URLへ終了案内/転送を設定。
- 派遣料金の税込、演技指導込み、1名単価を含む2026年の有効条件を責任者が確認。
- `track/1m.mp3` の練習利用・再配布条件を新記録ページへ引き継ぐ文言を確認。
- 更新一覧の `2024-7-23` が2025年項目間にあるため、年を原典で確認。
- 日常更新を1つのデータからトップ、更新帯、更新一覧へ反映する生成方式へ移行。
- ヘッダー/フッターとキャッシュ番号を手作業で11ページへ複製しない生成方式へ移行。

## 公開当日のチェックリスト

1. 公開日基準でイベント・更新・料金・受付状況を再確認。
2. バックアップ、復元テスト、公開allowlist、除外listを承認。
3. 新候補フォルダで全ページ、PDF、MP3、旧URL、301、canonicalを検証。
4. AJDC/OIDC/TIDCの表示、管理画面、DB接続を再確認。
5. 本番オリジンからFormSubmitを有効化し、受信/添付/失敗経路を確認。
6. HTTPSと正規hostの301、robots、sitemap、404/410を確認。
7. PC、iPhone相当、Android相当でメニュー、検索、動画、フォーム、カレンダー、地図を手動確認。
8. 切替後にアクセスログ、404、Search Console、メール受信を監視。
9. 問題時は旧公開フォルダへ戻し、原因と差分を記録。

## 参照

- [JDA現行公式サイト](https://diabolo.jp/)
- [現行sitemap](https://diabolo.jp/sitemap.xml)
- [FormSubmit Documentation](https://formsubmit.co/documentation)
- [FormSubmit AJAX Documentation](https://formsubmit.co/ajax-documentation)
- [2026-07-16 リニューアル会議メモ](meetings/2026-07-16-jda-website-renewal.md)
