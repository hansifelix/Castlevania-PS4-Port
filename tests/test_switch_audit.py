import io
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import audit_switch

def fake_nsp():
    names = b'mock.nca\0'
    entry = struct.pack('<QQII', 0, 4, 0, 0)
    return b'PFS0' + struct.pack('<III', 1, len(names), 0) + entry + names + b'MOCK'

class TestSwitchAudit(unittest.TestCase):
    def test_pfs0(self):
        data = fake_nsp()
        self.assertIn('PFS0 OK', audit_switch.read_pfs0(io.BytesIO(data), len(data)))
    def test_title(self):
        b = audit_switch.label('Castlevania [0100BA4026E94000][v0].nsp')
        u = audit_switch.label('Castlevania [0100BA4026E94800][v65536].nsp')
        self.assertIn('base', b[2]); self.assertIn('atualização', u[2])
        self.assertEqual(u[1], 65536)
    def test_bad_header(self):
        self.assertIn('NÃO é PFS0', audit_switch.read_pfs0(io.BytesIO(b'NOPE' + b'\0'*12), 16))
    def test_zip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'demo.zip'
            with zipfile.ZipFile(p, 'w') as z:
                z.writestr('Mock Game [0100BA4026E94000][v0].nsp', fake_nsp())
                z.writestr('prod.keys', 'dummy')
            import contextlib
            capture=io.StringIO()
            with contextlib.redirect_stdout(capture):
                audit_switch.check(p)
            self.assertIn('PFS0 OK',capture.getvalue())
            self.assertNotIn('dummy',capture.getvalue())

if __name__=='__main__': unittest.main()
