#!/usr/bin/env python3
"""Private, read-only exact-name provider scan for private AOT symbols."""
from __future__ import annotations
import argparse, json, re, shutil, subprocess
from collections import Counter, defaultdict
from pathlib import Path

LINE = re.compile(r"^(?P<origin>.*?):\s+(?P<symbol>\S+)\s+(?P<kind>[A-Za-z?])(?:\s+\S+){0,2}$")
SUFFIXES = {".a", ".so", ".o", ".elf", ".prx"}

def complete(data):
    return (data.get("audit_mode") == "READ_ONLY_SYMBOL_TABLE_PARSE_NO_EXTRACT_NO_COMPILE_NO_LINK"
            and data.get("index_coverage_complete") is True
            and data.get("duplicate_metadata_complete") is True
            and not data.get("invalid_objects")
            and data.get("private_symbol_names_in_report") is True
            and data.get("files_extracted") is False
            and data.get("compilation_performed") is False
            and data.get("link_performed") is False
            and isinstance(data.get("undefined_without_aot_provider"), dict)
            and data.get("totals", {}).get("undefined_symbols_without_provider_in_aot_inventory")
                == len(data.get("undefined_without_aot_provider", {})))

def parse_nm(text):
    out=[]
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.endswith(": no symbols") or line == "no symbols":
            continue
        m=LINE.match(line)
        if not m:
            if line.startswith(("nm:", "llvm-nm:", "warning:")):
                continue
            raise ValueError("unrecognized_nm_posix_line")
        if m.group("kind").upper() != "U":
            out.append((m.group("symbol"),m.group("kind")))
    return out

