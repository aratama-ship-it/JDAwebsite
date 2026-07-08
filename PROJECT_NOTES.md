# diabolo.jp リデザイン モック — 引き継ぎノート

## このプロジェクトについて

`https://www.diabolo.jp`(日本ディアボロ協会の公式サイト)のリデザイン案として作成した静的HTMLモックです。
デザインの参照元は `https://www.redbull.com/jp-ja/`(ダーク基調 → 現在は白基調に変更済み、後述)。

トップページ + 9つのサブページからなる完パケのフォルダで、`index.html` を起点にすべて相対パスでリンクしています。

## 動かし方(重要)

お問い合わせフォーム(FormSubmit連携)が `file://` では動作しないため、**ローカルサーバー経由で開く必要があります**。

```bash
cd "diabolo-redesign-mock"
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000/index.html` を開く。

## ファイル構成

```
diabolo-redesign-mock/
├── index.html                  トップページ
├── css/style.css                共通スタイル(全ページで読み込み)
├── js/main.js                   共通スクリプト(全ページで読み込み)
├── images/
│   ├── logo/                    ロゴ・仕切りバナー(midd.png)
│   ├── hero/                    ヒーロー/CTA用の写真
│   ├── pickup/                  PICK UPカード用(oidc.png, tar.png, regu.png, howtogo.png)
│   ├── champions/               CHAMPIONSカルーセル用の選手写真(1〜10)
│   ├── events/                  大会バナー(現在未使用、将来のイベント欄用に保持)
│   └── image-specs.txt          各画像の推奨サイズ・形式まとめ
└── external/                    サブページ・外部ミラー
    ├── about/                   協会について(本協会の目的・沿革)
    ├── access/                  事務所・店舗へのアクセス(Googleカレンダー・マップ埋め込み)
    ├── certification/           ディアボロ検定(検定技リストはアコーダション、動画はモーダル再生)
    ├── contact/                 お問い合わせ(FormSubmit連携フォーム、二段階確認モーダル)
    ├── news/                    更新情報(diabolo.jpの実際の更新履歴25件)
    ├── otp2/                    TAR UMT OTP TOURNAMENT 2.0 大会情報
    ├── records/                 記録一覧(男女別の各部門テーブル)
    ├── rule/                    採点規則(バージョン別PDFリンク一覧)
    ├── AJDC/, OIDC/, TIDC/      diabolo.jp本家サイトのHTMLをそのままミラーしたもの(レイアウトは別物、リンク先として使用)
```

## デザインの現状(重要な決定事項)

- **配色は白ベースに変更済み**。元はダーク基調(Red Bull風)で作っていたが、ユーザーの指示で全体を反転し、現在は白背景+濃いグレー系の文字が基本。赤(`--red: #db0a40`)はアクセントとして継続使用。
- **ヘッダーは全ページで白背景+暗色文字に統一**。スクロールしても色が変わらない(以前は暗→白に切り替わる仕様だったが「切り替え不要、白のままでよい」という指示で統一した)。
- ヘッダーの「大会情報」はクリックしても画面遷移しない(`href="javascript:void(0)"`)。ホバーでドロップダウン(全日本/東京国際/大阪国際/採点規則/記録一覧)が開くだけ。
- ヘッダー右側にサイト内検索(クリックで展開、虫眼鏡アイコンはYouTubeアイコンの右)。検索インデックスは `js/main.js` の `SEARCH_INDEX` 配列にハードコード。
- CHAMPIONSセクションはトレーディングカード比率(5:7)のカードが5枚見えるカルーセル。カーソルでホログラム風の傾き+虹色シャイン演出あり(`.athlete-card-shine`)。矢印+ドラッグ可能な進捗マーカー(ディアボロ型)で操作。
- PICK UP直前に `midd.png` を使った全幅の仕切りバナーがある。以前はスクロールに応じて動くパララックス演出があったが、「スクロールで動かさず固定にしてほしい」という指示で削除し、現在は完全に固定表示。

## キャッシュ対策(重要・忘れやすい)

