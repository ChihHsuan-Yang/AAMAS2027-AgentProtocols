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
