"""No ROM required: ensure PS4 writable_root switch is pinned and fail-closed."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.ps4.patch_writable_root import patch, OLD, NEW

class WritableRootPatch(unittest.TestCase):
    def test_pinned_upstream_is_not_overwritten_for_other_platforms(self):
        original = "header\n" + OLD + "\nfooter\n"
        patched = patch(original)
        self.assertIn(NEW,patched)
        self.assertEqual(patched.count("inline std::string writable_root() { return data_root(); }"),1)
        self.assertIn("|| defined(KAZUMA_PS4)",patched)
        self.assertIn("|| defined(KAZUMA_TEST_WRITABLE_ROOT)",patched)
        self.assertEqual(patched.replace(NEW,OLD),original)
    def test_refuses_unexpected_new_upstream_header(self):
        for changed in ("",OLD+OLD,NEW,OLD.replace("data_root()","/app0")):
            with self.assertRaises(ValueError):
                patch(changed)

if __name__ == "__main__":
    unittest.main()