`css/style.css` と `js/main.js` は、編集してもブラウザにキャッシュされて反映されないことが何度かあった。
**全ページの `<link>` / `<script>` タグに `?v=N` を付けてあるので、CSSかJSを編集したら必ずバージョン番号を上げること。**

- 現在のCSSバージョン: `style.css?v=50`(9ページ全て同じ値で揃える)
- CHAMPIONSカルーセル下部の進捗バー(`.carousel-progress`)の幅を160px→260pxに拡大(560px以下のスマホ用の100px幅は変更なし)。
- サイト共通のコンテンツ幅をさらに8%拡大(`1700px`→`1836px`)。
- サイト共通のコンテンツ幅をさらに`1600px`→`1700px`に拡大(「もう少しだけ拡大してほしい」の要望)。
- 画像の解像度見直し:
  - チャンピオン写真・`cardback`のWebPは長辺800px→900pxに再生成(コンテナが広がった分、表示サイズに対する余裕=ヘッドルームを確保するため)。
  - `images/pickup/*.png`(ヒーロー全幅+PICK UPカードで共用)と`images/logo/midd.png`は、表示に必要な解像度自体は既に適正(ヒーローが全幅・retina対応のため大きい解像度が必要)だったので**寸法は変更せず**、PNG→WebP(quality 85)でファイルサイズだけ圧縮(oidc: 1337KB→74KB、tar: 2520KB→232KB、regu: 1732KB→67KB、howtogo: 2262KB→199KB、midd: 1512KB→66KB)。`index.html`の参照を`.webp`に更新済み。元のPNGはこれまでの方針通り削除せず残している。
- サイト共通のコンテンツ幅(`.header-inner`/`.section`/`.footer-top`/`.footer-bottom`/`.page-title-inner`/`.cert-section-wide`等、計7箇所)を`max-width: 1400px`→`1600px`に拡大。理由: ヒーロー/マーキー/midd帯は全幅(full-bleed)なのに対し、ヘッダーやPICK UP/CHAMPIONS等のコンテンツは1400pxで止まっていたため、MacBook等の大きい画面でその差が目立って「崩れて見える」との指摘があった。1600pxまで広げることでPICK UPのカード・CHAMPIONSカルーセルの画像も自動的に大きくなる(画像サイズそのものは変更していない、コンテナが広がった分表示が拡大される)。これより広い画面への最適化は想定していない。
- お問い合わせページ(`external/contact/index.html`)の連絡先リストから「メール: info@diabolo.jp」の項目を削除済み(SNSのみの表示に)。
- 現在のJSバージョン: `main.js?v=32`
- **CHAMPIONSカルーセルは方針変更により、スクロール連動をやめて「回転寿司」式の常時自動再生に変更済み**(過去のスクロール連動・スナップ実装は完全に置き換えた)。
  - シャッフル済みの10枚をもう一度複製して20枚のトラックを作り(マーキーと同じ「ちょうど半分の位置でtranslateXを巻き戻す」手法)、`requestAnimationFrame`で時間経過に応じて`SPEED = 22px/秒`で一方向に流れ続ける。継ぎ目が見えないのは複製のおかげ。
  - カーソルが`#athletes`セクション(カード・矢印・進捗バーを含む全体)の上にある間は`paused`フラグで自動再生を止める(`mouseenter`/`mouseleave`)。
  - 矢印クリック・進捗バーのドラッグは、自動再生用の`offset`(px)を直接書き換える方式に統一(以前の「0〜maxIndexの段階的index」方式は廃止)。クリック時のみ`transition: transform 0.4s ease`を一時的に付けて滑らかにスナップさせ、自動再生中とドラッグ中は`transition: none`で逐次描画する。
