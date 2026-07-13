# 手動更新・引き継ぎガイド

この資料は、HTML/CSSを人が直接編集する時のための実務メモです。
作業履歴や細かい判断理由は `PROJECT_NOTES.md`、トップページ改善の検討メモは `TOP_PAGE_DESIGN_MEMO.md` を見てください。
OIDCトップの背景写真を差し替える場合は、先に `OIDC_PHOTO_EDITING_MANUAL.md` を読んでください。

## まず見るファイル

```
index.html                トップページ本体
css/style.css             全ページ共通の見た目
js/main.js                全ページ共通の動き
marquee-updates.txt       トップ直下の赤い流れる更新帯
external/*/index.html     下層ページ
images/                   実際に表示する画像
OIDCphotos/               OIDCトップの自動切り替え背景写真
OIDC_PHOTO_EDITING_MANUAL.md OIDC写真の制作・差し替え手順
archive/unused-assets/    未使用・旧素材の保管場所
```

基本は `index.html`、`css/style.css`、`js/main.js` の3つを中心に考えます。
下層ページは `external/about/index.html` のように各フォルダの `index.html` に入っています。

## ファイル間の関係

```
index.html
  ├─ css/style.css?v=59        トップと下層ページ共通のCSS
  ├─ js/main.js?v=35           トップと下層ページ共通のJS
  ├─ marquee-updates.txt       赤い流れる更新帯の文章
  ├─ images/pickup/*.webp      ヒーロー画像・PICK UPカード画像
  ├─ images/champions/**       CHAMPIONSカード画像
  └─ external/*/index.html     ナビ・カード・更新情報から移動する下層ページ

external/contact/index.html
  ├─ FormSubmit                お問い合わせ送信先
  └─ ?subject=dispatch         派遣業務などの種別を自動選択

external/champions/index.html
  ├─ external/champions/data/champions.json
  └─ images/champions/** または images/poker/cardback.webp

external/OIDC/index.html
  ├─ OIDCphotos/**            トップ背景で自動切り替え表示する写真
  └─ OIDC_PHOTO_EDITING_MANUAL.md
```

CSSとJSはキャッシュ対策として `?v=数字` を付けています。
`css/style.css` を触ったら全ページの `style.css?v=...` を上げ、`js/main.js` を触ったら全ページの `main.js?v=...` を上げてください。

## 更新情報を更新する

「更新情報」には3種類あります。どれを変えたいかで触るファイルが違います。

### 1. トップ直下の赤い流れる帯

触るファイル: `marquee-updates.txt`

手順:

1. `marquee-updates.txt` を開く。
2. 表示したい文章を1行に1件ずつ書く。
3. `#` で始まる説明行と空行は表示されません。
4. 保存する。
5. ブラウザでトップページを再読み込みする。

HTML/CSS/JSは触らなくて大丈夫です。

### 2. トップページ下部の UPDATES カード

触るファイル: `index.html`

場所:

```html
<!-- ===== UPDATES ===== -->
```

手順:

1. `index.html` の `<!-- ===== UPDATES ===== -->` を探す。
2. `<a class="rule-item"...>` 1つが更新カード1件です。
3. 日付は `<p class="rule-date">` を変更。
4. 見出しは `<h3 class="update-text">` を変更。
5. リンク先は `<a class="rule-item" href="...">` の `href` を変更。
6. 必要なら `NEW` バッジ付きのカードは `rule-item-latest` を使う。

CSSは `.rule-item:has(.update-text)` がトップ更新カード用の見た目を担当しています。

### 3. 更新情報一覧ページ

触るファイル: `external/news/index.html`

トップのUPDATESだけを変更しても一覧ページは自動では変わりません。
クライアントに一覧ページも見せる場合は、同じ内容を `external/news/index.html` にも追記してください。

## トップページの主要セクション

`index.html` の大きな区切りはコメントで分かれています。

