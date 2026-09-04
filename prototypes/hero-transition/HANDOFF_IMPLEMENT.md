# 引き継ぎ: ディアボロ・トランジション（抜き窓）を diabolo.jp モック本体に実装する

作成: 2026-08-28 ／ 承認済み仕様（本人確認済み。プロトタイプを見て「完璧です」と判断）

この文書だけで作業できるように書いてある。別マシン・別エージェント（Codex等）でも、
このファイルと参照実装を読めば実装できる。

---

## 0. 前提と置き場所

- ワークスペースは iCloud Drive 上の共有フォルダ。**パスに空白があるので引用符を徹底する。**
- 対象プロジェクト（絶対パス）:
  `/Users/arata/Library/Mobile Documents/com~apple~CloudDocs/claude code files/web-projects/diabolo-redesign-mock`
- **参照実装（動作確認済み・これが正）**:
  `prototypes/hero-transition/index.html`
  → 動きの実物。この中の `playTumble()` と `applyCutout()` と `sidePath()` が移植元。
- 他のエージェントも同じファイルを触る前提。**編集前に必ず現物を読み直す。**
- **ファイルの削除・移動はしない。**

---

## 1. やること（1行）

ヒーロー画像の切り替えを、現在のクロスフェードから
**「軸を縦にしたディアボロのシルエットが横切り、その輪郭を境に前後の画像が入れ替わる」抜き窓の演出**に置き換える。

---

## 2. 現状（実装前に確認した事実）

| 項目 | 現状 |
|---|---|
| ヒーロー本体 | `index.html` の `<section class="hero" id="top">` 内 `<div class="hero-slideshow" id="heroSlideshow">` |
| スライド | `.hero-slide` が複数。表示中のものに `is-active` |
| `.hero-slide` のCSS | `position:absolute; inset:0; opacity:0; visibility:hidden; transition:opacity 1s ease; pointer-events:none`（`css/style.css` 346行付近） |
| `.hero-slide.is-active` | `opacity:1; visibility:visible; pointer-events:auto` |
| `.hero` | `position:relative; margin-top:76px; height:662px; overflow:hidden` |
| 切り替えJS | `js/main.js` の `heroSlideshow` ブロック内 `goToSlide(index)`。クラスの付け外しのみ |
| ドット | `.hero-dot`。クリックで `goToSlide(i)` + `resetAutoplay()` |
| 自動送り | `setInterval(nextSlide, 5000)` |
| キャッシュ対策 | `index.html` から `css/style.css?v=69` と `js/main.js?v=36` を読み込み（2026-08-28時点の実測値） |

---

## 3. 仕様（確定。ここは判断せず、この数値どおりに実装する）

### 3-1. ディアボロの形

寸法は実測値（`3d/reference/diabolo/`、2026-08-24 ノギス実測・白カップ）。単位mm。

```js
var D = {
  R: 65.45,        // カップ外径130.9 / 2 …実測
  CUP_H: 61.6,     // カップ高さ …実測
  R_AXLE: 6,       // 軸半径 …未測定（仮値）
  AXLE_GAP: 10     // 露出した軸の長さ …未測定（仮値）
};
D.HALF_W = D.CUP_H + D.AXLE_GAP / 2;   // = 66.6
```

シルエット生成（**参照実装からそのまま移植する。値を変えない**）:

```js
// 軸が水平の基準形。実物のカップはベル型で、縁の近くは軸とほぼ平行に立ち上がり、
// ハブに近づくほど急に絞られる。三次ベジエでその変化を出している。
function sidePath(){
  var R = D.R, hw = D.HALF_W, ax = D.AXLE_GAP / 2, ar = D.R_AXLE;
  var lip = 3.2;                          // 縁の丸み（近似）
  var dx = hw - lip - ax, dy = R - ar;
  var e1x = 0.42 * dx, e1y = 0.06 * dy;   // 縁側の制御点
  var e2x = 0.18 * dx, e2y = 0.55 * dy;   // ハブ側の制御点
  function n(v){ return v.toFixed(2); }
  return [
    "M " + n(-hw) + " " + n(-R + lip),
    "Q " + n(-hw) + " " + n(-R) + " " + n(-hw + lip) + " " + n(-R),
    "C " + n(-hw + lip + e1x) + " " + n(-R + e1y) + " " + n(-ax - e2x) + " " + n(-ar - e2y) + " " + n(-ax) + " " + n(-ar),
    "L " + n(ax) + " " + n(-ar),
    "C " + n(ax + e2x) + " " + n(-ar - e2y) + " " + n(hw - lip - e1x) + " " + n(-R + e1y) + " " + n(hw - lip) + " " + n(-R),
    "Q " + n(hw) + " " + n(-R) + " " + n(hw) + " " + n(-R + lip),
    "L " + n(hw) + " " + n(R - lip),
    "Q " + n(hw) + " " + n(R) + " " + n(hw - lip) + " " + n(R),
    "C " + n(hw - lip - e1x) + " " + n(R - e1y) + " " + n(ax + e2x) + " " + n(ar + e2y) + " " + n(ax) + " " + n(ar),
    "L " + n(-ax) + " " + n(ar),
    "C " + n(-ax - e2x) + " " + n(ar + e2y) + " " + n(-hw + lip + e1x) + " " + n(R - e1y) + " " + n(-hw + lip) + " " + n(R),
    "Q " + n(-hw) + " " + n(R) + " " + n(-hw) + " " + n(R - lip),
    "Z"
  ].join(" ");
}
```

### 3-2. 動き

- **向きは軸が縦**（基準形から `rotate(90)`）。回転はしない。**横に平行移動するだけ。**
- 大きさ: `scale = (heroH * 1.02) / (D.HALF_W * 2)`
  （縦がヒーローの高さいっぱい。上下の端に隙間が出ないよう1.02倍）
- 進行方向の半分: `halfSpanX = D.R * scale`
- 移動: `x` は `-halfSpanX` → `heroW + halfSpanX`（画面外から画面外まで）
- 縦位置: `y = heroH / 2`
- **所要時間 1600ms**、イージングは `easeInOutCubic`
  `t < .5 ? 4t³ : 1 - (-2t+2)³/2`
- `heroW` / `heroH` は `.hero` の実ピクセル寸法を毎回計測して使う（固定値にしない）

### 3-3. 抜き窓（切り替えの肝）

次のスライドに SVG の `clipPath` を当てる。クリップは **2つの図形の和**:

1. `<path>` … ディアボロのシルエット（上の `sidePath()`、`rotate(90)` 済み）
2. `<rect>` … `x=0, y=0, width = ディアボロの中心のX座標, height = heroH`

**`width` は「ディアボロの中心」までにする。後ろ側の縁（`x - halfSpanX`）で止めてはいけない。**
止めるとシルエットがくびれている中央付近で矩形とシルエットの間に三日月状の隙間ができ、
そこに前の画像が残る（実際に起きた不具合。修正済み）。
中心まで埋めるとシルエットの左半分が完全に矩形の内側に入り、
**境界はディアボロの前側（右）の輪郭だけ**になり、左右が完全に入れ替わる。

`clipPath` は `clipPathUnits="userSpaceOnUse"` を使う。
このとき user space は**参照元HTML要素（`.hero-slide`）のボーダーボックス＝ピクセル**なので、
座標はステージ座標ではなく**ピクセルで**組む。

`rotate(90)` と `scale` はピクセル座標の行列に展開する:

```js
// scale は 3-2 の値、sx/sy はステージ→pxの倍率
// (このプロジェクトでは実寸pxで直接組むので sx = sy = 1 でよい)
shape.setAttribute("transform",
  "matrix(0," + scale + "," + (-scale) + ",0," + x + "," + y + ")");
```

### 3-4. 輪郭線

ディアボロの輪郭は**全体を白い線で描く**（左半分は次の画像の上に乗る。本人が見て了承済み）。

- `stroke: rgba(255,255,255,.9)`、`fill: none`
- `stroke-width` は **`2.2 / scale`**（拡大しても線の太さが一定に見えるように）
- 描画用SVGはヒーローに重ねる。`pointer-events: none`、`z-index` はスライドより上、ドットより下

### 3-5. 動きを減らす設定

`window.matchMedia("(prefers-reduced-motion: reduce)").matches` が真のとき、
**演出はせず即座に切り替える**（既存のクロスフェードにフォールバックしてよい）。

### 3-6. 保険（必須）