- **モバイルヘッダーのデザイン改善(4点レビュー対応)**:
  1. SNSアイコンをヘッダーから外し、ハンバーガーメニュー内(`.main-nav-sns`、全9ページの`<nav id="mainNav">`内に複製マークアップを追加)に移動。`max-width:1023px`で`.header-actions .sns-links`を非表示、`.main-nav.open .main-nav-sns`のみ表示。
  2. モバイル検索欄の幅をSNS分の余白を気にせず拡大(`max-width:1023px`で180px、`max-width:480px`で150px。旧480px時130px固定だった)。
  3. 「大会情報」ドロップダウンを`max-width:1023px`でクリック開閉対応。`js/main.js`が`.nav-trigger`クリックで親`.nav-item`に`is-open`をトグルし、CSSの`.nav-item.has-dropdown.is-open .dropdown-panel`で表示。**ハマったポイント**: `.nav-item`が`display:flex`なので、`.dropdown-panel`を`position:static`にしただけだと横並びの兄弧要素になってしまう。`@media(max-width:1023px){.nav-item.has-dropdown{display:block;}}`で縦積みに修正した。
  4. PICK UP/CHAMPIONS/UPDATESの余白・密度を`max-width:700px`でコンパクト化(`.section`のpadding、`.card-grid`/`.athlete-grid`のgap、`.card-body`/`.rule-item`のpadding等を縮小)。
  この一連の変更でハンバーガー/ドロップダウンのブレークポイントは`1023px`(既存の`.hamburger`表示切替と合わせた)、余白密度の変更は`700px`(スマホ向け)を使い分けている。
