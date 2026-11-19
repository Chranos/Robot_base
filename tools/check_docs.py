#!/usr/bin/env python3
"""Static documentation checks; never execute documented server commands."""
from pathlib import Path
import json
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["README.md", "CONTRIBUTING.md", "docs/review.md",
    "docs/00-stack-map.md", "docs/01-infrastructure.md", "docs/02-foundations.md",
    "docs/03-robot-assets.md", "docs/04-ros2-moveit.md", "docs/05-isaac-runtime.md",
    "docs/06-fairino-simulation.md", "docs/07-perception-calibration.md",
    "docs/08-datasets-imitation.md", "docs/09-d1-max-rl.md", "docs/10-vla-libero.md",
    "docs/11-sim-to-real.md", "docs/12-experiments.md", "docs/13-troubleshooting.md",
    "docs/14-learning-roadmap.md", "docs/15-runbooks.md", "docs/16-evidence.md",
    "evidence/2026-11-19-inventory.json"]
errors = []
links = blocks = 0
for name in REQUIRED:
    if not (ROOT / name).is_file():
        errors.append(f"Missing required document: {name}")
files = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]
for path in files:
    if path.suffix.lower() in {".pem", ".key", ".pt", ".pth", ".mp4", ".zip"}:
        errors.append(f"Unexpected credential/binary/asset file: {path.relative_to(ROOT)}")
    if path.suffix not in {".md", ".json", ".py", ".yml", ".yaml"}:
        continue
    source = path.read_text()
    # Detect concrete secrets, not prose describing credential boundaries.
    for pattern in [r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
                    r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{30,}",
                    r"sshpass\s+-p\s+['\"]?\w+", r"sk-[A-Za-z0-9]{30,}"]:
        if re.search(pattern, source):
            errors.append(f"Possible secret in {path.relative_to(ROOT)}")
    if path.suffix == ".json":
        try:
            json.loads(source)
        except ValueError as exc:
            errors.append(f"Invalid JSON: {path.relative_to(ROOT)}: {exc}")
    if path.suffix != ".md":
        continue
    lines = source.splitlines()
    if sum(line.startswith("```") for line in lines) % 2:
        errors.append(f"Unclosed code fence: {path.relative_to(ROOT)}")
    prose = re.sub(r"```.*?```", "", source, flags=re.S)
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", prose):
        target = target.strip("<>").split("#", 1)[0]
        if not target or re.match(r"[A-Za-z]+:", target):
            continue
        links += 1
        if not (path.parent / unquote(target)).is_file():
            errors.append(f"Broken local link: {path.relative_to(ROOT)} -> {target}")
    for block in re.findall(r"```bash\n(.*?)```", source, re.S):
        blocks += 1
        check = subprocess.run(["bash", "-n"], input=block, text=True, capture_output=True)
        if check.returncode:
            errors.append(f"Bash syntax: {path.relative_to(ROOT)}: {check.stderr.strip()}")

print(json.dumps({"documents": len([p for p in files if p.suffix == '.md']),
                  "local_links": links, "bash_blocks_syntax_checked": blocks,
                  "errors": errors, "note": "Static checks do not establish runtime success or independent review."},
                 indent=2, ensure_ascii=False))
sys.exit(bool(errors))
