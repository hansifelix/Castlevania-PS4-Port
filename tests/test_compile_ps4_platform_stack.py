import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.compile_ps4_platform_stack import (
    PLATFORM_SOURCES,
    build_compile_command,
    object_name,
)


class CompilePS4PlatformStackTests(unittest.TestCase):
    def test_manifest_has_fourteen_unique_reviewed_sources(self):
        self.assertEqual(len(PLATFORM_SOURCES), 14)
        self.assertEqual(len(set(PLATFORM_SOURCES)), 12)
        required = {
            "tools/etapa50/platform_ps4_memory.cpp",
            "tools/etapa73/platform_ps4_input.cpp",
            "tools/etapa74/platform_ps4_display.cpp",
            "tools/etapa75/platform_ps4_audio.cpp",
            "src/ps4/platform_ps4_app0_config.cpp",
            "src/ps4/platform_ps4_clock_thread.cpp",
            "src/ps4/platform_ps4_file_io.cpp",
            "src/ps4/platform_ps4_thread_launch.cpp",
            "src/ps4/platform_ps4_thread_name.cpp",
            "src/ps4/platform_ps4_optional_services.cpp",
            "src/ps4/platform_ps4_sysconf.cpp",
            "src/ps4/platform_ps4_thread_atexit.cpp",
            "src/runtime_bridge/linked_modules_castlevania.cpp",
            "src/ps4/main.cpp",
        }
        self.assertEqual(set(PLATFORM_SOURCES), required)

    def test_object_names_are_path_stable_and_safe(self):
        self.assertEqual(
            object_name("src/ps4/main.cpp"),
            "PS4-src__ps4__main.o",
        )
        for invalid in ("../escape.cpp", "/absolute.cpp", "not-source.c"):
            with self.assertRaises(ValueError):
                object_name(invalid)

    def test_ps4_and_native_defines_are_scoped_to_their_providers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src/ps4/platform_ps4_app0_config.cpp"
            sdk = root / "sdk"
            compat = root / "compat"
            upstream = root / "upstream"
            cmd = build_compile_command(
                source, root / "app0.o", sdk=sdk, compat=compat,
                upstream=upstream, repository=root,
            )
            self.assertIn("-DKAZUMA_PS4=1", cmd)
            self.assertNotIn("-DKAZUMA_PS4_NATIVE=1", cmd)
            self.assertEqual(cmd[cmd.index("-o") + 1], str(root / "app0.o"))

            native = root / "src/ps4/platform_ps4_thread_name.cpp"
            native_cmd = build_compile_command(
                native, root / "thread-name.o", sdk=sdk, compat=compat,
                upstream=upstream, repository=root,
            )
            self.assertIn("-DKAZUMA_PS4=1", native_cmd)
            self.assertIn("-DKAZUMA_PS4_NATIVE=1", native_cmd)

            ordinary = root / "tools/etapa74/platform_ps4_display.cpp"
            ordinary_cmd = build_compile_command(
                ordinary, root / "display.o", sdk=sdk, compat=compat,
                upstream=upstream, repository=root,
            )
            self.assertNotIn("-DKAZUMA_PS4_NATIVE=1", ordinary_cmd)

    def test_unreviewed_source_cannot_enter_the_platform_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                build_compile_command(
                    root / "random.cpp", root / "random.o",
                    sdk=root / "sdk", compat=root / "compat",
                    upstream=root / "upstream", repository=root,
                )


if __name__ == "__main__":
    unittest.main()