- **CSS変数のリネーム**: `css/style.css`の`:root`で`--black`(実際は白`#ffffff`)・`--white`(実際は黒系`#15151a`)という名前と実際の色が逆になっていた問題を修正。`--black`→`--bg`、`--black-soft`→`--bg-soft`、`--white`→`--text`、`--off-white`→`--text-muted`に役割名でリネーム済み(色の値そのものは変更なし、62箇所の`var(...)`参照も全て追従済み)。`--gray`/`--gray-dark`/`--red`/`--red-bright`は名前と実際の色が一致しているため変更していない。`css/style.css`以外(js/main.js・HTML)でこれらの変数名を直接参照している箇所は無かった。
- チャンピオン写真(`images/champions/2024・2025・2026/*.png`、各2〜9.5MB)と`images/poker/cardback.png`(2.7MB)をWebPに変換・圧縮済み(長辺800pxにリサイズ、quality=78)。合計84.6MB→1.7MBに削減。`index.html`・`external/champions/data/champions.json`・`external/champions-poker/js/main.js`・`external/champions/index.html`内の参照を`.webp`に更新し、チャンピオンカードの`<img>`に`loading="lazy"`を追加した(トップのCHAMPIONSカルーセル10枚、歴代チャンピオン一覧の121枚)。元のPNGファイルはユーザーの許可なく削除しない方針のため、参照されないまま各フォルダに残っている(容量整理が必要な場合は明示的な削除指示を待つこと)。
- **重要**: `images/diaicon.png`(赤いグロス調の元画像)は実体が存在しない(おそらく作業中に削除された)。`css/style.css`内の2箇所(マーキー区切りアイコン、`.page-title`の背景装飾)で参照していたため404になっていたバグを修正し、両方とも実在する`images/diaicon-white.png`に差し替えた。`.page-title`側は背景が薄いグレーで白アイコンのままだと見えなくなるため、`filter: brightness(0.35)`を追加してグレー寄りに暗くし、視認できるようにしている。今後 `diaicon.png` という名前のファイルを画像参照に使う場合は、まずファイルの実在を確認すること。
- `.page-title`のpaddingは`140px 32px 56px`(元)→`116px 32px 88px`(下が空きすぎたとの指摘)→`116px 32px 64px`(現在)と調整。
- サブページ共通の`.page-title`(協会について/検定/歴代チャンピオン一覧などのページ見出し帯)から赤バッジ(`.hero-tag`)を非表示にし、代わりに控えめな背景(赤の淡いradial-gradient2つ + `images/diaicon.png`を左上・右下に`opacity:0.06`で薄く配置、画像生成は行わずCSSのみで実装)を追加した。
- ヘッダーの「大会情報」ドロップダウン最下部に「歴代チャンピオン一覧」(`external/champions/index.html`へのリンク)を全9ページに追加済み。HTMLの変更のみでCSS/JSのバージョンアップは不要だった。
- スマホ幅(700px以下)のヒーロー高さを1.5倍(260px→390px)に変更し、ヒーロー内の赤いボタン(`.hero-actions`)を非表示にした。デスクトップ幅(662px・ボタン表示あり)には影響しない。
- フッター最下部のコピーライト(`.footer-bottom`)は`justify-content: space-between`(子要素が1つだけなので実質左寄せになっていた)から`center`に変更し、全ページ共通で中央寄せにした。
- `.section-divider`の下部を白背景(PICK UP)へ自然に溶け込ませるため、`::after`で`linear-gradient(to bottom, rgba(255,255,255,0) 40%, #ffffff 100%)`のオーバーレイを重ねている(`pointer-events:none`でクリックを妨げない)。
- `.section-divider img`の位置を10pxだけ上にずらすため、`transform: translate(-50%, calc(-50% - 10px))`にしている。
- `.section-divider img`の固定高さはさらに拡大の要望で440px→560pxに変更(セクション自体の高さ135pxは不変)。
- `external/champions/index.html`の年度見出し(`.champions-year-head h2`)は、長い正式名称を表示するようになったため太字すぎる見た目(グローバルなh1-h4の`font-weight:900`継承)を`font-weight:700`に軽量化、フォントサイズも`clamp(18px,2.2vw,24px)`に縮小済み。
- 「※ 選手の写真は現在準備中のため、カード画像は仮置きの状態です。」の注記は、ページ先頭の固定テキストではなく、実写真が無い最初の年度(2025年度)の直前に動的挿入するようにした(`firstPlaceholderIndex`で`item.image`を持たない最初のグループを検出)。2026年度のみ実写真があるため、注記はその後ろに表示される。
- `.section-divider img`の固定高さはさらに拡大の要望で320px→440pxに変更(セクション自体の高さ135pxは不変)。
- `images/logo/midd.png`がデザイン変更され、アスペクト比が大きく変わった(旧: 横長の細い帯 約1920:190 → 新: 2827:744 ≈3.8:1、ロゴ+テキストが中央に大きく配置された構図)。
- `.section-divider img`は当初`width:100%; height:100%; object-fit:cover;`(コンテナいっぱいに伸縮)にしたが、これだとウィンドウ幅が狭くなるほど表示スケールも縮んでロゴが小さくなりすぎる問題があった。`position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:auto; height:320px;`に変更し、画像をウィンドウ幅に依存しない固定の高さ(320px、拡大気味)で中央配置するようにした。コンテナ(`.section-divider`, 高さ135px固定)の`overflow:hidden`で上下左右が自動的にクロップされる。
- ヒーローのスライド切り替えドット(`.hero-dots`)は左寄せ(`left:32px`)から中央寄せ(`left:50%; transform:translateX(-50%)`)に変更。テキスト(`.hero-slide-content`)は左寄せを維持したまま、`padding-bottom`を56px→32pxにして下にずらした。
- `.hero-tag`(「大会」「案内」等のヒーロー内バッジ)はPCでも非表示にした。ただし`.hero-tag`クラスは`.page-title`(サブページの見出し帯、例: CERTIFICATION)でも再利用されているため、グローバルに`display:none`にはせず`.hero .hero-tag`に限定して非表示にしている。
- 現在のJSバージョン: `main.js?v=27`
- スマホ幅(700px以下)では`midd.png`の帯(`.section-divider`)を`display:none`で非表示にしている。
- ハンバーガーメニュー展開時、背景が旧ダーク基調時代の`rgba(10,10,10,0.98)`(黒)のままで、文字色は白ベース化後の暗い色を継承していたため「黒地に黒文字で読めない」バグがあった。背景を`#ffffff`に変更して修正済み(`js/main.js`のhamburgerクリック処理)。閉じる時は`removeAttribute('style')`でインラインスタイルを完全にクリアするようにした。
- スマホ幅(700px以下)では、ヒーロー(`.hero`)の高さをデスクトップの662pxの半分程度の`260px`に、ヒーローの赤いタグ(`.hero-tag`、「大会」「案内」等の表示)を`display:none`で非表示にしている。**CSSの注意点**: `.hero-tag`の非表示メディアクエリは`.hero-tag`の基本定義(`display: inline-block`)より後ろに置くこと。同じ詳細度の場合は記述順で後勝ちになるため、先に置くと無条件定義に上書きされて効かなくなるバグがあった。
- `midd.png`の表示位置(`.section-divider img`の`top`)は`-65.5%` → `-75%`に調整(セクション自体の高さ135pxは変更せず、画像だけ上にずらした)。
- ヒーロー(`.hero`)は元々`height: 60vh`(min420px/max620px)でビューポートの高さに連動していたが、「シネマサイズ・ウィンドウ幅で高さが大きく変わらないように」という要望で固定`height`に変更。その後「1.2倍に」を2回適用し、現在は`height: 662px`(700px以下は518px)。
- `midd.png`の帯(`.section-divider`)は元々`aspect-ratio: 1920/190`でウィンドウ幅に連動して高さが変わっていたが、「ウィンドウ幅で高さを変えたくない、赤帯(マーキー、高さ45px)の3倍程度に」という要望で固定`height: 135px`に変更。ウィンドウ幅を変えても高さは変動しない。
- マーキーのアイコンと文字の間隔は2回の拡大を経て、`.marquee-track span`のpadding: 31.5px、`::after`のmargin-left: 63px(対称性は維持)。
- マーキーの区切りは★文字から、`images/diaicon.png`(赤いグロス調のディアボロイラスト)を元に作った白いシルエット版 `images/diaicon-white.png`に変更。`.marquee-track span`のpaddingは14px→21px、`::after`のmargin-leftは28px→42px(いずれも1.5倍)にして、アイコン周りの空白を拡大した。
- `diaicon-white.png`は単純なアルファしきい値だと中央の軸部分がガタつく(元写真の反射ハイライトが薄いせいでノイズが残る)ため、モルフォロジー的クロージング(`ImageFilter.MaxFilter`→`MinFilter`)とガウスブラー+再しきい値で輪郭を滑らかにし、砂時計型のシンプルな1色シルエットに整形済み。再生成する場合は同じ手順(`images/diaicon.png`のアルファ→閾値40→クロージング(9px)→ブラー(2px)→再閾値127)を踏むこと。
- 現在のJSバージョン: `main.js?v=26`
- `midd.png`のパララックス処理(`updateDividerParallax`)は削除済み。「スクロールでの移動はなく固定にしてほしい」という指示により、`js/main.js`からscroll連動のtransform処理ブロックを丸ごと削除し、画像は常に静止表示。
- ヒーロー下の帯(マーキー)の表示内容は `marquee-updates.txt`(プロジェクトルート、index.htmlと同階層)から読み込む。1行1項目、`#`で始まる行と空行は無視。Claudeを使わずメモ帳等で編集→保存→ブラウザ再読み込みだけで帯の内容を更新できる(非エンジニアでも管理できるようにするための要望で対応)。`fetch`でファイルを読みに行くため、ローカルで確認する際も`python3 -m http.server`経由で開く必要がある(file://だとfetchがブロックされ、その場合はindex.html内にある既定の4項目にフォールバックする)。本番サーバーにアップロードする際は`marquee-updates.txt`も一緒に配置すること。
- マーキー(`#marqueeTrack`)は元々HTML側で項目セットを手動で2回コピーして無限ループを実現していたが、項目を増減すると複製がズレて途切れる恐れがあった。`js/main.js`の`setupMarquee()`で、元の項目セット(index.htmlには1セット=4項目のみ記述)を画面幅を覆うまで動的に複製し、その複製ブロックをさらに2倍にしてから`translateX(-50%)`アニメーションを適用する方式に変更。画面リサイズ時も再計算されるため、項目数や画面幅に関わらず途切れずループする。
- ヘッダーの「オンラインストア」は「オンラインショップ」に表記変更済み(全9ページ)。
- マーキー(`.marquee-track span`)の★と文字の間隔は、`padding: 0 28px`と`::after`の`margin-left: 28px`が不均等(文字→★が28px、★→次の文字が56px)だったバグを修正し、`padding: 0 14px`にして両側28pxで揃えた。
- `css/style.css`内の各`/* ===== セクション名 ===== */`バナーの直下に、そのブロックが何を担当しているかの一行説明コメントを追加済み。
- `external/champions/index.html`の年度見出しは単純な西暦(例: 2026)ではなく、正式名称「第◯回全日本ディアボロ選手権大会(AJDC◯◯◯◯)」に変換して表示している(`formatYearTitle()`、西暦-2011を回数として漢数字化)。2012年だけ特別扱いで「プレ日本ディアボロ大会(2012)」と表示(2012は「第1回」ではない)。
- CHAMPIONSセクションの「すべて見る」リンクは `external/champions/index.html`(歴代チャンピオン一覧ページ)に接続済み。このページは他のサブページ(検定ページ等)と同じ構成(共通ヘッダー・フッター・`.page-title`帯・共通の`css/style.css`/`js/main.js`を読み込む)で統一されている。CHAMPIONS POKER(`external/champions-poker/`)とは違い、独自CSS/JSは持たず、ページ固有のスタイルは本体`css/style.css`内の「Champions Archive」セクションに追記、データ取得・カード描画スクリプトはこのページ末尾にインライン`<script>`として記述(検定ページの動画モーダルスクリプトと同じ流儀)。
- `external/champions/data/champions.json`は2026・2025・2024年度分に、`images/champions/<年度>/<年度2桁>champ<略称>.png`(例: `images/champions/2026/26champMI.png`)の実写真を`image`フィールドで割り当て済み(略称対応: MI=男子個人総合, WI=女子個人総合, MJ=男子個人総合ジュニア, WJ=女子個人総合ジュニア, M1DHA=男子1ディアボロ水平軸固定, M1DHB=男子1ディアボロ水平軸ベアリング, M1DV=男子1ディアボロ垂直軸, 2DA=2ディアボロ固定軸, 2DB=2ディアボロベアリング軸, 3D=3ディアボロ部門)。2024年度はその年の女子部門優勝者がいなかったため8件のみ(WI/WJ無し)。この部門順(MI→WI→MJ→WJ→M1DHA→M1DHB→M1DV→2DA→2DB→3D、その後に高校生男子個人総合/女子1ディアボロ/団体/1ディアボロ部門/2ディアボロ部門 等の旧分類)で**全年度**のカードを並び替え済み(該当しない部門が無い年はスキップされるだけで欠落なし)。レンダリング側(`external/champions/index.html`)は`c.image`があればそれを使い、なければ`images/poker/cardback.png`にフォールバックする。2023年度以前はまだ`image`フィールドが無いため全件cardback.pngのまま(「仮置き」の注記もこの境界を自動検出して2023年度の直前に表示される)。今後、別の年度の実写真フォルダ(`images/champions/<年度>/`)が用意された場合は、同じ命名規則(`<年度2桁>champ<略称>.png`)で揃えれば同様にchampions.jsonへ`image`フィールドを追加できる。
- `external/champions/data/champions.json`は`AJDC_全日本ディアボロ選手権_選手別成績一覧.csv`(プロジェクトルート)から順位=1の行を年度別・部門別に抽出して生成したもの(チャレンジクラスは元データが部分的に壊れているため除外)。選手の実写真がまだないので、カード画像は全件 `images/poker/cardback.png` を仮置き。データは2012〜2026年・全121件。CSVが更新された場合はchampions.jsonの再生成が必要(現状は自動連携ではなく一度生成したJSONを置いているだけ)。
- CHAMPIONS POKERは `external/champions-poker/`(独自のindex.html・css/style.css・js/main.js)に完全分離して移植済み。トップページ(index.html)・本体のcss/style.css・js/main.jsからは関連コードを全て削除した。本体のCHAMPIONSセクション(カルーセル10枚・シャッフル機能)とは無関係で、現状トップページからのリンクは設置していない(直接 `external/champions-poker/index.html` を開く運用)。
- ヘッダー検索を展開すると `.sns-links` が幅ゼロに折りたたまれ `.header-actions` の幅が変化し、`justify-content: space-between` の再配分で `.main-nav` が右にずれるバグがあった。`.sns-links.is-hidden` は幅を保持したまま `opacity:0` で見た目だけ隠す方式に修正済み(検索入力欄自体は `position: absolute` でレイアウト幅に影響しない)。
- 全9ページ(index.html含む)の`<script src=".../js/main.js">`に`?v=N`のクエリを統一して付与済み(以前はサブページがクエリなしでキャッシュ対策が不揃いだった)。`external/champions-poker/`は独自の`js/main.js`(別ファイル、現在`?v=1`)を持つため対象外。今後JSを編集したら、index.htmlだけでなく全ページのこのクエリ番号を揃えて上げること。
- 現在のJSバージョン: `main.js?v=28`
- モバイルのハンバーガーメニュー展開は、以前`js/main.js`内でJSが直接`mainNav.style.xxx`を書き換えて見た目を作っていたが、CSSクラス(`.main-nav.open`)で見た目を管理する方式にリファクタ済み。JS側は`mainNav.classList.toggle('open')`のみを行う。見た目を調整したい場合は`css/style.css`の`.main-nav.open`を編集すればよい。
- トップページCHAMPIONSセクション(`#championsTrack`)の10枚は、架空の選手名(final_athlete_1〜10.jpg)から2026年度の実際の現役チャンピオン10名(`images/champions/2026/26champ*.png`、`external/champions/data/champions.json`の2026年度データと同じ人物・部門・並び順)に更新済み。
- CHAMPIONSカルーセル(10枚)もリロードごとにFisher-Yatesで表示順をシャッフルする(`championsTrack`の子要素を並び替えてから`items`配列を取得)。CHAMPIONS POKER(5枚抽選・重複あり)とは別の仕組み。
- CHAMPIONS POKERの画像は `images/champions/` ではなく `images/poker/` を参照(現在は final_athlete_1〜5.jpg の5枚のみ、テスト段階の限定プール)
- CHAMPIONS POKERのカードは初期状態で `images/poker/cardback.png`(裏面)を表示し、クリックで個別にフリップして表のチャンピオン情報が現れる仕組み(`.poker-card` / `.poker-card-inner` / `.poker-card-face--back` / `.poker-card-face--champion`、CSS 3D flip)。引き直しボタンで再描画すると全カード裏面の状態にリセットされる。

## 既知の保留事項 / 未対応

- **AJDC/OIDC/TIDCの既存ミラーは当面修復対象外**。この3つの特設サイトは後日別途新規に作り直す方針のため、現時点では `external/AJDC/`・`external/OIDC/`・`external/TIDC/` 内の古いHTML、外部依存、欠損アセットを直さなくてよい。トップや共通ナビからのリンク先としては残すが、デザイン統一・ローカル完全ミラー化・TIDCの不足ファイル補完は後続タスクに回す。
- **共同編集メモ**: Codex、Claude Codeなど複数のAI/エディタで触る前提。作業前後に `git status --short` を確認し、他ツールやユーザーの変更を勝手に戻さないこと。作業判断に迷う場合は、この `PROJECT_NOTES.md` と `AGENTS.md` を先に読む。
- **Git管理**: このフォルダはGit管理対象にする。`.gitignore` ではOS/エディタ/一時ファイルのみを除外し、HTML/CSS/JS/画像素材は基本的に追跡対象。画像の元PNG/PSDは重いが、削除指示があるまで残す方針。
- **細かい整備予定(一つずつ確認して進める)**:
  - `js/main.js` の検索インデックス内に残っている「オンラインストア」表記を、現行ナビに合わせて「オンラインショップ」に統一するか確認する。
  - 歴代チャンピオン周りのコメント/ノートに残っている「実写真があるのは2026年度のみ」系の古い記述を、現在の実データ(2024〜2026年度は実写真あり、2023年度以前は仮画像)に合わせて直す。
  - `images/image-specs.txt` の `final_athlete_1.jpg` など旧ダミー画像前提の記述を、現在の `images/champions/<年度>/*.webp` 運用に合わせて直す。
  - `PROJECT_NOTES.md` 内に過去の「現在のJSバージョン」記述が複数残っているため、最新値が読み取りやすい形に整理する。
- ルートに `diabolo_banner_*.png` や `middold.png` `middordd.png` など、ユーザーが置いたままの未使用画像ファイルが残っている(おそらく `midd.png` 採用前の試作)。削除指示はまだ受けていないのでそのままにしている。
- フッターの「プライバシーポリシー」「利用規約」はリンク先未定のため削除済み(コンテンツができたら追加)。
- `images/events/` 配下の大会バナー画像は現在どこからも参照されていない(将来イベント一覧セクションを復活させる場合用)。

## 連絡先・外部サービスの紐付け

- お問い合わせフォーム送信先: `info@diabolo.jp`(FormSubmit経由)。**重要**: FormSubmitは新しい送信先アドレスへの最初の送信時に確認メールを送るので、`info@diabolo.jp`の受信箱を見られる人がそのメール内のリンクをクリックして有効化するまで、フォーム送信が実際には届かない。本番公開前に必ず一度テスト送信して有効化しておくこと(旧テスト用アドレス`juggler.arata@gmail.com`からは変更済み)。
- お問い合わせフォームのスパム対策・実装の完成度を強化済み(`external/contact/index.html`):
  - `_captcha`を`false`→`true`に変更(以前は無効化されていた)。
  - FormSubmit公式のハニーポット欄(`_honey`、画面外に飛ばすCSSで人間には見えない)を追加。
  - お名前・メール・お問い合わせ内容に`required`属性を追加し、送信前に`contactForm.reportValidity()`でブラウザ標準の検証を行うようにした。
  - 送信処理を`fetch` + `FormData`によるAjax送信に変更(`Accept: application/json`ヘッダーでFormSubmitがJSONを返すモードを使用)。送信中はボタンを無効化+「送信中…」表示、成功時はフォームを隠して`#contactFormResult`に完了メッセージを表示、失敗時はエラーメッセージ+`mailto:info@diabolo.jp`リンク+「フォームに戻る」ボタンを表示する(ページ離脱なしで完結する)。
  - **ハマったポイント**: `.contact-form { display: flex; }`という著者スタイルが、ブラウザ標準の`[hidden]{display:none}`より優先されてしまい、JSで`contactForm.hidden = true`としても見た目上消えないバグがあった。`.contact-form[hidden] { display: none; }`を明示的に追加して解決(リセットCSSの全要素セレクタが無効化されたバグと同種の「同じ詳細度では記述順/出自が勝つ」パターン)。
  - フォームと結果表示(`#contactFormResult`)は`.contact-grid`の2カラムレイアウトを崩さないよう、`.contact-form-col`という共通の親divでまとめている。
  - Googleカレンダーiframe(`#contactCalendarIframe`)の下端とフォーム(`#contactForm`)の下端を揃えるため、固定の`height`では揺れる(フォントの読み込みや内容変化で高さが微妙に変わる)ことを避け、JSで`formRect.bottom - iframeRect.top`を都度計算してiframeの高さに反映している(`load`/`resize`時に再計算)。800px以下(`.contact-grid`が1カラムになる`@media`の境目)では合わせる必要がないので計算をスキップし、HTML側のデフォルト`height="475"`に戻す。
- 営業時間・在室スケジュール: Googleカレンダー埋め込み(`japandiaboloassociation@gmail.com`)
- SNS: X総合 `@Japan_Diabolo` / X店舗 `@diaboloshop` / Facebook `japandiabolo` / YouTube `@JapanDiabolo`
