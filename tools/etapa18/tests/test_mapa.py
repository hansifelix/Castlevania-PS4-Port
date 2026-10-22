"""Testes locais offline: nao acessam rede, nao usam PS4."""
import importlib.util
import pathlib
import unittest

SRC = pathlib.Path(__file__).resolve().parents[1] / 'auditar_mapa.py'
spec = importlib.util.spec_from_file_location('auditar_mapa', SRC)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

CPU = '''#ifndef NX_BASE
#if defined(__APPLE__)
#define NX_BASE 0x0000000C00000000ull
#else
#define NX_BASE 0x0000004000000000ull
#endif
#endif
'''
RUNTIME = '''constexpr uint64_t kAddressSpaceBase = 0x0008000000ull;
constexpr uint64_t kAddressSpaceSize = 0x7FF8000000ull;
constexpr uint64_t kModuleBase = NX_BASE;
constexpr uint64_t kHeapMax = 0x180000000ull;
constexpr uint64_t kStackSize = 0x100000000ull;
constexpr uint64_t kKernelSize = 0x100000000ull;
constexpr uint64_t kThunkSize = 0x100000ull;
#if defined(__APPLE__)
constexpr uint64_t kHeapBase = 0x400000000ull;
constexpr uint64_t kAliasBase = 0x600000000ull;
constexpr uint64_t kAliasSize = 0x400000000ull;
constexpr uint64_t kStackBase = 0xA00000000ull;
constexpr uint64_t kKernelBase = 0xB00000000ull;
constexpr uint64_t kThunkBase = 0xE00000000ull;
#else
constexpr uint64_t kHeapBase = 0x5000000000ull;
#if defined(__ANDROID__)
constexpr uint64_t kAliasBase = 0x2000000000ull;
#else
constexpr uint64_t kAliasBase = 0x5800000000ull;
#endif
constexpr uint64_t kAliasSize = 0x1000000000ull;
constexpr uint64_t kStackBase = 0x6800000000ull;
constexpr uint64_t kKernelBase = 0x6A00000000ull;
constexpr uint64_t kThunkBase = 0x6F00000000ull;
#endif
void memory_init();
'''

class TestAuditoria(unittest.TestCase):
    def test_consts_plataformas(self):
        linux = audit.runtime_constants(RUNTIME, CPU, 'linux')
        android = audit.runtime_constants(RUNTIME, CPU, 'android')
        mac = audit.runtime_constants(RUNTIME, CPU, 'macos')
        self.assertEqual(linux['kAliasBase'], 0x5800000000)
        self.assertEqual(android['kAliasBase'], 0x2000000000)
        self.assertEqual(mac['kModuleBase'], 0xC00000000)
        self.assertEqual(linux['kModuleBase'], 0x4000000000)
        self.assertEqual(audit.analyze(linux, 'linux')['sobreposicoes_nominais'], False)

    def test_detecta_colisao(self):
        const = audit.runtime_constants(RUNTIME, CPU, 'linux')
        const['kAliasBase'] = const['kHeapBase'] + 0x1000
        data = audit.analyze(const, 'linux')
        self.assertTrue(data['sobreposicoes_nominais'])
        self.assertFalse(data['enderecos_seguros_ps4_identificados'])

    def test_detecta_fora_envelope(self):
        const = audit.runtime_constants(RUNTIME, CPU, 'linux')
        const['kStackBase'] = 0x8000000000
        data = audit.analyze(const, 'linux')
        self.assertIn('fora_envelope', [x['tipo'] for x in data['achados_estaticos']])

    def test_expr_nao_executa_codigo(self):
        with self.assertRaises((SyntaxError, ValueError)):
            audit.number_expr('__import__("os").system("true")', {})

if __name__ == '__main__':
    unittest.main()
