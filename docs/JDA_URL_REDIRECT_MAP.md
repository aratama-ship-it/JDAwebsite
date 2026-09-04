# JDA本体 公開URL・旧URL転送表

初回案: 2026-08-22  
状態更新: 2026-09-03（未公開の将来案）

## 公開URL

| 内容 | 公開URL | ソース |
|---|---|---|
| トップ | `/` | `index.html` |
| 協会について | `/about/` | `about/index.html` |
| アクセス | `/access/` | `access/index.html` |
| ディアボロ検定 | `/certification/` | `certification/index.html` |
| 歴代チャンピオン | `/champions/` | `champions/index.html` |
| お問い合わせ | `/contact/` | `contact/index.html` |
| 派遣業務 | `/dispatch/` | `dispatch/index.html` |
| 更新情報 | `/news/` | `news/index.html` |
| OTP2 | `/otp2/` | `otp2/index.html` |
| 記録一覧 | `/records/` | `records/index.html` |
| 採点規則 | `/rule/` | `rule/index.html` |

大会サイトの `/AJDC/`、`/OIDC/`、`/TIDC/jp/` は変更しない。

## 301転送を提案している旧URL

同一host内のHTTP 301案を `server-config/proposals/clean-url-cutover.conf` に保管している。本番公開ルートには `.htaccess` が存在せず、この転送は現在有効ではない。

| 旧URL | 転送先 |
|---|---|
| `/about_us.html` | `/about/` |
| `/access.html` | `/access/` |
| `/records.html` | `/records/` |
| `/rule.html` | `/rule/` |
| `/inquiry.html` | `/contact/` |
| `/performer.html` | `/dispatch/` |
| `/workshop.html` | `/dispatch/` |
| `/about_OTP2.html` | `/otp2/` |
| `/external/about/` 等の旧モック10ページ | 対応するクリーンURL |

`performer.html` と `workshop.html` は、Apacheの転送が使えないプレビュー用に静的フォールバックも新URLへ更新した。`external/` の旧モックURLにも同様の静的フォールバックを残す。

## 今回は転送しない旧URL

次は内容の移行先が未確定、または新ページに必要情報が不足するため、現時点で転送しない。旧docrootから安全に保全し、各項目のレビュー時に決定する。

- `/onlinecoaching.html`: サービス継続可否が未決定。
- `/workshops.html`: 練習会・検定予定ページであり、派遣業務とは別内容。
- `/track.html`: MP3の利用・再配布条件を新ページへ引き継いでから判断。
- `/event.html`、`/contents.html`、`/link.html`: 対応する新ページを内容確認後に決定。
- 54件の `about_*.html`: 過去イベント記事として保全/個別転送を判断。

## 公開時の確認

1. 全転送先が本番でHTTP 200になった後、専用作業として `.htaccess` の新設を承認する。
2. 旧URLが1回の301で目的URLへ着地することを確認する。
3. 転送先が200で、AJDC/OIDC/TIDCに影響しないことを確認する。
4. HTTP→HTTPS・www統一を追加した後も転送が連鎖しすぎないことを再確認する。
