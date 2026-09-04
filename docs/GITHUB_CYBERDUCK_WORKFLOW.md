# GitHub・Codex・Cyberduck 運用手順

## 目的

リニューアル版の正本をGitHubで管理し、Codexまたはターミナルから安全に更新できるようにします。
ロリポップ上の `diabolo.jp` は、最終確認後にCyberduckで手動反映します。

次の2工程は分離します。

1. **制作工程**: GitHub、Codex、ターミナル、GitHub Actions
2. **本番工程**: ロリポップ、Cyberduck、本人の明示承認

GitHubへのpushは、本番サーバーへのアップロードを意味しません。ただしGitHub Pagesが`main`から公開されている場合、
`main`へのマージは確認用Pagesを更新します。制作途中は作業ブランチへpushし、`main`へ直接pushしません。

## 1. 最初のGitHub認証

ターミナルで次を実行します。

```bash
gh auth login -h github.com -p https -w
gh auth status
```

ブラウザに表示される認証は本人が完了します。トークン、パスワード、FTPS情報をリポジトリやチャットへ貼りません。

## 2. 日常の制作

```bash
git status --short --branch
git switch main
git pull --ff-only
git switch -c feature/変更内容
```

Codexに作業を依頼する場合も、作業前後に現在のブランチと未コミット変更を確認します。
変更後はローカルサーバーで表示を確認します。

```bash
python3 -m http.server 8000
```

確認URLは `http://127.0.0.1:8000/index.html` です。

## 3. GitHubへ保存する

```bash
git status --short
git diff --check
git add 変更したファイル
git commit -m "変更内容"
git push -u origin 現在のブランチ名
```

Pull Requestを作成し、GitHub Actionsの `Verify safe release candidate` がPASSすることを確認します。
Codexからcommit、push、Pull Request作成まで実行できますが、push前に変更内容を報告し、対象ブランチを確認します。

## 4. Cyberduck用候補を作る

リポジトリ直下で実行します。

```bash
./scripts/prepare_release.sh
```

生成先は `release-candidate/` です。このフォルダはGit管理対象外で、毎回Git管理中のソースから再生成します。

生成物:

- `release-candidate/public/`: Cyberduckへ渡すファイル
- `release-candidate/UPLOAD_MANIFEST.md`: アップロード範囲と注意
- `release-candidate/FILELIST.sha256`: ファイル一覧とハッシュ
- `release-candidate/SOURCE_COMMIT.txt`: 元にしたGitコミット
- `release-candidate/SOURCE_STATE.txt`: 未コミット変更の有無

Cyberduckへ渡すのは **`public/` の中身** です。外側のフォルダはアップロードしません。
編集途中の確認では通常コマンドを使えますが、本番に使う最終候補はcommit後に次で作り直します。

```bash
./scripts/prepare_release.sh --require-clean
```

`SOURCE_STATE.txt` が `CLEAN` でない候補は本番に使用しません。

## 5. 本番アップロード前の停止条件

次をすべて満たすまでは接続・上書きしません。

1. ロリポップ管理画面で正式なFTPSサーバー名を確認した
2. Cyberduckの証明書名不一致が解消した、または管理者から明示的な確認を得た
3. Cyberduckで接続後、まずリモート公開ルートを読み取り確認した
4. `server-config/production-state.json` の記録とリモートの `.htaccess` の状態が一致し、`AJDC/`、`OIDC/`、`TIDC/`、`wp/` の存在を確認した（2026-09-03確認時点では公開ルートの `.htaccess` は存在しない）
5. `./scripts/prepare_release.sh --require-clean` とGitHub ActionsがPASSした
6. PC・スマートフォン表示を確認した
7. 本人が対象ファイルを確認し、本番アップロードを明示承認した

## 6. Cyberduckの使い方

- 接続方式: `FTP-SSL (Explicit AUTH TLS)`
- 転送方式: 通常の「アップロード」
- 使用しない操作: 「同期」、サーバー側ファイルの一括削除
- パスワード: 本人がCyberduckへ入力し、Gitやファイルへ保存しない

アップロード対象一覧に `AJDC/`、`OIDC/`、`TIDC/`、`wp/`、`.htaccess` が現れたら中止します。
`.htaccess` の新設・変更は通常公開に混ぜず、`server-config/README.md` に従う専用作業として扱います。

## 7. 状態の呼び分け

- **Git保存済み**: commit済み
- **GitHub保存済み**: 作業ブランチへpush済み
- **確認用Pages反映済み**: GitHub Pagesで確認済み
- **公開候補生成済み**: `release-candidate/` を生成・検証済み
- **本番反映済み**: Cyberduck転送後、`diabolo.jp`を実機確認済み

これらは別の状態です。GitHubへpushしただけで「本番公開済み」とは扱いません。
