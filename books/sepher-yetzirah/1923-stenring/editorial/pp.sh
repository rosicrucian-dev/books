# pp.sh FILE PRINTED: a printed page's draft lines (FILE in proofread/) and
# its render in halves, for proofreading.
S=/private/tmp/claude-501/-Users-espositocode-Code-botaschool/e3aaa2e9-1722-4f36-b5af-17c6fc2c9fdd/scratchpad
p=$2; if [ $p -le 14 ]; then n=$((p+5)); elif [ $p -le 24 ]; then n=$((p+7)); else n=$((p+9)); fi
python3 halves.py $n $S
awk -F"\t" -v p="@$p" '$1==p {print NR": "$2}' proofread/$1.txt
echo "(pdf $n: $S/pg${n}a.png, pg${n}b.png)"
