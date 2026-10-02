#!/usr/bin/env python3
"""Run every submission gate and write FINAL_FREEZE.json.

This is the single command that answers "is the submission in a releasable
state?". It is deliberately paranoid about its own correctness, because
three earlier versions of the project's gates each passed while measuring
something other than the thing:

  * the page check was column-blind, then vacuous under \\clearpage;
  * the terminology check could not see inside a figure PDF;
  * `| tail` made $? report tail's status, producing a false PASS.

So: nothing here is hand-maintained that can be read off a source instead.
The title is parsed from main.tex, the figure list from \\includegraphics,
the supplement is discovered rather than assumed, and every gate that can
be positive-controlled is.

Exit 0 only if every gate passes.
"""
import subprocess, hashlib, json, os, re, sys, datetime

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(P, "paper")
os.chdir(PAPER)


def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def build(stem):
    """pdflatex -> bibtex -> pdflatex x2. NOT latexmk: from a clean tree it
    schedules bibtex before any .aux exists and fails."""
    rc = subprocess.run(f"pdflatex -interaction=nonstopmode {stem}.tex",
                        shell=True, capture_output=True).returncode
    subprocess.run(f"bibtex {stem}", shell=True, capture_output=True)
    for _ in range(2):
        rc = subprocess.run(f"pdflatex -interaction=nonstopmode {stem}.tex",
                            shell=True, capture_output=True).returncode
    return rc


# Anything that would deanonymise, in the RENDERED text. Checked on
# pdftotext output, never on the source: the source legitimately contains
# these strings in comments and in paper/README.md.
IDENTIFYING = ("argonne", "alcf", "bellayang", "huggingface", "agentssci",
               "github.com", "overleaf", "chihhsuan")

gates = {}

# ---------------------------------------------------------------- main paper
gates["main_build_exit"] = build("main")
gates["main_pagecheck_exit"] = subprocess.run(
    f"python3 {P}/scripts/pagecheck.py main.pdf", shell=True,
    capture_output=True).returncode
log = open("main.log", errors="ignore").read()
gates["main_undefined_citations"] = log.count("Undefined citation")
gates["main_undefined_refs"] = log.count("LaTeX Warning: Reference")
gates["main_multiply_defined"] = log.count("multiply defined")
gates["main_pages"] = int(re.search(r"Output written.*\((\d+) page", log).group(1))
main_txt = sh("pdftotext main.pdf -")
gates["main_anonymity_hits"] = sum(main_txt.lower().count(k) for k in IDENTIFYING)

# ---------------------------------------------------------------- supplement
# Discovered, not assumed. Its absence is a reported state, not a crash --
# but once it exists it is gated exactly as hard as the main paper.
gates["supplement_exists"] = os.path.exists("supplement.tex")
if gates["supplement_exists"]:
    gates["supp_build_exit"] = build("supplement")
    slog = open("supplement.log", errors="ignore").read()
    gates["supp_undefined_refs"] = slog.count("LaTeX Warning: Reference")
    gates["supp_undefined_citations"] = slog.count("Undefined citation")
    gates["supp_pages"] = int(re.search(r"Output written.*\((\d+) page", slog).group(1))
    supp_txt = sh("pdftotext supplement.pdf -")
    gates["supp_anonymity_hits"] = sum(supp_txt.lower().count(k) for k in IDENTIFYING)
    # The supplement has NO page limit; it must not acquire a page check.
else:
    supp_txt = ""

# ------------------------------------------------- terminology, both PDFs
# A bare internal condition code reaching a reader is a hard failure. The
# .tex grep cannot see inside a figure, which is how one slipped through
# once; this reads the rendered text of every PDF the submission ships.
ARMCODE = re.compile(r"\bArms?\s*[ABC]\b")
gates["armcode_in_main_pdf"] = len(ARMCODE.findall(main_txt))
gates["armcode_in_supp_pdf"] = len(ARMCODE.findall(supp_txt))
gates["armcode_in_sources"] = int(sh(
    r"grep -c -E 'Arm~?\s*[ABC]\b' main.tex sections/*.tex | "
    r"awk -F: '{s+=$2} END{print s+0}'") or 0)
gates["figure_pdfs_clean_exit"] = subprocess.run(
    f"python3 {P}/scripts/check_terminology_pdfs.py", shell=True,
    capture_output=True).returncode

