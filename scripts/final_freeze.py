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

# ------------------------------------------------------------ the abstract
# Taken from the SOURCE, not from pdftotext output.
#
# DEFECT FIXED 2026-10-02: the old abstract hash sliced the rendered text
# between "Multi-agent LLM systems" and "CCS CONCEPTS". In a two-column
# layout pdftotext's reading order puts the Introduction's first paragraph
# inside that span, so the "abstract hash" covered the abstract PLUS 140
# words of intro -- stable, reproducible, and not the abstract. A hash is
# only as meaningful as the subject it is taken over.
abstract_src = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
                         open("main.tex").read(), re.S).group(1)


def abstract_plaintext(tex):
    """LaTeX abstract -> the plain text a submission form wants."""
    t = tex
    # Sweep the whole command set repeatedly, innermost-first, until nothing
    # changes. One pass per command in a fixed order is NOT enough: the
    # abstract ends with \textbf{Role structure \emph{can} be ...}, whose
    # outer group contains braces, so the textbf pattern cannot match until
    # the emph inside it is gone -- and by then textbf's turn has passed.
    # That left a literal "\textbfRole" in the output, which the guard below
    # caught.
    for _ in range(10):
        before = t
        for cmd in ("textbf", "emph", "textsc", "text"):
            t = re.sub(r"\\" + cmd + r"\{([^{}]*)\}", r"\1", t)
        if t == before:
            break
    t = (t.replace(r"\rightarrow", "->").replace(r"\times", "x")
          .replace(r"\%", "%").replace(r"\,", " "))
    t = re.sub(r"\$([^$]*)\$", lambda m: m.group(1), t)
    t = t.replace("{,}", ",").replace("^{-8}", "^-8").replace("{-}", "-")
    t = t.replace("---", "--").replace("{", "").replace("}", "")
    t = re.sub(r"\s+", " ", t).strip()
    # Nothing may survive that would read as markup in a plain-text box.
    leftover = re.findall(r"\\[a-zA-Z]+", t)
    if leftover:
        raise SystemExit(f"abstract plaintext still contains LaTeX: {leftover}")
    return t


abstract_txt = abstract_plaintext(abstract_src)
abstract_words = len(abstract_txt.split())
# Written out so the submission form is filled from a file, not from a
# hand-retyped paragraph that can drift from the compiled paper.
open("ABSTRACT_SUBMIT.txt", "w").write(abstract_txt + "\n")

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
# Bibliography: entries present, entries rendered, and -- the one that
# matters -- that every \cite resolves. An uncited entry is harmless (bibtex
# drops it); an unresolved \cite ships a "[?]".
gates["bib_entries"] = len(re.findall(r"^@[a-zA-Z]+\{", open("refs.bib").read(), re.M))
gates["bib_rendered"] = (len(re.findall(r"\\bibitem", open("main.bbl").read()))
                         if os.path.exists("main.bbl") else 0)

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
    # BYTE hashes of a PDF change on every build -- pdflatex embeds a
    # wall-clock CreationDate -- so they identify a BUILD, not a paper. Record
    # them, but the field that answers "is this the same paper?" is the TEXT
    # hash below, which is stable across rebuilds and across machines. The
    # Overleaf equivalence check compares the text hash for that reason.
    "main_pdf_sha256_build": sha("main.pdf"),
    "main_pdf_bytes": os.path.getsize("main.pdf"),
    # Hashed over the RAW pdftotext bytes, so this equals what
    #     pdftotext main.pdf - | shasum -a 256
    # prints. `sh()` strips trailing whitespace, and a recorded number that
    # the documented command does not reproduce is worse than no number --
    # whoever checks it concludes the paper changed.
    "main_text_sha256": hashlib.sha256(
        subprocess.run(["pdftotext", "main.pdf", "-"],
                       capture_output=True).stdout).hexdigest(),
    "supplement_pdf_sha256_build": sha("supplement.pdf") if gates["supplement_exists"] else None,
    "supplement_text_sha256": (hashlib.sha256(
        subprocess.run(["pdftotext", "supplement.pdf", "-"],
                       capture_output=True).stdout).hexdigest()
        if gates["supplement_exists"] else None),
    "figures_used": figs,
    "figures_missing": missing,
    "abstract_sha256": hashlib.sha256(abstract_src.encode()).hexdigest(),
    "abstract_words_approx": abstract_words,
    "abstract_plaintext": "paper/ABSTRACT_SUBMIT.txt",
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
