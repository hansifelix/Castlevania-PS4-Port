import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from tools.etapa90.private_aot_sdk_provider_audit import complete, parse_nm, provider_files, safe_report, scan

def inventory():
    return {"audit_mode":"READ_ONLY_SYMBOL_TABLE_PARSE_NO_EXTRACT_NO_COMPILE_NO_LINK",
        "root_name":"synthetic-private","index_coverage_complete":True,"duplicate_metadata_complete":True,
        "invalid_objects":[],"private_symbol_names_in_report":True,"files_extracted":False,
        "compilation_performed":False,"link_performed":False,
        "totals":{"object_copies_parsed":3,"undefined_symbols_without_provider_in_aot_inventory":3},
        "undefined_without_aot_provider":{"_ZprivateA":["main:1"],"_ZprivateB":["sdk:2"],"external_missing":["subsdk0:3"]}}

class ProviderAuditTests(unittest.TestCase):
    def test_requires_complete_inventory(self):
        data=inventory(); data["index_coverage_complete"]=False
        self.assertFalse(complete(data))
    def test_parses_nm_archive_and_object_rows(self):
        got=parse_nm("libx.a[a.o]: _ZprivateA T 0 8\nlibx.a[a.o]: external U 0 0\n")
        self.assertEqual(got,[("_ZprivateA","T")])
    def test_rejects_unrecognized_nm_output(self):
        with self.assertRaisesRegex(ValueError,"unrecognized_nm_posix_line"): parse_nm("not nm output")
    def test_unique_ambiguous_and_missing_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); 
            for name in ("one.a","two.a","none.a"): (root/name).write_bytes(b"synthetic")
            def fake(cmd,**kwargs):
                name=Path(cmd[-1]).name
                data={"one.a":"one.a[x.o]: _ZprivateA T 0 8\none.a[x.o]: _ZprivateB W 0 8\n",
                      "two.a":"two.a[y.o]: _ZprivateB T 0 8\n","none.a":"none.a[z.o]: other T 0 8\n"}[name]
                from types import SimpleNamespace
                return SimpleNamespace(returncode=0,stdout=data,stderr="")
            from unittest.mock import patch
            with patch("tools.etapa90.private_aot_sdk_provider_audit.subprocess.run",side_effect=fake):
                r=scan(inventory(),[("sdk",root)],"fake-nm")
            self.assertEqual(r["exact_provider_candidate_count"],1)
            self.assertEqual(r["ambiguous_provider_candidate_count"],1)
            self.assertEqual(r["no_provider_candidate_count"],1)
            self.assertFalse(r["abi_compatibility_proven"])
    def test_ignores_symlink_and_non_library_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"x.a").write_text("x"); (root/"readme.txt").write_text("x")
            (root/"alias.a").symlink_to(root/"x.a")
            self.assertEqual([x.name for x in provider_files(root)],["x.a"])
    def test_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); sdk=root/"sdk"; sdk.mkdir(); p=root/"out.json"; p.write_text("old")
            dest=safe_report(p,[sdk],False)
            self.assertEqual(dest.name,"out_v2.json"); self.assertEqual(p.read_text(),"old")
    def test_rejects_report_inside_provider_root(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with self.assertRaisesRegex(ValueError,"outside"):
                safe_report(root/"out.json",[root],False)

if __name__=="__main__": unittest.main()
