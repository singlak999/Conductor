#!/usr/bin/env python3
"""Reproducible benchmark for conductor. Runs real agent CLIs; costs real tokens.

  python bench/run_bench.py                      # all suites
  python bench/run_bench.py --suite parallel --harnesses claude,codex
Writes bench/results/<date>.json and prints a markdown table.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import platform
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "skills" / "conductor" / "scripts"))
import conductor as c  # noqa: E402

TASKS = {
    "slugify": ("Create slug.py with def slugify(text: str) -> str. Lowercase; convert accented letters to ASCII "
                "(e.g. e-acute becomes e); every run of characters that are not a-z or 0-9 becomes a single hyphen; "
                "strip leading and trailing hyphens; empty or symbol-only input returns an empty string.",
                "from slug import slugify as f\n"
                "assert f('Hello, World!') == 'hello-world'\nassert f('  --a__b--  ') == 'a-b'\n"
                "assert f('Caf\\u00e9 \\u00dcber') == 'cafe-uber'\nassert f('!!!') == ''\nassert f('') == ''\n"
                "assert f('A1 b2') == 'a1-b2'\n"),
    "duration": ("Create duration.py with def parse_duration(s: str) -> int returning seconds. Accepts one or "
                 "more number+unit parts with units d, h, m, s in any order, e.g. 1h30m, 90s, 2d4h, 1m1s. "
                 "Whitespace between parts is allowed. Raise ValueError for empty input, unknown units, "
                 "a number without a unit, or a repeated unit.",
                 "from duration import parse_duration as f\n"
                 "assert f('1h30m') == 5400\nassert f('90s') == 90\nassert f('2d4h') == 187200\n"
                 "assert f('1m 1s') == 61\nassert f('30m1h') == 5400\n"
                 "for bad in ['', '5', '3x', '1h1h', 'h']:\n"
                 "    try:\n        f(bad)\n    except ValueError:\n        pass\n"
                 "    else:\n        raise AssertionError(bad)\n"),
    "roman": ("Create roman.py with def roman_to_int(s: str) -> int for valid uppercase Roman numerals 1 to 3999 "
              "and raise ValueError for invalid ones, including bad characters, empty string, and non-canonical "
              "forms such as IIII, VV, IC, IL, XM.",
              "from roman import roman_to_int as f\n"
              "assert f('MCMXCIV') == 1994\nassert f('III') == 3\nassert f('MMMCMXCIX') == 3999\n"
              "assert f('XLII') == 42\n"
              "for bad in ['', 'IIII', 'VV', 'IC', 'IL', 'XM', 'ABC', 'mcm']:\n"
              "    try:\n        f(bad)\n    except ValueError:\n        pass\n"
              "    else:\n        raise AssertionError(bad)\n"),
    "intervals": ("Create intervals.py with def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]. "
                  "Merge overlapping or touching closed intervals, e.g. (1,3) and (3,5) become (1,5). Input may be "
                  "unsorted and contain reversed pairs like (5,1), which mean (1,5). Return a sorted list of tuples. "
                  "Do not mutate the input.",
                  "from intervals import merge as f\n"
                  "x = [(5, 1), (2, 3)]\nassert f(x) == [(1, 5)]\nassert x == [(5, 1), (2, 3)]\n"
                  "assert f([(1, 3), (3, 5), (7, 8)]) == [(1, 5), (7, 8)]\nassert f([]) == []\n"
                  "assert f([(8, 9), (1, 2)]) == [(1, 2), (8, 9)]\n"),
}

SUFFIX = " Only create that one file in the current directory. Do not create tests or other files."

BUGGY = '''\
import json
import time


def load_users(path):
    with open(path) as fh:
        return json.load(fh)


def average_age(users):
    total = 0
    for u in users:
        total += u["age"]
    return total / len(users) if users else 0


def oldest(users):
    best = users[0]
    for u in users[1:]:
        if u["age"] < best["age"]:
            best = u
    return best


def paginate(items, page, size):
    start = page * size
    return items[start:start + size - 1]


def is_adult(user):
    return user["age"] > 18


def add_tag(user, tag, tags=[]):
    tags.append(tag)
    user["tags"] = tags
    return user


def retry(fn, attempts=3):
    for i in range(attempts):
        try:
            return fn()
        except Exception:
            time.sleep(2 ** i)


def find_by_email(users, email):
    for u in users:
        if u["email"] == email.lower:
            return u
    return None


def chunk(items, n):
    return [items[i:i + n] for i in range(0, len(items) - n, n)]


def median(values):
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid] + s[mid + 1]) / 2
'''


def _bug_lines() -> dict[str, int]:
    lines = BUGGY.splitlines()
    marks = {"oldest": 'if u["age"] < best["age"]', "paginate": "start + size - 1",
             "is_adult": 'user["age"] > 18', "add_tag": "tags=[]", "retry": "time.sleep(2 ** i)",
             "find_by_email": "email.lower:", "chunk": "len(items) - n", "median": "s[mid + 1]"}
    return {k: next(i + 1 for i, ln in enumerate(lines) if v in ln) for k, v in marks.items()}


REVIEW_PROMPT = ("Review users.py in the current directory for real bugs (logic errors, wrong results, crashes, "
                 "silent failures). Do not edit anything. For every bug output one line in exactly this form: "
                 "BUG <line number> - <short description>. Output nothing else besides the summary line.")


def hidden_pass(task_dir: Path, name: str) -> bool:
    test = task_dir / f"_hidden_{name}.py"
    test.write_text(TASKS[name][1], encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, test.name], cwd=task_dir, capture_output=True, timeout=60)
        return r.returncode == 0
    finally:
        test.unlink()


def run_parallel_suite(reg, available, harnesses, timeout):
    by_id = {h["id"]: h for h in available}
    out = {}
    configs = {
        f"sequential, 1 agent ({harnesses[0]})": ([harnesses[0]] * len(TASKS), 1),
        f"conductor fanout, 1 agent x{len(TASKS)} ({harnesses[0]})": ([harnesses[0]] * len(TASKS), len(TASKS)),
        f"conductor fanout, {len(harnesses)} agents": ([harnesses[i % len(harnesses)] for i in range(len(TASKS))],
                                                      len(TASKS)),
    }
    for label, (pins, par) in configs.items():
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tasks = []
            for (name, (spec, _)), hid in zip(TASKS.items(), pins):
                (root / name).mkdir()
                tasks.append({"id": name, "role": "implement", "harness": hid, "cwd": str(root / name),
                              "prompt": spec + SUFFIX})
            t0 = time.monotonic()
            res = c.fanout({"tasks": tasks}, reg, [by_id[h] for h in set(pins)], root / ".runs",
                           max_parallel=par, timeout=timeout)
            wall = round(time.monotonic() - t0, 1)
            passed = {r["id"]: hidden_pass(root / r["id"], r["id"]) for r in res}
        out[label] = {"wall_seconds": wall, "passed": sum(passed.values()), "total": len(TASKS),
                      "per_task": {r["id"]: {"harness": r["harness"], "status": r["status"],
                                             "seconds": r["seconds"], "hidden_tests": passed[r["id"]]} for r in res}}
        print(f"  {label}: {wall}s, {sum(passed.values())}/{len(TASKS)} hidden tests", flush=True)
    return out


def run_review_suite(reg, available, harnesses, timeout):
    truth = _bug_lines()
    by_id = {h["id"]: h for h in available}
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "users.py").write_text(BUGGY, encoding="utf-8")
        tasks = [{"id": f"review-{h}", "role": "review", "harness": h, "cwd": str(root), "prompt": REVIEW_PROMPT}
                 for h in harnesses]
        t0 = time.monotonic()
        res = c.fanout({"tasks": tasks}, reg, [by_id[h] for h in harnesses], root / ".runs",
                       max_parallel=len(tasks), timeout=timeout)
        wall = round(time.monotonic() - t0, 1)
        untouched = (root / "users.py").read_text(encoding="utf-8") == BUGGY
        per, union = {}, set()
        for r in res:
            text = Path(r["log"]).read_text(encoding="utf-8", errors="replace") if r["log"] else r["tail"]
            reported = {int(n) for n in re.findall(r"BUG\s+(?:line\s+)?(\d+)", text)}
            found = {k for k, ln in truth.items() if any(abs(ln - x) <= 2 for x in reported)}
            union |= found
            per[r["harness"]] = {"status": r["status"], "seconds": r["seconds"], "found": sorted(found),
                                 "recall": f"{len(found)}/{len(truth)}"}
            print(f"  {r['harness']}: {len(found)}/{len(truth)} bugs, {r['seconds']}s", flush=True)
    print(f"  union: {len(union)}/{len(truth)}", flush=True)
    return {"seeded_bugs": len(truth), "per_harness": per, "union_recall": f"{len(union)}/{len(truth)}",
            "wall_seconds": wall, "file_unmodified": untouched}


def run_detect_suite(reg):
    t0 = time.monotonic()
    found = c.detect(reg)
    t_detect = round(time.monotonic() - t0, 2)
    probes = {}
    for h in found:
        p = c.probe(reg, h)
        probes[h["id"]] = {"ready": p["ready"], "seconds": p["probe_seconds"], "note": p["note"]}
    return {"detect_seconds": t_detect, "installed": [f"{h['id']} {h['version']}" for h in found], "probe": probes}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=["all", "detect", "parallel", "review"], default="all")
    ap.add_argument("--harnesses", help="comma list; default: every ready harness")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()
    reg = c.load_registry()
    available = c.detect(reg)
    result = {"date": dt.date.today().isoformat(), "machine": f"{platform.system()} {platform.release()}, "
              f"Python {platform.python_version()}"}
    if args.suite in ("all", "detect"):
        print("detect/probe", flush=True)
        result["detect"] = run_detect_suite(reg)
    if args.harnesses:
        harnesses = args.harnesses.split(",")
    elif "detect" in result:
        harnesses = [h for h, p in result["detect"]["probe"].items() if p["ready"]]
    else:
        harnesses = [h["id"] for h in available if c.probe(reg, h).get("ready")]
    result["harnesses"] = harnesses
    if args.suite in ("all", "parallel"):
        print("parallel", flush=True)
        result["parallel"] = run_parallel_suite(reg, available, harnesses, args.timeout)
    if args.suite in ("all", "review"):
        print("review", flush=True)
        result["review"] = run_review_suite(reg, available, harnesses, args.timeout)
    out = HERE / "results" / f"{result['date']}-{args.suite}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
