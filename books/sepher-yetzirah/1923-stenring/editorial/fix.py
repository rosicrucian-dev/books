# fix.py: applies corrections to proofread/32-paths.txt, each exactly once.
# Usage: python3 fix.py <<'X' ... X  with pairs "old ⟶ new" one per line.
import pathlib, sys
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "proofread/32-paths.txt")
s = p.read_text()
bad = []
for line in sys.stdin.read().split("\n"):
    if "⟶" not in line:
        continue
    a, b = line.split(" ⟶ ", 1)
    a, b = a.replace("\\t", "\t").replace("\\n", "\n"), b.replace("\\t", "\t").replace("\\n", "\n")
    if s.count(a) != 1:
        bad.append(f"{s.count(a)}x {a[:70]}")
        continue
    s = s.replace(a, b)
p.write_text(s)
print("not applied:", bad if bad else "none")
