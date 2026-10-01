import subprocess, hashlib, json, os, sys, datetime
P = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
os.chdir(P + "/paper")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()

gates = {}
gates["latexmk_exit"] = subprocess.run("latexmk -pdf -interaction=nonstopmode main.tex",
    shell=True, capture_output=True).returncode
gates["pagecheck_exit"] = subprocess.run(f"python3 {P}/scripts/pagecheck.py main.pdf",
    shell=True, capture_output=True).returncode
gates["undefined_citations"] = int(sh("grep -a -c 'Undefined citation' main.log") or 0)
gates["pages"] = int(sh("pdfinfo main.pdf | grep -i '^Pages' | awk '{print $2}'"))
txt = sh("pdftotext main.pdf -")
gates["anonymity_hits"] = sum(txt.lower().count(k) for k in
    ("argonne","alcf","bellayang","huggingface","agentssci","github.com","overleaf"))
gates["todo_markers"] = int(sh("grep -c 'TODO{' main.tex sections/*.tex | grep -v ':0' | wc -l"))
gates["aamas_cls_official"] = sha("aamas.cls") == sha(P+"/paper_support/aamas_official/aamas.cls")

frz = json.load(open(P+"/experiments/results/FROZEN/MANIFEST.json"))
freeze = {
  "frozen_at": datetime.datetime.now().isoformat(timespec="seconds"),
  "title": "When Is Multi-Agent Organization Load-Bearing?",
  "github_head": sh(f"git -C {P} rev-parse HEAD"),
  "overleaf_head": sh("git -C /tmp/aamas_ol ls-remote origin | head -1 | cut -f1"),
  "pdf_sha256": sha("main.pdf"),
  "pdf_bytes": os.path.getsize("main.pdf"),
  "figure_sha256": {"fig1_v1_grouped.pdf": sha("figures/fig1_v1_grouped.pdf")},
  "abstract_sha256": hashlib.sha256(
      txt[txt.find("Multi-agent LLM systems"):txt.find("CCS CONCEPTS")].encode()).hexdigest(),
  "data_omnimath": frz["files"],
  "data_scibench": {f: {"sha256": sha(P+"/experiments/results/xdomain/FROZEN_SCIBENCH/"+f),
                        "rows": sum(1 for _ in open(P+"/experiments/results/xdomain/FROZEN_SCIBENCH/"+f))}
                    for f in os.listdir(P+"/experiments/results/xdomain/FROZEN_SCIBENCH") if f.endswith(".jsonl")},
  "hf_dataset": "AgentsSci/AAMAS2027-Roles v1.1.0 (PRIVATE during review)",
  "gates": gates,
}
ok = (gates["latexmk_exit"]==0 and gates["pagecheck_exit"]==0 and
      gates["undefined_citations"]==0 and gates["anonymity_hits"]==0 and
      gates["aamas_cls_official"])
freeze["ALL_GATES_PASS"] = ok
json.dump(freeze, open(P+"/FINAL_FREEZE.json","w"), indent=2)
print(json.dumps(freeze, indent=2))
sys.exit(0 if ok else 1)