def provider_files(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("provider_root_not_real_directory")
    return [p for p in sorted(root.rglob("*")) if not p.is_symlink() and p.is_file()
            and (p.suffix.lower() in SUFFIXES or ".so." in p.name.lower())]

def scan(data, roots, nm):
    if not complete(data):
        raise ValueError("inventory_incomplete_or_not_read_only")
    providers=defaultdict(list); errors=[]; scanned=0; symbols=0; root_rows=[]
    for label,root in roots:
        fs=provider_files(root); root_rows.append({"label":label,"library_count":len(fs)})
        for path in fs:
            scanned+=1
            try:
                p=subprocess.run([nm,"-A","-g","--defined-only","--format=posix",str(path)],
                    check=False,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=300)
                if p.returncode: raise RuntimeError("nm_failed")
                rows=parse_nm(p.stdout); symbols+=len(rows)
                for name,kind in rows:
                    providers[name].append({"root":label,"path":path.relative_to(root).as_posix(),"nm_type":kind})
            except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as e:
                errors.append({"root":label,"path":path.relative_to(root).as_posix(),"error":str(e) or type(e).__name__})
    matched={}; ambiguous={}; missing={}
    categories=Counter()
    for name,consumers in sorted(data["undefined_without_aot_provider"].items()):
        if name.startswith(("nx::","_ZN2nx","_ZN3nx")): category="nx_runtime"
        elif name.startswith(("plat::","_ZN4plat")): category="platform"
        elif name.startswith(("__cxa_","__gxx_","_Unwind_","_Z","std::")): category="cxx_abi"
        elif name in {"ceil","floor","fma","trunc","sqrt","sin","cos","pow","round","nearbyint"}: category="libm"
        elif name.startswith("__atomic_"): category="compiler_runtime"
        else: category="c_or_other"
        categories[category]+=1
        row={"consumers":consumers,"class":category,"providers":providers.get(name,[])}
        if not row["providers"]: missing[name]=row
        elif len({(x["root"],x["path"]) for x in row["providers"]})>1: ambiguous[name]=row
        else: matched[name]=row
    return {"audit_mode":"READ_ONLY_NM_PROVIDER_CANDIDATE_SCAN_NO_LINK",
        "inventory_root_name":data.get("root_name"),"inventory_object_count":data.get("totals",{}).get("object_copies_parsed"),
        "provider_roots":root_rows,"libraries_scanned":scanned,"defined_nm_entries_seen":symbols,
        "aot_unresolved_symbol_count":len(data["undefined_without_aot_provider"]),
        "aot_unresolved_by_class":dict(sorted(categories.items())),
        "exact_provider_candidate_count":len(matched),"ambiguous_provider_candidate_count":len(ambiguous),
        "no_provider_candidate_count":len(missing),"matched_exact_names":matched,
        "ambiguous_exact_names":ambiguous,"no_exact_name_provider":missing,"library_scan_errors":errors,
        "all_provider_roots_scanned":not errors,"inputs_modified":False,"archives_extracted":False,
        "compilation_performed":False,"link_performed":False,"abi_compatibility_proven":False,
        "limitations":["Exact-name matches are candidates, not proof of ABI compatibility.",
            "No relocation, symbol-version, calling-convention, type-layout, or transitive-dependency validation.",
            "The report contains private mangled names and local paths; keep it private."]}

def safe_report(path, protected, overwrite):
    dest=path.expanduser().absolute()
    if dest.is_symlink(): raise ValueError("report_path_is_symlink")
    parent=dest.parent.resolve()
    if any(parent==r.resolve() or r.resolve() in parent.parents for r in protected):
        raise ValueError("report_must_be_outside_inventory_and_provider_roots")
    if dest.exists() and not overwrite:
        base=dest; n=2
        while True:
            candidate=base.with_name(f"{base.stem}_v{n}{base.suffix}")
            if not candidate.exists() and not candidate.is_symlink(): dest=candidate; break
            n+=1
    dest.parent.mkdir(parents=True,exist_ok=True)
    return dest

def main():
    ap=argparse.ArgumentParser(description="Private read-only AOT/SDK provider candidate scan")
    ap.add_argument("--inventory",type=Path,required=True)
    ap.add_argument("--provider-root",action="append",required=True,metavar="LABEL=PATH")
    ap.add_argument("--nm",default="llvm-nm")
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--overwrite-report",action="store_true")
    a=ap.parse_args()
    tool=shutil.which(a.nm)
    if not tool: ap.error("nm_executable_not_found")
    if a.inventory.is_symlink() or not a.inventory.is_file(): ap.error("inventory_must_be_regular_file")
    try:
        data=json.loads(a.inventory.read_text(encoding="utf-8"))
        roots=[]
        for raw in a.provider_root:
            if "=" not in raw: ap.error("provider_root_must_be_LABEL_equals_PATH")
            label,path=raw.split("=",1); root=Path(path).expanduser()
            if not label.strip() or root.is_symlink() or not root.is_dir(): ap.error("invalid_provider_root")
            roots.append((label.strip(),root))
        result=scan(data,roots,tool)
        if not result["libraries_scanned"]: raise ValueError("no_provider_libraries_found")
        dest=safe_report(a.report,[a.inventory.parent,*(r for _,r in roots)],a.overwrite_report)
        dest.write_text(json.dumps(result,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"status":"PROVIDER_SCAN_COMPLETE" if result["all_provider_roots_scanned"] else "PROVIDER_SCAN_INCOMPLETE",
            "libraries_scanned":result["libraries_scanned"],"defined_nm_entries_seen":result["defined_nm_entries_seen"],
            "aot_unresolved_symbol_count":result["aot_unresolved_symbol_count"],
            "exact_provider_candidate_count":result["exact_provider_candidate_count"],
            "ambiguous_provider_candidate_count":result["ambiguous_provider_candidate_count"],
            "no_provider_candidate_count":result["no_provider_candidate_count"],
            "library_scan_error_count":len(result["library_scan_errors"]),"abi_compatibility_proven":False,
            "report_path":str(dest)},ensure_ascii=True,indent=2))
        return 0 if result["all_provider_roots_scanned"] else 1
    except (OSError,json.JSONDecodeError,ValueError,subprocess.TimeoutExpired) as e:
        ap.error(str(e))
if __name__=="__main__": raise SystemExit(main())
