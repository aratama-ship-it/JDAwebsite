#!/usr/bin/env python3
"""公開候補の境界検査に関する回帰テスト。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_release import copy_path, validate_copy_source
from release_config import IMAGE_FILES, LIVE_LINK_REPLACEMENTS
from verify_release import is_forbidden_public_name


class ReleaseSourceSafetyTests(unittest.TestCase):
    def test_regular_source_tree_is_copied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "external" / "about"
            source.mkdir(parents=True)
            (source / "index.html").write_text("safe", encoding="utf-8")
            destination = root / "candidate" / "about"

            copy_path(source, destination, root)

            self.assertEqual((destination / "index.html").read_text(encoding="utf-8"), "safe")

    def test_nested_source_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(temp_dir)
            source = root / "external" / "about"
            source.mkdir(parents=True)
            outside = Path(outside_dir) / "secret.txt"
            outside.write_text("not public", encoding="utf-8")
            (source / "leak.txt").symlink_to(outside)

            with self.assertRaisesRegex(RuntimeError, "シンボリックリンク"):
                validate_copy_source(source, root)

    def test_source_outside_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as outside_dir:
            source = Path(outside_dir) / "outside.html"
            source.write_text("not public", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "リポジトリ外"):
                validate_copy_source(source, Path(root_dir))


class ReleaseFilenameSafetyTests(unittest.TestCase):
    def test_server_control_and_hidden_names_are_rejected(self) -> None:
        for name in (".htaccess", ".HTACCESS", ".user.ini", "web.config", "WEB.CONFIG", ".well-known"):
            with self.subTest(name=name):
                self.assertTrue(is_forbidden_public_name(name))

    def test_normal_static_names_are_allowed(self) -> None:
        for name in ("index.html", "style.css", "main.js", "champions.json", "photo.webp"):
            with self.subTest(name=name):
                self.assertFalse(is_forbidden_public_name(name))

    def test_release_images_exclude_design_experiments(self) -> None:
        forbidden_fragments = ("concepts", "neon", "overlay", "diabolo-v1", "diabolo-v2")
        for image_path in IMAGE_FILES:
            with self.subTest(image_path=image_path):
                self.assertFalse(any(fragment in image_path for fragment in forbidden_fragments))

    def test_live_event_links_are_absolute_production_urls(self) -> None:
        expected_paths = ("/AJDC/", "/OIDC/", "/TIDC/jp/")
        values = set(LIVE_LINK_REPLACEMENTS.values())

        for path in expected_paths:
            with self.subTest(path=path):
                self.assertIn(f"https://diabolo.jp{path}", values)
        for url in values:
            with self.subTest(url=url):
                self.assertTrue(url.startswith("https://diabolo.jp/"))

    def test_certification_passed_lists_match_current_legacy_site(self) -> None:
        certification_html = (
            Path(__file__).resolve().parent.parent / "external" / "certification" / "index.html"
        ).read_text(encoding="utf-8")

        for grade in range(1, 5):
            expected_url = (
                f"https://diabolo.jp/certification/grade_{grade}_list(20260813).pdf"
            )
            with self.subTest(grade=grade):
                self.assertIn(expected_url, certification_html)
        self.assertIn("(2026.8.15 更新)", certification_html)


class ContactFormConfigurationTests(unittest.TestCase):
    def test_contact_form_uses_native_multipart_submission(self) -> None:
        contact_html = (
            Path(__file__).resolve().parent.parent / "external" / "contact" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('action="https://formsubmit.co/info@diabolo.jp"', contact_html)
        self.assertIn('method="POST" enctype="multipart/form-data"', contact_html)
        self.assertIn(
            'name="_next" value="https://www.diabolo.jp/external/contact/?submitted=1"',
            contact_html,
        )
        self.assertIn('contactForm.submit();', contact_html)
        self.assertNotIn('fetch(contactForm.action', contact_html)

    def test_contact_attachment_limit_matches_formsubmit_limit(self) -> None:
        contact_html = (
            Path(__file__).resolve().parent.parent / "external" / "contact" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn("添付ファイル合計10MBまで", contact_html)
        self.assertIn("10 * 1024 * 1024", contact_html)


if __name__ == "__main__":
    unittest.main()
