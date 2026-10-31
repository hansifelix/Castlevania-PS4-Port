"""Synthetic, no-game tests of the exact 7-shard private link contract."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from check_shards import MAIN_NAMES, SDK_NAME, ZSTD_MAGIC, validate


class ShardChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.main_dir = root / "main"
        self.main_dir.mkdir()
        self.sdk_file = root / SDK_NAME
        for name in MAIN_NAMES:
            (self.main_dir / name).write_bytes(ZSTD_MAGIC + b"x" * 16)
        self.sdk_file.write_bytes(ZSTD_MAGIC + b"x" * 16)

    def test_complete(self):
        self.assertEqual(validate(self.main_dir, self.sdk_file), 7)

    def test_missing_main(self):
        (self.main_dir / next(iter(MAIN_NAMES))).unlink()
        with self.assertRaisesRegex(ValueError, "mismatch"):
            validate(self.main_dir, self.sdk_file)

    def test_duplicate_across_directories(self):
        sub = self.main_dir / "nested"
        sub.mkdir()
        (sub / next(iter(MAIN_NAMES))).write_bytes(ZSTD_MAGIC + b"x" * 16)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            validate(self.main_dir, self.sdk_file)

    def test_wrong_main_range(self):
        name = next(iter(MAIN_NAMES))
        (self.main_dir / name).rename(self.main_dir / "MAIN_0-9999.o.zst")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            validate(self.main_dir, self.sdk_file)

    def test_invalid_main_magic(self):
        (self.main_dir / next(iter(MAIN_NAMES))).write_bytes(b"nope" + b"x" * 16)
        with self.assertRaisesRegex(ValueError, "header"):
            validate(self.main_dir, self.sdk_file)

    def test_sdk_empty(self):
        self.sdk_file.write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "Invalid regular"):
            validate(self.main_dir, self.sdk_file)

    def test_sdk_wrong_name(self):
        wrong = self.sdk_file.with_name("sdk-any-other-file.o.zst")
        self.sdk_file.rename(wrong)
        with self.assertRaisesRegex(ValueError, "Unexpected SDK"):
            validate(self.main_dir, wrong)

    def test_sdk_symlink(self):
        original = self.sdk_file.with_name("target")
        self.sdk_file.rename(original)
        self.sdk_file.symlink_to(original)
        with self.assertRaisesRegex(ValueError, "Invalid regular"):
            validate(self.main_dir, self.sdk_file)


if __name__ == "__main__":
    unittest.main()
