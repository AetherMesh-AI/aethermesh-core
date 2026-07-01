import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aethermesh_core.identity import (
    IdentityPersistenceError,
    _default_goos,
    _fallback_parts,
    _machine_fingerprint,
    _read_or_empty,
    _read_text_file,
    _run_command,
    _run_or_empty,
    deterministic_machine_node_id,
    load_or_create_identity,
)


class IdentityPersistenceTests(unittest.TestCase):
    def test_missing_identity_file_is_created_with_deterministic_machine_node_id(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "deep" / "nested" / "local-node.json"

            identity = load_or_create_identity(
                identity_path,
                goos="linux",
                read_file=lambda path: {
                    "/etc/machine-id": " machine-a\n",
                    "/var/lib/dbus/machine-id": "dbus-a",
                }[path],
                run_command=lambda name, *args: "product-a",
                read_hostname=lambda: "host-a",
            )
            persisted = json.loads(identity_path.read_text(encoding="utf-8"))

        expected = "local-" + hashlib.sha256(b"machine-a|dbus-a|product-a").hexdigest()
        self.assertEqual(identity.node_id, expected)
        self.assertEqual(
            persisted,
            {"version": 1, "node": {"node_id": identity.node_id}},
        )

    def test_deterministic_machine_node_id_filters_empty_parts(self) -> None:
        node_id = deterministic_machine_node_id(
            goos="linux",
            read_file=lambda path: {
                "/etc/machine-id": "\n",
                "/var/lib/dbus/machine-id": "dbus-a\n",
            }[path],
            run_command=lambda name, *args: "  ",
            read_hostname=lambda: "ignored-host",
        )

        self.assertEqual(
            node_id,
            "local-" + hashlib.sha256(b"dbus-a").hexdigest(),
        )

    def test_deterministic_machine_node_id_uses_hostname_fallback(self) -> None:
        node_id = deterministic_machine_node_id(
            goos="linux",
            read_file=lambda path: (_ for _ in ()).throw(FileNotFoundError(path)),
            run_command=lambda name, *args: (_ for _ in ()).throw(OSError(name)),
            read_hostname=lambda: " fallback-host\n",
        )

        self.assertEqual(
            node_id,
            "local-" + hashlib.sha256(b"fallback-os|linux|fallback-host").hexdigest(),
        )

    def test_machine_fingerprint_uses_platform_specific_sources(self) -> None:
        self.assertEqual(
            _machine_fingerprint(
                "darwin",
                read_file=lambda path: "unused",
                run_command=lambda name, *args: " DARWIN-UUID ",
                read_hostname=lambda: "ignored",
            ),
            "DARWIN-UUID",
        )
        self.assertEqual(
            _machine_fingerprint(
                "windows",
                read_file=lambda path: "unused",
                run_command=lambda name, *args: (
                    " WINDOWS-UUID " if name == "wmic" else "POWERSHELL-UUID"
                ),
                read_hostname=lambda: "ignored",
            ),
            "WINDOWS-UUID|POWERSHELL-UUID",
        )
        self.assertEqual(
            _machine_fingerprint(
                "plan9",
                read_file=lambda path: "unused",
                run_command=lambda name, *args: "unused",
                read_hostname=lambda: "ignored",
            ),
            "unknown-os|plan9",
        )

    def test_machine_fingerprint_helper_edges_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            value_path = Path(temp_dir) / "value.txt"
            value_path.write_text(" value\n", encoding="utf-8")

            self.assertEqual(_read_text_file(str(value_path)), "value")

        self.assertEqual(_read_or_empty(None, "/missing"), "")
        self.assertEqual(_run_or_empty(None, "ignored"), "")
        self.assertEqual(
            _run_or_empty(
                lambda name, *args: (_ for _ in ()).throw(
                    subprocess.CalledProcessError(1, name)
                ),
                "false",
            ),
            "",
        )
        self.assertEqual(_fallback_parts("linux", None), ["fallback-os", "linux"])
        self.assertEqual(
            _fallback_parts(
                "linux", lambda: (_ for _ in ()).throw(OSError("hostname"))
            ),
            ["fallback-os", "linux"],
        )
        self.assertEqual(
            _fallback_parts("linux", lambda: " \n"), ["fallback-os", "linux"]
        )
        self.assertEqual(
            _fallback_parts("linux", lambda: " host "), ["fallback-os", "linux", "host"]
        )

    def test_default_goos_maps_common_python_platforms(self) -> None:
        cases = [
            ("linux", "linux"),
            ("linux2", "linux"),
            ("darwin", "darwin"),
            ("win32", "windows"),
            ("freebsd13", "freebsd13"),
        ]
        for platform_name, expected in cases:
            with self.subTest(platform_name=platform_name):
                with patch("aethermesh_core.identity.sys.platform", platform_name):
                    self.assertEqual(_default_goos(), expected)

    def test_default_command_runner_trims_stdout(self) -> None:
        self.assertEqual(
            _run_command(sys.executable, "-c", "print(' command-value ')"),
            "command-value",
        )

    def test_existing_identity_file_reuses_node_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            identity_path.write_text(
                json.dumps({"version": 1, "node": {"node_id": "local-stable-node"}}),
                encoding="utf-8",
            )

            identity = load_or_create_identity(identity_path)

        self.assertEqual(identity.node_id, "local-stable-node")

    def test_malformed_identity_json_raises_clear_error_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            identity_path.write_text("{not json", encoding="utf-8")

            with self.assertRaisesRegex(IdentityPersistenceError, "malformed"):
                load_or_create_identity(identity_path)

            self.assertEqual(identity_path.read_text(encoding="utf-8"), "{not json")

    def test_unsupported_identity_version_raises_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            original = json.dumps({"version": 2, "node": {"node_id": "local-future"}})
            identity_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(IdentityPersistenceError, "version 1"):
                load_or_create_identity(identity_path)

            self.assertEqual(identity_path.read_text(encoding="utf-8"), original)

    def test_invalid_identity_node_id_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            identity_path.write_text(
                json.dumps({"version": 1, "node": {"node_id": ""}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(IdentityPersistenceError, "node.node_id"):
                load_or_create_identity(identity_path)

    def test_identity_error_messages_are_stable(self) -> None:
        cases = [
            ([], "identity JSON must be an object"),
            (
                {"version": 2, "node": {"node_id": "local-future"}},
                "identity JSON must contain version 1",
            ),
            (
                {"version": 1, "node": []},
                "identity JSON field 'node' must be an object",
            ),
            (
                {"version": 1, "node": {"node_id": ""}},
                "identity JSON field 'node.node_id' must be a non-empty string",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            for document, expected_message in cases:
                with self.subTest(expected_message=expected_message):
                    identity_path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertRaises(IdentityPersistenceError) as cm:
                        load_or_create_identity(identity_path)
                    self.assertEqual(str(cm.exception), expected_message)


if __name__ == "__main__":
    unittest.main()
