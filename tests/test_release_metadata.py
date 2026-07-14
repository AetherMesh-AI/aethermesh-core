import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import release_metadata


class ReleaseMetadataTests(unittest.TestCase):
    def test_source_files_sha256_hashes_relative_paths_and_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "pyproject.toml"
            second = root / "src" / "aethermesh_core" / "__init__.py"
            second.parent.mkdir(parents=True)
            first.write_text("[project]\nname = 'aethermesh'\n", encoding="utf-8")
            second.write_text("__version__ = '0.2.0a0'\n", encoding="utf-8")

            digest = release_metadata.source_files_sha256(root, [second, first])

        expected = hashlib.sha256()
        for rel, content in [
            ("pyproject.toml", b"[project]\nname = 'aethermesh'\n"),
            ("src/aethermesh_core/__init__.py", b"__version__ = '0.2.0a0'\n"),
        ]:
            expected.update(rel.encode("utf-8"))
            expected.update(b"\0")
            expected.update(content)
            expected.update(b"\0")
        self.assertEqual(digest, expected.hexdigest())

    def test_source_archive_sha256_hashes_actual_archive_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir) / "source.tar.gz"
            archive.write_bytes(b"actual release source archive")

            digest = release_metadata.source_archive_sha256(archive)

        self.assertEqual(
            digest,
            hashlib.sha256(b"actual release source archive").hexdigest(),
        )

    def test_release_tag_and_name_use_numbered_alpha_version(
        self,
    ) -> None:
        metadata = release_metadata.build_release_metadata(
            release_version="0.2.0-alpha",
            source_sha256="abcdef1234567890",
            head_sha="feedfacecafebeef",
            previous_tag="v0.2.0-alpha.115",
            commits=[
                release_metadata.Commit(
                    sha="feedfacecafebeef",
                    subject="feat: add release automation",
                    author="Miyu",
                )
            ],
            build_number=116,
        )

        self.assertEqual(metadata.tag, "v0.2.0-alpha.116")
        self.assertEqual(metadata.name, "0.2.0-alpha.116")
        self.assertIn("Previous release tag: `v0.2.0-alpha.115`", metadata.notes)
        self.assertIn("- `feedfac` feat: add release automation (Miyu)", metadata.notes)
        self.assertNotIn("early", metadata.name.lower())
        self.assertNotIn("early", metadata.notes.lower())

    def test_first_release_notes_include_full_commit_list_marker(self) -> None:
        metadata = release_metadata.build_release_metadata(
            release_version="0.2.0-alpha",
            source_sha256="abc123",
            head_sha="2222222222222222",
            previous_tag=None,
            commits=[
                release_metadata.Commit(
                    "1111111111111111", "chore: initial commit", "Trevor"
                ),
                release_metadata.Commit(
                    "2222222222222222", "feat: package core", "Trevor"
                ),
            ],
            build_number=116,
        )

        self.assertIn("Commit range: full history", metadata.notes)
        self.assertIn("- `1111111` chore: initial commit (Trevor)", metadata.notes)
        self.assertIn("- `2222222` feat: package core (Trevor)", metadata.notes)

    def test_previous_alpha_release_tag_ignores_current_rerun_tag(self) -> None:
        with mock.patch.object(
            release_metadata,
            "run_git",
            return_value="v0.1.1-alpha-current\nv0.1.1-alpha-previous\n",
        ):
            tag = release_metadata.previous_alpha_release_tag(
                exclude_tag="v0.1.1-alpha-current"
            )

        self.assertEqual(tag, "v0.1.1-alpha-previous")


if __name__ == "__main__":
    unittest.main()
