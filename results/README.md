# Recorded output

Everything here was produced by the commands named below, from the run pinned at
`prereg_fp = 42a8c37dc4b6e7e7` (9 arms x 16 seeds x 12 generations, seeds
100-115). No file here was edited by hand.

| file | produced by |
|---|---|
| `runs.jsonl` | `cusm.py run --preset main` — 144 arm-seed runs, every checkpoint and every modification event |
| `shards/*.jsonl` | the same run, sharded one process per arm; concatenating them reproduces `runs.jsonl` |
| `controls.txt` / `.json` | `cusm.py controls` — 33/33 |
| `tests.txt` | `python -m unittest discover -s tests` — 50/50 |
| `summary_table.txt` | `cusm.py report` |
| `analysis.txt` / `.json` | `cusm.py analyse` — preregistered verdicts |
| `sensitivity.txt` / `.json` | `cusm.py sensitivity` — minimum detectable effect per contrast |
| `experiments/*.txt` | the corresponding script in `experiments/` |

Sharding is result-neutral: every arm-seed run is independent and every random
stream is keyed by decision-site name rather than drawn from a shared sequence.
