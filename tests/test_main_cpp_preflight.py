"""Synthetic-only tests: no commercial code or game assets."""
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.main_compile.main_cpp_preflight import audit

def fixture(path, entries):
    with tarfile.open(path, 'w:gz') as out:
        for name, source in entries:
            blob = source.encode()
            member = tarfile.TarInfo('synthetic/' + name)
            member.size = len(blob)
            out.addfile(member, io.BytesIO(blob))

class MainAuditTest(unittest.TestCase):
    def test_counts_and_sve(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'test.tar.gz'
            fixture(archive, [
                ('code_000.cpp', 'std::countl_zero(x); std::popcount(y); "mov z24.b, p3/m, #4";'),
                ('code_001.cpp', 'std::popcount(y);')])
            result = audit(archive, total=2)
            self.assertEqual(result['std_calls'], {'countl_zero': 1, 'popcount': 2})
            self.assertEqual(result['std_union_units'], 2)
            self.assertEqual(result['sve_mov_units'], [0])
            self.assertFalse(result['compiled_for_ps4'])

    def test_missing(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'test.tar.gz'
            fixture(archive, [('code_000.cpp', 'void a(){}')])
            with self.assertRaisesRegex(ValueError, 'Missing'):
                audit(archive, total=2)

    def test_duplicate(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'test.tar.gz'
            fixture(archive, [('code_000.cpp', 'void a(){}'),
                              ('code_000.cpp', 'void a(){}')])
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                audit(archive, total=1)

    def test_sha_bad(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'test.tar.gz'
            fixture(archive, [('code_000.cpp', 'void a(){}')])
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                audit(archive, total=1, expected_sha256='0'*64)

    def test_sha_good(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'test.tar.gz'
            fixture(archive, [('code_000.cpp', 'void a(){}')])
            good = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(audit(archive, total=1, expected_sha256=good)['units_complete'], 1)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'test.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                member = tarfile.TarInfo('synthetic/code_000.cpp')
                member.type = tarfile.SYMTYPE
                member.linkname = '/etc/passwd'
                tar.addfile(member)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                audit(archive, total=1)

if __name__ == '__main__':
    unittest.main()
