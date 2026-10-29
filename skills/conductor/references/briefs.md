# Briefs and plans

## Brief templates

### implement
```
Goal: <one sentence outcome>.
Context: <what the code does, key files with paths, how they connect>.
Do: <numbered steps or acceptance criteria>.
Constraints: minimal change; follow existing style; no new dependencies unless
needed; do not commit; do not touch <paths>.
Done when: `<exact test/build command>` passes. Add tests for new behaviour in
<test file>.
```

### test
```
Goal: write tests that would catch bugs in <feature>.
Context: <spec of the behaviour, files>.
Do: add cases to <test file> covering normal input, edge cases (<list>), and
failure paths. Tests must fail on obviously wrong implementations.
Done when: `<test command>` runs; report which cases fail against the current code.
```

### review
```
Goal: find real bugs in the change below. Read only.
Scope: `git diff <base>` in <repo>, plus the code it calls.
Report: ranked list, max 10, each with file:line, the problem, a concrete repro
or failing input, and a suggested fix. No style nits. Say "no issues" if none.
```

### research
```
Goal: answer <question> from official docs/sources.
Report: concise answer with source URLs; mark anything you could not verify.
```

## Plan format (fanout)

```json
{
  "cwd": "/path/to/repo",
  "tasks": [
    {"id": "api",     "role": "implement", "prompt": "..."},
    {"id": "ui",      "role": "implement", "prompt": "...", "harness": "claude"},
    {"id": "tests",   "role": "test",      "prompt": "..."},
    {"id": "review",  "role": "review",    "prompt": "Review the api and ui changes.",
     "depends_on": ["api", "ui"]}
  ]
}
```

- Tasks with no `depends_on` run in the first wave, in parallel.
- A task runs after everything it depends on; the tail of each upstream
  output is appended to its brief.
- If an upstream task fails or times out, its dependents are skipped.
- Optional per task: `harness` (pin an agent), `mode` (`read|edit|full`),
  `model`, `cwd`.
- Parallel tasks that edit files should touch different files, or use
  separate git worktrees as their `cwd`.
