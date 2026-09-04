# Overnight Run Plan

## Objective

2026 World Diabolo Contest向けに、左側へ既存の公式ロゴを載せられる余白、右側に競技用ディアボロ、台湾らしい背景を共通条件とする16:9画像を、異なる8コンセプトで制作する。ヒーローとPICK UPの両方で同じ画像を使える候補セットとして、比較可能なプレビューと検証記録を明朝までに残す。

## Scope

- Working directory: `/Users/arata/Library/Mobile Documents/com~apple~CloudDocs/claude code files/web-projects/diabolo-redesign-mock`
- Writable paths: `images/pickup/wdc2026-concepts/`, `overnight-runs/2026-08-25-wdc2026-eight-concepts/`
- Baseline branch: `feature/wdc-2026-event-refresh`
- Baseline commit: `f9807689d54b0cf1871b1497150c961e59d330bc`
- Protected current assets: `images/pickup/wdc2026-v1.webp`, `images/pickup/wdc2026-v2.webp`
- Protected consumer files: `index.html`, `css/style.css`, `MAINTENANCE_GUIDE.md`, `PROJECT_NOTES.md`
- Reporting time: 2026-08-25 07:00 JST（完了が早い場合はその時点で報告）

## Definition of Done

- 16:9の候補画像が8案あり、各案が別の台湾コンセプトを持つ。
- 全案で左側約42%が公式ロゴ用の暗く読みやすい余白になっている。
- 全案で右側のディアボロが、左右対称の2つのカップと細い中央軸を持つ正しい競技用形状で、完全に画面内へ収まっている。
- 画像内に文字、偽ロゴ、人物、透かしがない。
- ヒーローとPICK UPで同一ファイルを使う前提の比較用プレビューがある。
- 現行サイトの参照先は変更しない。

## Allowed Actions

- Read project files and applicable instructions.
- Built-in image generation calls, one distinct prompt per concept.
- Save generated outputs under `images/pickup/wdc2026-concepts/` without overwriting existing files.
- Convert PNG outputs to WebP and create local comparison artifacts.
- Run local image-dimension, file-integrity, Git-status, HTML preview, desktop, and 390px mobile checks.

## Prohibited Actions

- Do not push, deploy, publish, send external messages, purchase, or change secrets.
- Do not delete user data.
- Do not modify `index.html`, `css/style.css`, existing WDC images, release candidates, or production references.
- Do not stage or commit files.
- Do not resolve or overwrite pre-existing dirty worktree changes.

## Stop Conditions

- Record direction-changing creative choices for the user; do not silently select a production winner.
- Stop unsafe work if the protected baseline files change unexpectedly.
- Continue other independent concepts if one generation fails.
- Stop generating once eight valid candidates and the comparison preview exist.

## Team

- Coordinator: scope, waves, integration, report
- Explorer: sequential read-only inventory and concept design
- Writer: primary Codex process only; writes only to the two approved paths
- Verifier: sequential independent re-inspection after generation

## Verification

- Confirm dimensions and format for every candidate.
- Inspect each image visually for composition, Taiwanese setting, and diabolo geometry.
- Check a comparison sheet at desktop and 390px mobile proportions.
- Run `git diff --check` and compare protected-file hashes against the baseline.
- Record unresolved visual judgment separately from technical validity.
