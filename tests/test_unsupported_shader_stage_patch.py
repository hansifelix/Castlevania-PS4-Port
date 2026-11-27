import tempfile
import unittest
from pathlib import Path

from tools.link.patch_unsupported_shader_stage_failclosed import (
    PATCHES,
    PatchError,
    apply_patch,
)


class UnsupportedStagePatchTests(unittest.TestCase):
    def make_tree(self, root):
        for relative, (before, after) in PATCHES.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(before + "\n", encoding="utf-8")

    def test_patches_all_four_pinned_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)
            self.assertEqual(apply_patch(root), len(PATCHES))
            for relative, (_, after) in PATCHES.items():
                self.assertIn(after, (root / relative).read_text(encoding="utf-8"))

    def test_patch_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)
            self.assertEqual(apply_patch(root), len(PATCHES))
            self.assertEqual(apply_patch(root), 0)

    def test_source_drift_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)
            (root / "runtime/src/nvn/nvn_draw.cpp").write_text("changed", encoding="utf-8")
            with self.assertRaises(PatchError):
                apply_patch(root)
            self.assertIn(PATCHES["runtime/src/nvn/nvn_pipeline.cpp"][0],
                          (root / "runtime/src/nvn/nvn_pipeline.cpp").read_text(encoding="utf-8"))

    def test_symlinked_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)
            target = root / "outside.cpp"
            target.write_text(PATCHES["runtime/src/nvn/nvn_pipeline.cpp"][0], encoding="utf-8")
            path = root / "runtime/src/nvn/nvn_pipeline.cpp"
            path.unlink()
            path.symlink_to(target)
            with self.assertRaises(PatchError):
                apply_patch(root)

    def test_symlinked_root_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            actual = base / "actual"
            actual.mkdir()
            alias = base / "alias"
            alias.symlink_to(actual, target_is_directory=True)
            with self.assertRaises(PatchError):
                apply_patch(alias)


if __name__ == "__main__":
    unittest.main()