```
HEADER                全ページ共通に近いヘッダー
HERO                  最初の大きなスライド
MARQUEE STRIP         赤い流れる更新帯
SECTION DIVIDER       ロゴ入りの横長い仕切り画像
NEWS                  PICK UPカード
CHAMPIONS             トップのチャンピオンカルーセル
UPDATES               更新情報カード
ABOUT / FOOTER        フッター
```

見た目はほぼ `css/style.css` 側で決まります。
文章やリンク先、画像パスは `index.html` 側に直接書いてあります。

## 画像を差し替える

よく触る画像:

```
images/pickup/oidc.webp
images/pickup/tar.webp
images/pickup/regu.webp
images/pickup/howtogo.webp
images/logo/midd.webp
images/champions/<年度>/*.webp
OIDCphotos/*
```

注意:

- 既存画像を同じ名前で差し替えた場合、ブラウザキャッシュで古い画像が見えることがあります。
- その場合はHTML側の画像パスに `?v=2`、`?v=3` のような番号を付けます。
- 旧画像や元素材は削除せず、必要なら `archive/unused-assets/` に移動してください。

例:

```html
<img src="images/pickup/oidc.webp?v=4" alt="">
```

OIDCトップの背景写真は `OIDCphotos/` を使います。通常は5枚構成を維持し、`external/OIDC/index.html` の `.oidc-hero-bg` 内の `src="../../OIDCphotos/..."` だけを差し替えます。詳しい制作注意は `OIDC_PHOTO_EDITING_MANUAL.md` を参照してください。

## ヘッダー・フッターを変える

このサイトはビルドシステムを使っていないため、ヘッダーとフッターは各HTMLに直接コピーされています。
つまり、ナビやフッターのリンクを変える時は複数ファイルを同じように直す必要があります。

主な対象:

```
index.html
external/about/index.html
external/access/index.html
external/certification/index.html
external/champions/index.html
external/contact/index.html
external/dispatch/index.html
external/news/index.html
external/otp2/index.html
external/records/index.html
external/rule/index.html
```

`external/AJDC/`、`external/OIDC/`、`external/TIDC/` は旧特設サイトのミラーです。
この3つは後日作り直す方針なので、今は積極的に直さなくて大丈夫です。

## お問い合わせフォームを変える

触るファイル: `external/contact/index.html`

主な場所:

- `<form id="contactForm">`: 入力欄本体
- `<select id="cf-subject">`: お問い合わせ種別
- `subjectParamMap`: URLパラメータから種別を自動選択する設定
- `action="https://formsubmit.co/info@diabolo.jp"`: 送信先

例:

```js
const subjectParamMap = {
  dispatch: '派遣業務'
};
```

URLを `external/contact/index.html?subject=dispatch` にすると、種別が「派遣業務」になります。

## サイト内検索にページを追加する

触るファイル: `js/main.js`

場所:

```js
const SEARCH_INDEX = [
```

新しいページを作ったら、ここに1行追加します。

```js
{ title: 'ページ名', keywords: '検索に引っかけたい語句', path: 'external/example/index.html' },
```

`js/main.js` を触った場合は、全ページの `main.js?v=...` を上げます。

## ローカル確認

`file://` で直接開くと、`marquee-updates.txt` の読み込みやフォーム周りが正しく動かないことがあります。
必ずローカルサーバーで確認してください。

```bash
python3 -m http.server 8000
```

確認URL:

```text
http://127.0.0.1:8000/index.html
```

## GitHub Pages公開

現在の公開先:

```text
https://aratama-ship-it.github.io/JDAwebsite/
```

通常の流れ:

```bash
git status --short
git add 変更したファイル
git commit -m "変更内容を短く書く"
git push
```

push後、GitHub Pagesの反映には少し時間がかかります。

## 手動編集時の注意

- 作業前に `git status --short` を見る。
- `work/` は未追跡の作業素材置き場です。必要がなければpushしません。
- 旧素材は捨てずに `archive/unused-assets/` に残します。
- CSS/JSを変えたらキャッシュ番号を上げます。
- ヘッダー・フッター変更は複数ページに反映漏れが起きやすいので、検索して確認します。
- 大きく崩れた場合は、まず直前のコミットとの差分を確認します。
