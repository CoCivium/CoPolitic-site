#!/usr/bin/env python3
"""Re-verify ai/sources.lock.json against GitHub using plain git (network, read-only).

For each locked source: fetch the locked commit (shallow, blob-less), confirm the
path resolves to the locked blob, and report whether the floating ref has since moved
the file. Exit 0 only if every locked blob exists at its locked commit.
Usage: python3 -I tools/verify_sources_lock.py [workdir]
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def main(work: Path) -> int:
    lock = json.loads((ROOT / "ai" / "sources.lock.json").read_text(encoding="utf-8"))
    failures, repos = 0, {}
    for s in lock["sources"]:
        repo = s["repo"]
        d = repos.get(repo)
        if d is None:
            d = work / repo.replace("/", "__")
            git("init", "-q", str(d), cwd=work)
            git("remote", "add", "origin", f"https://github.com/{repo}", cwd=d)
            repos[repo] = d
        git("fetch", "-q", "--depth=1", "--filter=blob:none", "origin", s["commit"], cwd=d)
        got = git("rev-parse", f'{s["commit"]}:{s["path"]}', cwd=d).stdout.strip()
        git("fetch", "-q", "--depth=1", "--filter=blob:none", "origin", s["ref"], cwd=d)
        now = git("rev-parse", f'FETCH_HEAD:{s["path"]}', cwd=d).stdout.strip() or "MISSING"
        ok = got == s["blob"]
        failures += not ok
        drift = "unchanged" if now == s["blob"] else f"DRIFTED->{now}"
        print(f'{"OK  " if ok else "FAIL"} {repo}@{s["commit"][:7]}:{s["path"]} ref {s["ref"]} {drift}')
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(main(Path(sys.argv[1]).resolve()))
    with tempfile.TemporaryDirectory() as t:
        sys.exit(main(Path(t)))