`requestAnimationFrame` はタブが非表示だと止まる。止まったまま切り替えが途中で固まると
ヒーローが壊れた状態で残るので、**`setTimeout(finish, duration + 600)` で強制完了させる**。
`finish()` は「最終フレームを適用してから完了処理」を1回だけ行う（二重実行を防ぐフラグを持つ）。

---

## 4. 既存機能との噛み合わせ（ここを壊さない）

1. **`goToSlide(index)` は任意のindexで呼ばれる**（ドットクリック）。次送りだけでなく任意遷移で動くこと。
2. **多重起動を防ぐ。** 演出中（1600ms）に再度呼ばれたら無視するか、現在の演出を完了させてから受ける。
   ドットクリックが効かなくなる時間が長すぎないよう、無視する場合も自動送りのタイマーはリセットする。
3. **`.hero-slide` の `transition: opacity 1s ease` が干渉する。**
   演出中は次スライドを即座に可視化する必要があるので、`is-incoming` のような状態クラスを追加し、
   そのときだけ `transition: none; opacity: 1; visibility: visible;` にする。
   **既存の `.hero-slide` / `.hero-slide.is-active` のルール自体は消さない**（低モーション時のフォールバックに使う）。
4. **演出が終わったら、インラインで付けた `clip-path` 等は必ず消す。**
   付けっぱなしだとヒーローが欠けたまま残る。
5. `.hero-slide--event`（WDCスライド）内の `hero-wdc-*` 演出や、`.hero-slide-media img` の
   `transform: scale(1)` は現状のまま壊さない。
6. **`ドット` の `is-active` の切り替えタイミング**は今までどおり（演出の開始時でよい）。

---

## 5. 変更するファイルと、忘れてはいけない作業

| ファイル | 変更内容 |
|---|---|
| `index.html` | ①`clipPath` を持つインラインSVG（`<svg width="0" height="0">` 内の `<defs>`）を追加 ②ヒーロー内に演出描画用SVGを追加 ③**`css/style.css?v=69` → `?v=70`、`js/main.js?v=36` → `?v=37`** |
| `css/style.css` | `is-incoming` 用のルール、演出用SVGの重ね方（`position:absolute; inset:0; pointer-events:none`）を追加 |
| `js/main.js` | `heroSlideshow` ブロックに演出を実装 |

**`?v=` の更新は必須。** 上げないとブラウザが古いCSS/JSを掴んでこの実装が反映されない
（このプロジェクトで繰り返し起きている）。**上げる前に現在の値を grep で確認すること**
（他の作業で既に上がっている可能性がある）。

---

## 6. 完了条件（検証可能な形で）

1. ローカルサーバを起動して確認できる（`file://` では不可）:
   ```bash
   cd "/Users/arata/Library/Mobile Documents/com~apple~CloudDocs/claude code files/web-projects/diabolo-redesign-mock" && python3 -m http.server 8000
   ```
   → `http://127.0.0.1:8000/index.html`
2. ヒーローが自動で切り替わるとき、**軸が縦のディアボロが左から右へ横切る**。
3. 横切っている最中、**ディアボロの輪郭を境に、左は次の画像・右は前の画像**になっている。
   **左側に前の画像が残る領域がない**（特に中央のくびれ付近をよく見る）。
4. ディアボロの縦の大きさが**ヒーローの高さいっぱい**で、上下に隙間がない。
5. 切り替え完了後、スライドに `clip-path` などのインラインスタイルが残っていない
   （DevToolsで `.hero-slide` の style属性を確認）。
6. ドットをクリックしても同じ演出で切り替わり、連打しても表示が壊れない。
7. コンソールエラーが0件。
8. OSの「視差効果を減らす」をONにすると、演出せず即座に切り替わる。
9. 幅 1440 / 768 / 390 で表示を確認し、いずれも破綻しない。

---

## 7. やらないこと

- 他のセクション（CHAMPIONS カルーセル、UPDATES、マーキー等）には触らない。
- ファイルの削除・移動をしない。
- 寸法・時間・イージングの値を「よくしよう」として勝手に変えない
  （変えたほうがよいと思った点があれば、実装はせず報告する）。
- **文字ランプ（写真をDIABOLOの文字で描くASCII演出）はここでは使わない。**
  別途保留中のアイデアで、diabolo.jp トップには使わない方針が決まっている。
