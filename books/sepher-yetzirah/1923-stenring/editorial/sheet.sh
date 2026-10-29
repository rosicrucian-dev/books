# sheet.sh FIRST LAST OUT: crops of hebrew-checks.txt lines FIRST..LAST
python3 - "$1" "$2" "$3" <<'PY'
import sys,subprocess
a,b,out=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]
rows=[l.rstrip('\n').split('\t') for l in open('hebrew-checks.txt')][a-1:b]
for i,r in enumerate(rows,a): print(i, r[2])
subprocess.run(['python3','look.py',out]+[f'{r[0]}:{r[1]}' for r in rows],check=True)
PY
