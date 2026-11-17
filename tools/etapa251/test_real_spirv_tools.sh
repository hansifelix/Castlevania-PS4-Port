#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
SPV_DIR="$TMP/spv"
mkdir -p "$SPV_DIR"

command -v spirv-as >/dev/null
command -v spirv-val >/dev/null
REAL_SPIRV_VAL="$(command -v spirv-val)"

cat > "$TMP/vertex.spvasm" <<'EOF'
OpCapability Shader
OpMemoryModel Logical GLSL450
OpEntryPoint Vertex %main "main"
%void = OpTypeVoid
%fn = OpTypeFunction %void
%main = OpFunction %void None %fn
%entry = OpLabel
OpReturn
OpFunctionEnd
EOF

cat > "$TMP/fragment.spvasm" <<'EOF'
OpCapability Shader
OpMemoryModel Logical GLSL450
OpEntryPoint Fragment %main "main"
OpExecutionMode %main OriginUpperLeft
%void = OpTypeVoid
%fn = OpTypeFunction %void
%main = OpFunction %void None %fn
%entry = OpLabel
OpReturn
OpFunctionEnd
EOF

cat > "$TMP/compute.spvasm" <<'EOF'
OpCapability Shader
OpMemoryModel Logical GLSL450
OpEntryPoint GLCompute %main "main"
OpExecutionMode %main LocalSize 1 1 1
%void = OpTypeVoid
%fn = OpTypeFunction %void
%main = OpFunction %void None %fn
%entry = OpLabel
OpReturn
OpFunctionEnd
EOF

spirv-as --target-env vulkan1.2 "$TMP/vertex.spvasm" -o "$SPV_DIR/1111111111111111.spv"
spirv-as --target-env vulkan1.2 "$TMP/fragment.spvasm" -o "$SPV_DIR/2222222222222222.spv"
spirv-as --target-env vulkan1.2 "$TMP/compute.spvasm" -o "$SPV_DIR/3333333333333333.spv"

python3 - "$TMP" <<'PY'
import csv
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
items = [
    ("1111111111111111", "vertex"),
    ("2222222222222222", "fragment"),
    ("3333333333333333", "compute"),
]
rows = []
for key, stage in items:
    rows.append({
        "hash": key,
        "stage": stage,
        "status": "ok",
        "spv_bytes": str((root / "spv" / (key + ".spv")).stat().st_size),
    })
(root / "inventory.json").write_text(json.dumps({
    "programs": [{"hash": key, "stage": stage, "required": True} for key, stage in items]
}, indent=2) + "\n")
for name in ("all-results.tsv", "results.tsv"):
    with (root / name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["hash", "stage", "status", "spv_bytes"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
PY

cat > "$TMP/spirv-val-counting" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$3" >> "$SPIRV_VAL_CALL_LOG"
exec "$REAL_SPIRV_VAL" "$@"
EOF
chmod +x "$TMP/spirv-val-counting"
export REAL_SPIRV_VAL
export SPIRV_VAL_CALL_LOG="$TMP/validator-calls.log"
: > "$SPIRV_VAL_CALL_LOG"

AUDITOR="$ROOT/tools/etapa242/audit_spirv_bundle.py"
python3 "$AUDITOR" \
  --inventory "$TMP/inventory.json" \
  --all-results "$TMP/all-results.tsv" \
  --results "$TMP/results.tsv" \
  --spirv-dir "$SPV_DIR" \
  --spirv-val "$TMP/spirv-val-counting" \
  --report "$TMP/report-pass.json"
python3 - "$TMP/report-pass.json" <<'PY'
import json
import sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["status"] == "PASS", report
assert report["inventory_count"] == 3, report
assert report["required_count"] == 3, report
assert report["successful_results"] == 3, report
assert report["failures"] == [], report
PY
[ "$(wc -l < "$SPIRV_VAL_CALL_LOG")" -eq 3 ]
grep -q '1111111111111111.spv' "$SPIRV_VAL_CALL_LOG"
grep -q '2222222222222222.spv' "$SPIRV_VAL_CALL_LOG"
grep -q '3333333333333333.spv' "$SPIRV_VAL_CALL_LOG"
echo "KAZUMA251_REAL_SPIRV_VALIDATOR=PASS_VERTEX_FRAGMENT_COMPUTE"

python3 - "$SPV_DIR/3333333333333333.spv" <<'PY'
import struct
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = bytearray(path.read_bytes())
if len(data) % 4:
    raise SystemExit("fixture is not word aligned")
words = list(struct.unpack("<" + "I" * (len(data) // 4), data))
offset = 5
changed = False
while offset < len(words):
    word = words[offset]
    count, opcode = word >> 16, word & 0xffff
    if count == 0:
        raise SystemExit("unexpected zero word count in assembled fixture")
    if opcode == 253:  # OpReturn
        words[offset] = (count << 16) | 0xffff  # Reserved opcode; keep module size unchanged.
        changed = True
        break
    offset += count
if not changed:
    raise SystemExit("could not locate OpReturn in assembled fixture")
path.write_bytes(struct.pack("<" + "I" * len(words), *words))
PY

: > "$SPIRV_VAL_CALL_LOG"
set +e
python3 "$AUDITOR" \
  --inventory "$TMP/inventory.json" \
  --all-results "$TMP/all-results.tsv" \
  --results "$TMP/results.tsv" \
  --spirv-dir "$SPV_DIR" \
  --spirv-val "$TMP/spirv-val-counting" \
  --report "$TMP/report-fail.json"
rc=$?
set -e
if [ "$rc" -ne 2 ]; then
  echo "Expected the real validator failure to block the audit (exit 2), got $rc" >&2
  exit 1
fi
python3 - "$TMP/report-fail.json" <<'PY'
import json
import sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["status"] == "BLOCKED", report
assert any(x.get("hash") == "3333333333333333" and x.get("reason") == "SPIRV_VAL_FAILED"
           for x in report.get("failures", [])), report
PY
[ "$(wc -l < "$SPIRV_VAL_CALL_LOG")" -eq 3 ]
echo "KAZUMA251_REAL_VALIDATOR_REJECTS_INVALID_OPCODE=PASS"
echo "KAZUMA251_VALIDATOR_INVOCATIONS=3_PER_AUDIT"
