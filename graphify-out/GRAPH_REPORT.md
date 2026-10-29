# Graph Report - conductor  (2026-10-29)

## Corpus Check
- Corpus is ~8,071 words - fits in a single context window. You may not need a graph.

## Summary
- 147 nodes · 249 edges · 21 communities (7 shown, 14 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Conductor CLI Core
- Plan & Routing Tests
- Installer & Misc Tests
- Benchmark Runner
- Project Documentation
- Roles & Safety Docs
- Detection Tests
- Registry Tests
- Brief Templates
- Brief Tests
- Probe Mechanism Docs
- Antigravity Harness Notes
- Wave Scheduling Docs
- Decide & Verify Steps
- Claude Code Harness
- Codex Harness
- Gemini CLI Harness
- Verification Step
- Report Step

## God Nodes (most connected - your core abstractions)
1. `run_task()` - 12 edges
2. `avail()` - 12 edges
3. `_dispatch()` - 11 edges
4. `fanout()` - 9 edges
5. `Plans` - 9 edges
6. `main()` - 8 edges
7. `probe()` - 8 edges
8. `Routing` - 8 edges
9. `run_review_suite()` - 7 edges
10. `main()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Conductor skill definition (SKILL.md)` --implements--> `Conductor project`  [INFERRED]
  skills/conductor/SKILL.md → README.md
- `Conductor project` --references--> `install.py installer script`  [EXTRACTED]
  README.md → .github/workflows/tests.yml
- `Roles table (SKILL.md)` --conceptually_related_to--> `Roles to permissions mapping`  [INFERRED]
  skills/conductor/SKILL.md → README.md
- `Safety rules (SKILL.md)` --conceptually_related_to--> `Safety rules (README)`  [INFERRED]
  skills/conductor/SKILL.md → README.md
- `CI Test Workflow (tests.yml)` --references--> `python -m unittest discover -s tests command`  [EXTRACTED]
  .github/workflows/tests.yml → CONTRIBUTING.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Harnesses benchmarked in cross-review** — readme_claude_code, readme_copilot_cli, readme_hermes, readme_antigravity, readme_cross_review_benchmark [EXTRACTED 1.00]
- **Conductor delegation workflow steps** — skills_conductor_skill_conductor_detect_step, skills_conductor_skill_conductor_decide_delegate_step, skills_conductor_skill_conductor_write_brief_step, skills_conductor_skill_conductor_dispatch_step, skills_conductor_skill_conductor_verify_step, skills_conductor_skill_conductor_report_step [EXTRACTED 1.00]
- **Supported coding agent harnesses** — readme_claude_code, readme_copilot_cli, readme_antigravity, readme_hermes, readme_codex, readme_gemini_cli, readme_openclaw [EXTRACTED 1.00]

## Communities (21 total, 14 thin omitted)

### Community 0 - "Conductor CLI Core"
Cohesion: 0.17
Nodes (21): build_command(), depth(), detect(), _dispatch(), fanout(), _first_line(), _kill_tree(), load_registry() (+13 more)

### Community 1 - "Plan & Routing Tests"
Cohesion: 0.18
Nodes (5): avail(), Plans, runner(), flaky(), Routing

### Community 2 - "Installer & Misc Tests"
Cohesion: 0.15
Nodes (6): main(), project_targets(), user_targets(), Installer, RunTask, SkillSpec

### Community 3 - "Benchmark Runner"
Cohesion: 0.23
Nodes (6): _bug_lines(), hidden_pass(), main(), run_detect_suite(), run_parallel_suite(), run_review_suite()

### Community 4 - "Project Documentation"
Cohesion: 0.15
Nodes (16): bench/run_bench.py benchmark runner, Contributing guide, python -m unittest discover -s tests command, CI Test Workflow (tests.yml), install.py installer script, Comparison to other orchestrators, Conductor project, Cross-review benchmark (8 seeded bugs) (+8 more)

### Community 5 - "Roles & Safety Docs"
Cohesion: 0.25
Nodes (7): GitHub Copilot CLI harness, Dogfooded self-review findings, Hermes Agent harness, OpenClaw harness, Roles to permissions mapping, Safety rules (README), Roles table (SKILL.md)

### Community 8 - "Brief Templates"
Cohesion: 0.50
Nodes (5): Implement brief template, Research brief template, Review brief template, Test brief template, Write the brief step

## Knowledge Gaps
- **23 isolated node(s):** `Parallel fan-out benchmark (2.1x faster)`, `Cross-review benchmark (8 seeded bugs)`, `Detection/probe benchmark`, `Waves (parallel tasks with dependencies)`, `Conductor verifies step` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 58 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Plans` connect `Plan & Routing Tests` to `Installer & Misc Tests`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **What connects `Parallel fan-out benchmark (2.1x faster)`, `Cross-review benchmark (8 seeded bugs)`, `Detection/probe benchmark` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Installer & Misc Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.14619883040935672 - nodes in this community are weakly interconnected._
- **Why does `avail()` connect `Plan & Routing Tests` to `Installer & Misc Tests`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `Registry` connect `Registry Tests` to `Installer & Misc Tests`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._