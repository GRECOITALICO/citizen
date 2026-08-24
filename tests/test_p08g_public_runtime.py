"""P0.8G — public 0.4.2.1 artifact and installer door."""
from __future__ import annotations

import hashlib
import json
import os
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release" / "0.4.2.1"
WHEEL = RELEASE / "conrrad_citizen-0.4.2.1-py3-none-any.whl"
EXPECTED_SHA = "fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9"
FROZEN_SHA = "0b4eb6d336352901e783f747bc5f2cc1775f0822ec1be17c145143ea6a4457ce"
TAG = "citizen-runtime-0.4.2.1"
FROZEN_TAG = "citizen-runtime-0.4.2"
PUBLIC_WHEEL_URL = (
    f"https://raw.githubusercontent.com/GRECOITALICO/citizen/{TAG}"
    f"/release/0.4.2.1/conrrad_citizen-0.4.2.1-py3-none-any.whl"
)
FROZEN_WHEEL_URL = (
    f"https://raw.githubusercontent.com/GRECOITALICO/citizen/{FROZEN_TAG}"
    f"/release/0.4.2/conrrad_citizen-0.4.2-py3-none-any.whl"
)
SOURCE_COMMIT = "44246a3ffa9f789c40fe023a0d72a053dc08088b"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class TestLocalPublicArtifact(unittest.TestCase):
    def test_public_wheel_exists(self):
        self.assertTrue(WHEEL.is_file(), WHEEL)

    def test_public_wheel_sha(self):
        self.assertEqual(_sha256(WHEEL), EXPECTED_SHA)

    def test_provenance(self):
        prov = json.loads((RELEASE / "PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertEqual(prov["artifact"], "conrrad_citizen-0.4.2.1-py3-none-any.whl")
        self.assertEqual(prov["package_version"], "0.4.2.1")
        self.assertEqual(prov["runtime_version"], "0.4.2")
        self.assertEqual(prov["source_repository"], "GRECOITALICO/CONRRAD-CITIZEN")
        self.assertEqual(prov["source_commit"], SOURCE_COMMIT)
        self.assertEqual(prov["wheel_sha256"], EXPECTED_SHA)
        self.assertEqual(prov["frozen_public_0_4_2"]["sha256"], FROZEN_SHA)
        self.assertIn("not the frozen 0.4.2", prov["note"].lower())
        self.assertIn("install != sync", prov["note"].lower())
        self.assertIn("none", prov["signing"].lower())

    def test_frozen_0_4_2_checksum_unchanged(self):
        text = (ROOT / "release" / "0.4.2" / "SHA256SUMS.txt").read_text(encoding="utf-8")
        self.assertIn(f"{FROZEN_SHA}  conrrad_citizen-0.4.2-py3-none-any.whl", text)


class TestDocs(unittest.TestCase):
    def test_readme_install_consistency(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        for text in (readme, install):
            self.assertIn("0.4.2.1", text)
            self.assertIn(TAG, text)
            self.assertIn(EXPECTED_SHA, text)
            self.assertIn(
                f"https://raw.githubusercontent.com/GRECOITALICO/citizen/{TAG}/release/0.4.2.1/",
                text,
            )
            self.assertIn("citizen-runtime-0.4.2.1/install.sh", text)
            self.assertIn("INSTALL", text)
            self.assertIn("Birth", text)
            self.assertIn("SYNC", text)
            self.assertIn("IMPLEMENTED_NOT_PUBLIC", text)
            self.assertNotIn(
                "curl -fsSL https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-runtime-0.4.2/install.sh | bash",
                text.split("## Advanced", 1)[0] if "## Advanced" in text else text,
            )

    def test_no_auto_sync_documented(self):
        for name in ("README.md", "INSTALL.md", "install.sh"):
            plain = (ROOT / name).read_text(encoding="utf-8").lower().replace("*", "")
            self.assertIn("does not", plain)
            self.assertIn("sync", plain)
        install_sh = (ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertNotIn('citizen" sync', install_sh)
        self.assertNotIn("citizen' sync", install_sh)
        self.assertNotIn("one_click_update", install_sh)
        self.assertIn('citizen" install', install_sh)

    def test_no_destructive_primary_installer(self):
        src = (ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertNotIn("kill -9", src)
        self.assertNotRegex(src, r"\bkill\b")
        self.assertNotIn("rm -rf", src)
        self.assertNotIn("pip uninstall", src)
        self.assertNotIn("pip3 uninstall", src)
        self.assertIn(EXPECTED_SHA, src)
        self.assertIn("0.4.2.1", src)
        hist = (ROOT / "historical" / "install-0.4.2-destructive.sh").read_text(encoding="utf-8")
        self.assertIn("DEPRECATED", hist)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        first = readme.split("## Advanced", 1)[0]
        self.assertIn("citizen-runtime-0.4.2.1/install.sh", first)
        self.assertNotIn("historical/install-0.4.2-destructive.sh | bash", first)

    def test_windows_macos_honest(self):
        for name in ("README.md", "INSTALL.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("WINDOWS_STATUS=IMPLEMENTED_NOT_PUBLIC", text)
            self.assertIn("MACOS_STATUS=IMPLEMENTED_NOT_PUBLIC", text)
            self.assertNotIn("Install-Citizen.ps1", text.split("## Advanced", 1)[0])


class TestPublicNetwork(unittest.TestCase):
    def test_frozen_0_4_2_still_public(self):
        req = urllib.request.Request(FROZEN_WHEEL_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as resp:
            self.assertEqual(resp.status, 200)

    def test_public_tag_and_anonymous_download(self):
        if os.environ.get("P08G_SKIP_LIVE") == "1":
            self.skipTest("live tag check skipped")
        req = urllib.request.Request(PUBLIC_WHEEL_URL, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = resp.status
                data = resp.read()
        except urllib.error.HTTPError as e:
            self.fail(f"public wheel not retrievable: HTTP {e.code} {PUBLIC_WHEEL_URL}")
        self.assertEqual(status, 200)
        self.assertEqual(hashlib.sha256(data).hexdigest(), EXPECTED_SHA)


if __name__ == "__main__":
    unittest.main()
