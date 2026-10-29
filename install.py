#!/usr/bin/env python3
"""Install the conductor skill into every agent harness found on this machine.

  python install.py            # user-level install for all detected harnesses
  python install.py --project  # install into ./.agents/skills and ./.claude/skills
  python install.py --dry-run
  python install.py --uninstall
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent / "skills" / "conductor"
NAME = "conductor"


def user_targets(home: Path, env: dict, which=shutil.which) -> list[tuple[str, Path]]:
    hermes_home = Path(env["HERMES_HOME"]) if env.get("HERMES_HOME") else home / ".hermes"
    # ~/.agents/skills is read by Copilot CLI, Codex, Gemini CLI and OpenClaw.
    targets = [("copilot, codex, gemini, openclaw", home / ".agents" / "skills")]
    if which("claude") or (home / ".claude").exists():
        targets.append(("claude", home / ".claude" / "skills"))
    if which("hermes") or hermes_home.exists():
        targets.append(("hermes", hermes_home / "skills"))
    if which("agy") or (home / ".gemini" / "antigravity").exists():
        targets.append(("antigravity", home / ".gemini" / "config" / "skills"))
    return targets


def project_targets(cwd: Path) -> list[tuple[str, Path]]:
    return [("copilot, codex, gemini, openclaw, antigravity, hermes", cwd / ".agents" / "skills"),
            ("claude", cwd / ".claude" / "skills")]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", action="store_true", help="install into the current repo instead of your home dir")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    args = ap.parse_args(argv)
    targets = project_targets(Path.cwd()) if args.project else user_targets(Path.home(), dict(os.environ))
    for who, root in targets:
        dest = root / NAME
        if args.uninstall:
            action = "remove" if dest.exists() else "absent"
            if dest.exists() and not args.dry_run:
                shutil.rmtree(dest)
        else:
            action = "update" if dest.exists() else "install"
            if not args.dry_run:
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(SKILL, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"{action:<8} {dest}  ({who})")
    if not args.uninstall:
        print("\nNext: python " + str((targets[0][1] / NAME / "scripts" / "conductor.py")) + " detect --probe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