# ------------------------------------------------------- unrun placeholders
# Count USES of \TODO{...}, not the \newcommand that defines it. The old
# gate counted its own macro definition and reported 1 forever, which is a
# gate that cannot reach 0 and therefore cannot mean anything.
src = "".join(open(f, errors="ignore").read()
              for f in ["main.tex"] + sh("ls sections/*.tex").split())
gates["todo_uses"] = len(re.findall(r"(?<!newcommand\{)\\TODO\{", src))

# ---------------------------------------------------------- class integrity
gates["aamas_cls_official"] = (
    sha("aamas.cls") == sha(f"{P}/paper_support/aamas_official/aamas.cls"))

# ------------------------------------------------------------ tables fresh
gates["tables_match_sources_exit"] = subprocess.run(
    f"python3 {P}/analysis/scripts/mk_tables.py --check", shell=True,
    capture_output=True).returncode

# ------------------------------------------------- figures the paper USES
# Parsed from \includegraphics, so a renamed or newly added figure is
# hashed automatically and a stale one stops being recorded.
used = re.findall(r"\\includegraphics\[[^\]]*\]\{figures/([^}]+)\}", src)
figs, missing = {}, []
for f in sorted(set(used)):
    p = os.path.join("figures", f)
    (figs.__setitem__(f, sha(p)) if os.path.exists(p) else missing.append(f))
gates["figures_present"] = not missing

frz = json.load(open(f"{P}/experiments/results/FROZEN/MANIFEST.json"))
SCI = f"{P}/experiments/results/xdomain/FROZEN_SCIBENCH"

title = re.sub(r"\s+", " ", re.search(
    r"\\title\{(.+?)\}", src, re.S).group(1)).strip()

freeze = {
    "frozen_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "title": title,                       # parsed, never typed
    "github_head": sh(f"git -C {P} rev-parse HEAD"),
    "overleaf_head": sh("git -C /tmp/aamas_ol ls-remote origin 2>/dev/null "
                        "| head -1 | cut -f1") or "UNREACHABLE (access blocked)",
    "main_pdf_sha256": sha("main.pdf"),
    "main_pdf_bytes": os.path.getsize("main.pdf"),
    "supplement_pdf_sha256": sha("supplement.pdf") if gates["supplement_exists"] else None,
    "figures_used": figs,
    "figures_missing": missing,
    "abstract_sha256": hashlib.sha256(main_txt[
        main_txt.find("Multi-agent LLM systems"):
        main_txt.find("CCS CONCEPTS")].encode()).hexdigest(),
    "data_omnimath": frz["files"],
    "data_scibench": {f: {"sha256": sha(f"{SCI}/{f}"),
                          "rows": sum(1 for _ in open(f"{SCI}/{f}"))}
                      for f in sorted(os.listdir(SCI)) if f.endswith(".jsonl")},
    "hf_dataset": "AgentsSci/AAMAS2027-Roles v1.1.0 (PRIVATE during review)",
    "gates": gates,
}

MUST_BE_ZERO = ["main_build_exit", "main_pagecheck_exit", "main_undefined_citations",
                "main_undefined_refs", "main_multiply_defined", "main_anonymity_hits",
                "armcode_in_main_pdf", "armcode_in_supp_pdf", "armcode_in_sources",
                "figure_pdfs_clean_exit", "todo_uses", "tables_match_sources_exit"]
if gates["supplement_exists"]:
    MUST_BE_ZERO += ["supp_build_exit", "supp_undefined_refs",
                     "supp_undefined_citations", "supp_anonymity_hits"]
MUST_BE_TRUE = ["aamas_cls_official", "figures_present"]

failed = ([k for k in MUST_BE_ZERO if gates.get(k) != 0]
          + [k for k in MUST_BE_TRUE if not gates.get(k)]
          + (["main_pages_over_limit"] if gates["main_pages"] > 9 else []))
freeze["FAILED_GATES"] = failed
freeze["ALL_GATES_PASS"] = not failed

json.dump(freeze, open(f"{P}/FINAL_FREEZE.json", "w"), indent=2)
print(json.dumps(freeze, indent=2))
if failed:
    print("\nFAILED: " + ", ".join(failed), file=sys.stderr)
sys.exit(0 if not failed else 1)
