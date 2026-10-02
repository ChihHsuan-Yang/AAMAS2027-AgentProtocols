#!/usr/bin/env python3
"""Verify every repo-relative path and markdown link in the documentation.

WHY.  A navigation document whose links do not resolve is worse than no
document: it sends a new collaborator to a path that does not exist and
costs them the time it was meant to save. This project has had a README
naming a dead canonical path before.

WHAT IT CHECKS, in the files that are meant to be navigation:
  * every markdown link target that is a repo-relative path -- these are
    navigation promises and must resolve
  * every `backtick path` CONTAINING A SLASH -- a directory-qualified path
    is a claim about where something is

WHAT IT DELIBERATELY DOES NOT CHECK, and why.  A first version flagged 88
references of which exactly one was real.  Bare basenames in prose --
`main.tex`, `FINAL_TABLES.py`, `MANIFEST.json` -- are not path claims; they
name a file the surrounding sentence has already located, and demanding
they resolve from the repo root produces noise that buries the one real
failure.  A check with an 87/88 false-positive rate is a check nobody runs.
Bare basenames are instead resolved anywhere in the repo, and reported only
if the name exists NOWHERE -- which catches the case that actually matters,
a file that was renamed or deleted.

It does NOT check external URLs -- it cannot, and a network check that
fails on a proxy would report a false broken link. Those are listed
separately as UNVERIFIED, which is the honest state.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = ["README.md", "HANDOFF_CURRENT.md", "SUBMISSION_PACKAGE.md",
        "SUBMISSION_CHECKLIST.md", "TODO.md", "paper/README.md",
        "paper/figures/README.md", "paper/tables/README.md",
        "docs/PAPER_ARTIFACT_MAP.md", "docs/DATA_PROVENANCE.md",
        "docs/TRACE_AVAILABILITY.md", "docs/REPRODUCIBILITY.md",
        "docs/INVALID_AND_SUPERSEDED.md"]

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CODE = re.compile(r"`([^`\n]+)`")
EXTS = (".md", ".py", ".tex", ".json", ".jsonl", ".bib", ".cls", ".bst",
        ".pdf", ".txt", ".parquet", ".sty")


def is_qualified_path(s):
    """A directory-qualified path -- a claim about WHERE something is.

    `hf:` marks a path inside the Hugging Face artifact repository, which
    is a different file tree. Those are real claims but not claims about
    THIS repo, so they are excluded here rather than silently passed --
    the prefix is what makes the distinction visible to a reader too.
    """
    s = s.strip()
    if s.startswith("hf:"):
        return False
    if not s or " " in s or s.startswith(("http", "#", "$", "-", "@")):
        return False
    if "*" in s or "{" in s or "\u2026" in s:      # glob, brace set, ellipsis
        return False
    return "/" in s and (s.endswith("/") or s.endswith(EXTS))


def is_basename(s):
    """A bare filename, which is a weaker claim: that the file EXISTS."""
    s = s.strip()
    return (s and " " not in s and "/" not in s and "*" not in s
            and s.endswith(EXTS) and not s.startswith("."))


_ALL = None
def exists_anywhere(name):
    global _ALL
    if _ALL is None:
        _ALL = set()
        for dp, dns, fns in os.walk(ROOT):
            dns[:] = [d for d in dns if d not in (".git", "__pycache__")]
            _ALL.update(fns)
    return name in _ALL


def main():
    broken, external, checked = [], set(), 0
    for doc in DOCS:
        dp = os.path.join(ROOT, doc)
        if not os.path.exists(dp):
            broken.append((doc, "<the document itself>", "document missing"))
            continue
        base = os.path.dirname(dp)
        text = open(dp, errors="ignore").read()

        for tgt in LINK.findall(text):
            if tgt.startswith(("http://", "https://")):
                external.add(tgt)
                continue
            if tgt.startswith("#"):
                continue                      # same-page anchor
            path = tgt.split("#")[0]
            checked += 1
            if not os.path.exists(os.path.join(base, path)):
                broken.append((doc, tgt, "link target does not exist"))

        for c in CODE.findall(text):
            if is_qualified_path(c):
                checked += 1
                # Resolve against the repo root AND the document's own
                # directory -- both spellings appear legitimately.
                if not (os.path.exists(os.path.join(ROOT, c))
                        or os.path.exists(os.path.join(base, c))):
                    broken.append((doc, c, "qualified path does not exist"))
            elif is_basename(c):
                checked += 1
                if not exists_anywhere(c):
                    broken.append((doc, c, "no file of this name exists "
                                           "anywhere in the repo"))

    nhf = sum(open(os.path.join(ROOT, d), errors="ignore").read().count("`hf:")
              for d in DOCS if os.path.exists(os.path.join(ROOT, d)))
    print(f"checked {checked} repo-relative references across "
          f"{len(DOCS)} documents")
    if nhf:
        print(f"  ({nhf} `hf:` references point into the Hugging Face "
              f"artifact repo -- a different tree, not checked here)")
    if external:
        print(f"\n{len(external)} external URLs NOT checked (no network "
              f"verification; reporting them as unverified rather than "
              f"claiming they resolve):")
        for u in sorted(external):
            print(f"    {u}")
    if broken:
        print(f"\n{len(broken)} BROKEN:")
        for doc, tgt, why in broken:
            print(f"    {doc}: {tgt!r} -- {why}")
        return 1
    print("\nAll repo-relative references resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
