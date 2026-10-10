#!/bin/sh
cd "$(dirname "$0")"
TZ=UTC pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1
bibtex main >/dev/null 2>&1
TZ=UTC pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1
TZ=UTC pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1
grep -E "^! |Overfull|undefined|multiply" main.log | sort | uniq -c
pdfinfo main.pdf | grep Pages
