# OIDC写真編集マニュアル

この資料は、`external/OIDC/index.html` のトップ画面で使っている背景写真を差し替える時の制作・編集メモです。
OIDCは毎年継続して使う特設サイトなので、写真を変えてもトップの文字、右側の告知カード、黒×オレンジの世界観が崩れないことを優先します。

## 使われている場所

OIDCトップのファーストビュー背景で、`OIDCphotos/` 内の写真を5枚読み込んでいます。

```text
OIDCphotos/
external/OIDC/index.html
```

HTML上の差し替え箇所は `external/OIDC/index.html` のこのブロックです。

```html
<div class="oidc-hero-bg" aria-hidden="true">
  <figure class="oidc-hero-bg-slide">
    <img src="../../OIDCphotos/..." alt="" loading="eager" decoding="async" fetchpriority="high">
  </figure>
  ...
</div>
```

`external/OIDC/index.html` から見ると、写真フォルダは2階層上にあるため、パスは必ず `../../OIDCphotos/ファイル名` になります。

## 基本方針

- 写真は「大会の空気感」を伝える背景として使います。主役はタイトルと2026年告知カードです。
- 写真自体に文字、ロゴ、日付、余白付きの加工を入れないでください。文字情報はHTML側で管理します。
- 写真は暗いオーバーレイの下に入るため、少し明るめ・コントラスト高めの写真が向いています。
- 左側には大きな `Osaka International Diabolo Competition` の文字、右側には告知カードが重なります。重要な顔、手元、ディアボロが画面の端やカードの裏に来ない写真を選んでください。
- 横長写真が最も安定します。縦長写真も使えますが、PCでは上下左右が大きく切り取られます。

## 推奨サイズ

推奨:

```text
横幅: 2000px前後
比率: 16:9 / 3:2 / 4:3 の横長
形式: WebP または JPEG
容量: 1枚あたり 300KB〜900KB 目安
```

避けたいもの:

- 横幅が1000px未満の写真
- 文字やロゴが焼き込まれている写真
- 主役が画面の左端・右端に寄りすぎている写真
- 暗すぎて黒背景と一体化する写真
- 白飛びが強く、オレンジのアクセントや白文字を邪魔する写真

## 枚数とアニメーション

現在は5枚構成です。

CSSでは30秒で1周し、6秒ごとに次の写真へ切り替わるようにしています。

```css
.oidc-hero-bg-slide {
  animation: oidc-hero-photo 30s ease-in-out infinite;
}

.oidc-hero-bg-slide:nth-child(2) { animation-delay: 6s; }
.oidc-hero-bg-slide:nth-child(3) { animation-delay: 12s; }
.oidc-hero-bg-slide:nth-child(4) { animation-delay: 18s; }
.oidc-hero-bg-slide:nth-child(5) { animation-delay: 24s; }
```

一番安全な更新方法は、5枚構成を維持して `src` のファイル名だけ差し替えることです。

枚数を変える場合は、HTMLだけでなくCSSの `animation-delay` と `animation` 秒数も調整してください。例えば4枚にするなら、1枚あたりの表示時間に合わせて `30s` や `6s` の数字を見直します。

## 差し替え手順

1. 新しい写真を `OIDCphotos/` に入れる。
2. ファイル名は英数字・ハイフン・アンダースコアだけにする。
3. `external/OIDC/index.html` を開く。
4. `.oidc-hero-bg` 内の `img src="../../OIDCphotos/..."` を新しいファイル名に変更する。
5. 先頭の1枚は `loading="eager"` と `fetchpriority="high"` を残す。
6. 2枚目は `loading="eager"` のままでよい。
7. 3枚目以降は `loading="lazy"` のままでよい。
8. ローカルサーバーで表示確認する。

確認URL:

```text
http://127.0.0.1:8000/external/OIDC/index.html
```

## ファイル名の例

今後、管理しやすくするなら次のような名前がおすすめです。

```text
oidc-2026-hero-01.webp
oidc-2026-hero-02.webp
oidc-2026-hero-03.webp
oidc-2026-hero-04.webp
oidc-2026-hero-05.webp
```

日本語、スペース、記号の多いファイル名は避けてください。GitHub Pagesやサーバー上でパスの扱いが面倒になります。

## 表示確認のチェックリスト

- PC幅でタイトルが読みやすい。
- 右側の2026年告知カードが写真に負けていない。
- 写真の主役がタイトル文字や右カードに隠れすぎていない。
- スマホ幅で写真の切り抜きが不自然ではない。
- 5枚すべてが読み込まれる。
- ヘッダーの `2026 Season` を押すとトップに戻る。
- ヒーロー内の `Aftermovie` 再生カード、右カード内の `Register`、`Details` が見える。
- `Aftermovie` 再生カードを押すとモーダルで動画が開き、閉じると再生が止まる。

## 写真が暗い・明るい時の調整

写真ごとに画像を強く加工する前に、まずCSSのオーバーレイを確認します。

関係するCSS:

```css
.oidc-hero::before
.oidc-hero::after
.oidc-hero-bg-slide img
```

基本は `.oidc-hero::before` の黒いグラデーションで文字の読みやすさを保っています。
現在は写真の存在感を少し出すため、`.oidc-hero-bg-slide img` に `brightness(1.18)` を入れ、黒いオーバーレイもやや薄めにしています。
写真が明るすぎる時はオーバーレイを少し濃くし、写真が暗すぎる時はオーバーレイを少し薄くします。

ただし、オーバーレイを薄くしすぎるとタイトルと右カードの可読性が落ちるので注意してください。

## アクセシビリティ

現在の写真は背景演出として扱っているため、`aria-hidden="true"` の中に置き、`alt=""` にしています。

写真自体をコンテンツとして見せたい場合は、背景ではなく別セクションにし、写真ごとに意味のある `alt` を入れてください。

動きが苦手な人向けに、`prefers-reduced-motion: reduce` では最初の1枚だけを静止表示するようにしています。この設定は残してください。

## 元画像の扱い

元画像、未使用写真、別候補の写真は削除しないでください。

保管先の候補:

```text
work/
archive/unused-assets/
```

本番で使う写真だけを `OIDCphotos/` に置くと、後から見た時に管理しやすくなります。

## Gitで忘れやすい点

`OIDCphotos/` は新しく追加したフォルダなので、コミット時に写真ファイルも一緒に含める必要があります。

```bash
git status --short
git add external/OIDC/index.html OIDCphotos/ OIDC_PHOTO_EDITING_MANUAL.md PROJECT_NOTES.md MAINTENANCE_GUIDE.md
git commit -m "Document OIDC hero photo editing"
```

`work/` は作業素材置き場なので、必要がない限りコミットしません。
