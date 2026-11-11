"""Synthetic contract tests for the pinned full-runtime PS4 compiler helper."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.compile_full_runtime import (
    NVN_DEBUG_AFTER,
    NVN_DEBUG_BEFORE,
    build_compile_command,
    object_name,
    parse_runtime_sources,
    patch_nvn_debug,
)


class FullRuntimeCompileContracts(unittest.TestCase):
    def test_manifest_deduplicates_original_cmake_entries_in_order(self):
        cmake = """set(NX_RUNTIME_SOURCES
            runtime/src/a.cpp
            runtime/src/b.cpp
            runtime/src/a.cpp
        )
        file(GLOB NX_GAME_SOURCES CONFIGURE_DEPENDS "games/*.cpp")
        """
        sources, duplicates = parse_runtime_sources(cmake, expected_count=2)
        self.assertEqual(sources, ["runtime/src/a.cpp", "runtime/src/b.cpp"])
        self.assertEqual(duplicates, ["runtime/src/a.cpp"])

    def test_manifest_rejects_missing_or_changed_source_count(self):
        with self.assertRaises(ValueError):
            parse_runtime_sources("set(NX_RUNTIME_SOURCES runtime/src/a.cpp) file(GLOB", expected_count=2)

    def test_manifest_rejects_path_traversal(self):
        cmake = """set(NX_RUNTIME_SOURCES
            runtime/src/../private/module.cpp
        )
        file(GLOB NX_GAME_SOURCES)
        """
        with self.assertRaises(ValueError):
            parse_runtime_sources(cmake, expected_count=1)

    def test_manifest_rejects_absolute_or_non_runtime_paths(self):
        cmake = """set(NX_RUNTIME_SOURCES
            /tmp/evil.cpp
        )
        file(GLOB NX_GAME_SOURCES)
        """
        with self.assertRaises(ValueError):
            parse_runtime_sources(cmake, expected_count=1)

    def test_nvn_debug_patch_changes_exactly_the_float_double_expression(self):
        original = "else big = " + NVN_DEBUG_BEFORE + ";"
        patched = patch_nvn_debug(original)
        self.assertEqual(patched, "else big = " + NVN_DEBUG_AFTER + ";")
        self.assertEqual(patched.count(NVN_DEBUG_AFTER), 1)

    def test_nvn_debug_patch_fails_closed_if_upstream_changes(self):
        with self.assertRaises(ValueError):
            patch_nvn_debug("std::max(1.0f, 2.0);")

    def test_object_names_are_deterministic_and_reject_unknown_paths(self):
        self.assertEqual(
            object_name("runtime/src/nvn/nvn_vk.cpp"),
            "RT-runtime__src__nvn__nvn_vk.o",
        )
        with self.assertRaises(ValueError):
            object_name("../private/main.cpp")

    def test_compile_command_targets_orbis_and_uses_pinned_include_roots(self):
        command = build_compile_command(
            Path("/upstream/runtime/src/main.cpp"),
            Path("/tmp/out.o"),
            Path("/sdk"),
            Path("/compat"),
            Path("/upstream"),
            Path("/vulkan/include"),
            Path("/mesa/include"),
        )
        self.assertIn("--target=x86_64-pc-freebsd12-elf", command)
        self.assertIn("-std=c++20", command)
        self.assertIn("/sdk/include/c++/v1", command)
        self.assertIn("/compat", command)
        self.assertIn("/upstream/runtime/include", command)
        self.assertIn("/vulkan/include", command)
        self.assertIn("/mesa/include", command)
        self.assertEqual(command[command.index("-o") + 1], "/tmp/out.o")
        self.assertNotIn("-o/tmp/out.o", command)


if __name__ == "__main__":
    unittest.main()
