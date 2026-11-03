# Reproducibility

The reproduction guide is in the repository README:
[Reproducing the paper](../README.md#reproducing-the-paper).

It covers three levels:

- **A** regenerates Table 2, the post-freeze supplement tables and every
  figure from the committed intermediate files (`make smoke`, `make figures`).
- **B** re-derives every number from the released trajectories and diffs it
  against the committed record (`make data numbers tables`).
- **C** re-runs inference against an OpenAI-compatible vLLM endpoint.

Every table and figure, with the script that generates it and the data it
reads, is listed in the [paper artifact matrix](reproduction/paper_artifact_matrix.md).

## Verified release baseline

The clean-environment reproduction reported on 2026-11-02 used code
`13f306b84eb5b5e1cfe42d4bb43cfb6acd8f89fc`, Roles dataset revision
`449d699969fae4e0f5df2add32497366dd34bb07` (data identical to `v1.2.0`),
and the supporting dataset revision
`1ffffb31c3cae02627b8a4be973a2b405c28529c`.
It reproduced the intermediate numbers and tables byte for byte and all six
figure PDFs pixel for pixel when rendered at 200 dpi. This is analysis
reproduction from released trajectories, not a new inference run.

The subsequent public-text synchronization aligns the manuscript and project
summaries with the final preprint. It does not change analysis code, raw data,
result tables, or scientific figure files. The website's `paper.pdf` includes
both the main paper and supplementary material.
