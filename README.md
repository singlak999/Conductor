<div align="center">

# 🎼 Conductor

**One agent plans. Every agent on your machine works.**

A skill that finds the coding agents installed on your machine (Claude Code, Copilot CLI, Codex, Antigravity, Gemini CLI, Hermes, OpenClaw), checks which ones are actually signed in, and makes your current agent their conductor: it fans out tasks in parallel, routes each to the best fit, and has a *different* agent review the result.

[![tests](https://github.com/singlak999/Conductor/actions/workflows/tests.yml/badge.svg)](https://github.com/singlak999/Conductor/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![deps](https://img.shields.io/badge/dependencies-0-brightgreen)
![license](https://img.shields.io/badge/license-MIT-green)

</div>

```text
you ──► your agent (conductor)
            ├─ detect --probe ──► claude ✓  copilot ✓  antigravity ✓  hermes ✓  codex ✗ (auth expired)
            ├─ wave 1 (parallel) ─► claude: api   antigravity: ui   hermes: tests
            ├─ wave 2 ───────────► copilot: review (never the agent that wrote it)
            └─ verifies diffs + runs tests itself, then reports
```

## Measured, not claimed

Every number below comes from one real run of [`bench/run_bench.py`](bench/run_bench.py) on 2026-10-29: Windows 10, Python 3.11, Claude Code 2.1.220, Copilot CLI 1.0.105, Antigravity 1.4.10, Hermes 0.21.4. Raw output is in [`bench/results/`](bench/results/). Run it yourself; it uses your own agent subscriptions.

### 1. Parallel fan-out: 2.1× faster, same quality

Four small coding tasks (slugify, duration parser, Roman numerals, interval merge), each graded by **hidden tests the agent never saw**.

| Setup | Wall time | Hidden tests passed |
|---|---:|---:|
| One agent (Claude Code), tasks one after another | 225.4 s | 4 / 4 |
| **Conductor fan-out**, 4 × Claude Code in parallel | **107.8 s** (2.09× faster) | **4 / 4** |
| **Conductor fan-out**, 4 different agents in parallel | 206.2 s | **4 / 4** |

With four different agents the wave finishes when the slowest one does (Antigravity took 206 s on its task), so mixing vendors buys a second opinion, not speed.

### 2. Cross-review: every agent, in parallel, read-only

A 62-line module with **8 seeded bugs** (off-by-one, mutable default, `email.lower` without `()`, swallowed exceptions, …). Each ready agent reviewed it in read-only mode at the same time. Numbers are from the rerun with the shipped flags ([`2026-10-29-review.json`](bench/results/2026-10-29-review.json)).

| Reviewer | Bugs found | Time |
|---|---:|---:|
| Claude Code | 8 / 8 | 41.7 s |
| Copilot CLI | 8 / 8 | 57.8 s |
| Hermes | 8 / 8 | 69.9 s |
| Antigravity | 8 / 8 | 276.6 s (126.5 s in the earlier run) |
| **All four via conductor (parallel)** | **8 / 8** | **276.7 s wall** (vs 446.0 s back-to-back) |

The module file was byte-identical after both runs. Honest caveat: these seeded bugs were easy enough that every agent found all of them, so this measures reliability and wall-clock time, not which reviewer is best. Parallel review is bounded by the slowest agent.

### 3. Detection that tells the truth

| Check | Result |
|---|---|
| Scan 7 known harnesses (PATH + versions) | 16.1 s, found 6 |
| Probe each with a real prompt | 9.8–35.7 s each |
| Agents correctly marked **not ready** | Codex (expired login), Gemini CLI (account tier no longer supported) |

The probe asks a question whose answer has to be computed (`READY-42`), because our first version was fooled by a CLI that echoed the prompt back while its login was broken. More on that below.

## Install

```bash
git clone https://github.com/singlak999/Conductor
python Conductor/install.py            # every harness found on this machine
python Conductor/install.py --project  # or just this repo (.agents/skills + .claude/skills)
```

The installer copies `skills/conductor/` to:

| Harness | Skill directory |
|---|---|
| Copilot CLI, Codex, Gemini CLI, OpenClaw | `~/.agents/skills/` (always) |
| Claude Code | `~/.claude/skills/` |
| Hermes | `$HERMES_HOME/skills/` (default `~/.hermes/skills/`) |
| Antigravity | `~/.gemini/config/skills/` |

Prefer doing it by hand? Copy `skills/conductor` into any of those folders. `python install.py --uninstall` removes it again.

## Use

Just ask your agent:

> *"Use conductor: implement the export endpoint, write tests for it in parallel, then get a different agent to review both."*
>
> *"Get a second opinion from codex on this diff."*
>
> *"Fan these four refactors out to whatever agents I have."*

Or drive it directly:

```bash
python skills/conductor/scripts/conductor.py detect --probe
python skills/conductor/scripts/conductor.py run auto --role review --prompt "Review git diff main for bugs"
python skills/conductor/scripts/conductor.py fanout plan.json --max-parallel 4
```

```json
{
  "cwd": ".",
  "tasks": [
    {"id": "api",    "role": "implement", "prompt": "..."},
    {"id": "tests",  "role": "test",      "prompt": "...", "harness": "hermes"},
    {"id": "review", "role": "review",    "prompt": "Review the api change.", "depends_on": ["api"]}
  ]
}
```

Each run writes `.conductor/runs/<time>/` with every brief, full log, and `results.json`.

## Supported harnesses

| Harness | Headless command used | Status |
|---|---|---|
| Claude Code | `claude -p … --permission-mode acceptEdits --allowedTools …` | ✅ benchmarked |
| GitHub Copilot CLI | `copilot -p … -s --no-ask-user` (+ `--allow-tool=write` / `--allow-all-tools`) | ✅ benchmarked |
| Google Antigravity | `agy --print … --mode plan\|accept-edits\|auto` | ✅ benchmarked |
| Hermes Agent | `hermes -z … -t file,web` (read/edit), `--yolo` (full) | ✅ benchmarked; read mode can't block file writes, so auto-routing doesn't pick it for reviews |
| OpenAI Codex CLI | `codex exec -s read-only\|workspace-write …` | ⚠️ wired, flags verified; our login had expired so not benchmarked |
| Gemini CLI | `gemini -p … --approval-mode plan\|auto_edit\|yolo` | ⚠️ wired, flags verified; free tier now redirects to Antigravity |
| OpenClaw | `openclaw agent --local --message …` | 🧪 untested, contributions welcome |

A CLI changed its flags, or you use one we don't list? Edit [`harnesses.json`](skills/conductor/scripts/harnesses.json) or drop an override in `~/.conductor/harnesses.json`. No code change needed.

## How it works

- **Roles → permissions.** `implement`/`test` run with edit + shell, `docs` edit only, `review`/`research` read-only. Each role has a preference order; `auto` takes the first installed agent that isn't you, skipping agents a probe marked not ready. An unknown role is an error, never a silent default.
- **Waves.** Tasks without dependencies run in parallel; dependents get the tail of their upstream output, fenced and labelled as untrusted data; if an upstream fails, its dependents are skipped, not run on garbage. A crashing worker is recorded as `error` without losing the other results.
- **No self-grading.** An auto-routed review never goes to the agent that wrote the code, unless no other agent exists; then the result carries a `note` saying so.
- **Briefs as files.** The worker gets a one-line pointer to a full brief on disk. Windows `.cmd` shims mangle multi-line arguments; this sidesteps that everywhere.
- **The conductor verifies.** The skill tells your agent to treat "done" as a claim: read the diff, rerun the tests, then report.

## Safety

- Workers never commit, push, or deploy; the brief says so, and the conductor does those steps only after verification.
- Reviews and research run in each CLI's read-only mode (verified in the benchmark: the reviewed file was unchanged). Hermes and OpenClaw have no read mode that blocks writes; they're used for read roles only when pinned or when nothing else is installed.
- Workers start without the parent's session variables, and delegation stops at depth 2: no infinite agent recursion.
- Timeouts (task runs and probes) kill the whole process tree.
- Never put secrets in briefs; worker output is treated as untrusted input.

## Bugs the benchmark caught in conductor itself

The first benchmark run went badly, and that was useful:

1. **Probe false positive.** Codex echoes the prompt; our token was in the prompt; an expired login looked "ready". → The probe now asks for a computed answer and checks the exit code.
2. **Simultaneous starts hung.** Four Claude Code processes launched in the same instant: three finished in about 2 minutes, one sat silent until the 900 s timeout. → `fanout` now staggers launches of the same CLI by 5 s. Rerun: 4/4 in 107.8 s.
3. **Antigravity plan mode is too strict headless.** It denied the shell tool it used to read the brief, then printed nothing. → Read mode is now `--mode plan --sandbox`, auto-approving inside the sandbox, and was verified not to modify files.

## Dogfooded: conductor reviewed itself

Before release, conductor sent its own code to Claude Code as a read-only `review` task (204 s). It came back with 10 ranked, real findings, and all of them are fixed in this release:

- An unknown role (e.g. a `"reviewer"` typo) silently got full edit + shell access → now rejected.
- Hermes/OpenClaw "read" modes didn't block writes → marked `read_only: false`, avoided for reviews.
- Copilot read mode was allow-all minus a deny list → now default-deny (verified: reads work, write and shell refused).
- One crashing worker aborted the whole fan-out → recorded as `error`, others kept.
- Upstream output was pasted unframed into the next brief → fenced, labelled untrusted, can't fake the summary marker.
- Probe timeouts leaked child processes; relative plan `cwd`; run-dir collisions; junk `CONDUCTOR_DEPTH` crash → fixed.

That's the workflow conductor encourages: a second agent's review, then you verify and fix.

## Compared to

Orchestrators like claude-flow, Claude-Code-Workflow, maestro and metaswarm coordinate many copies of **one** agent, usually Claude. Conductor is deliberately small: one stdlib Python file plus a JSON registry, and it coordinates **different vendors' agents** that you already pay for, so you get real second opinions and spread the load across subscriptions.

## Develop

```bash
python -m unittest discover -s tests   # 32 tests, no agent CLIs needed
python bench/run_bench.py              # real agents, real tokens
```

See [CONTRIBUTING.md](CONTRIBUTING.md). MIT © singlak999.
