import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'auditar_portabilidade.py'
spec=importlib.util.spec_from_file_location('kazuma19',p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Auditoria(unittest.TestCase):
    def test_strip_comments(self):
        self.assertFalse(m.defined('// bool reserve(uint64_t addr, uint64_t size) {\n','reserve'))
        self.assertFalse(m.declared('// bool reserve(uint64_t addr, uint64_t size);\n','reserve'))
    def test_basic(self):
        self.assertTrue(m.declared('bool reserve(uint64_t addr, uint64_t size);','reserve'))
        self.assertTrue(m.defined('bool reserve(uint64_t addr, uint64_t size) {return false;}','reserve'))
        self.assertTrue(m.defined('FILE* fopen_utf8(const std::string& p, const char* m) {return nullptr;}','fopen_utf8'))
        self.assertTrue(m.defined('void read_pad(PadState& p) { }','read_pad'))
        self.assertFalse(m.defined('int a = nx::plat::read_pad(p);','read_pad'))
    def test_missing_contract_rejected(self):
        with self.assertRaises(ValueError):m.audit('bool reserve(uint64_t addr,uint64_t sz);','')
    def test_fail_closed(self):
        self.assertFalse(m.defined('/*void vulkan_create_surface() {}*/','vulkan_create_surface'))

if __name__ == '__main__': unittest.main()
