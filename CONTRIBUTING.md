# Contributing

Conductor is one stdlib-only Python script plus a JSON registry. Keep it that way.

- **A CLI changed its flags / a new agent CLI exists:** edit
  `skills/conductor/scripts/harnesses.json`. Verify flags from the CLI's own
  `--help`, and paste the `detect --probe` output in the PR.
- **Tests:** `python -m unittest discover -s tests`. They need no agent CLIs.
- **Benchmarks:** `python bench/run_bench.py` runs real agents and costs real
  tokens. Only commit numbers you measured; include the generated JSON from
  `bench/results/`.
- Python 3.9+ compatible, no third-party dependencies.
