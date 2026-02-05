#!/usr/bin/env python3
"""Repository health audit for codex-web.

Generates a markdown report with high-level structure metrics and hygiene warnings.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def top_level_file_counts(root: Path) -> Counter:
    counts: Counter[str] = Counter()
    for dp, _, files in os.walk(root):
        if "/.git" in dp:
            continue
        rel = dp[len(str(root)) + 1 :] if dp.startswith(str(root) + os.sep) else "."
        top = rel.split(os.sep, 1)[0] if rel and rel != "." else "."
        counts[top] += len(files)
    return counts


def git_ls_files(root: Path) -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=root, text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def generate_report(root: Path, top_n: int = 15, noisy_threshold: int = 1000) -> str:
    counts = top_level_file_counts(root)
    tracked = git_ls_files(root)

    tracked_node_modules = [p for p in tracked if "/node_modules/" in p]
    tracked_venv = [p for p in tracked if p.startswith(".venv/") or "/.venv/" in p]
    tracked_backups = [p for p in tracked if p.startswith("backups_reorg/")]

    large_dirs = [(name, cnt) for name, cnt in counts.most_common() if cnt >= noisy_threshold]

    lines: list[str] = []
    lines.append("# codex-web Repository Health Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Top-level directories scanned: **{len(counts)}**")
    lines.append(f"- Tracked files: **{len(tracked)}**")
    lines.append(f"- Tracked `node_modules` files: **{len(tracked_node_modules)}**")
    lines.append(f"- Tracked `.venv` files: **{len(tracked_venv)}**")
    lines.append(f"- Tracked `backups_reorg` files: **{len(tracked_backups)}**")
    lines.append("")

    lines.append("## Top-level file density")
    lines.append("")
    lines.append("| Directory | File count |")
    lines.append("|---|---:|")
    for name, cnt in counts.most_common(top_n):
        lines.append(f"| `{name}` | {cnt} |")
    lines.append("")

    lines.append("## Risk flags")
    lines.append("")
    if not large_dirs and not tracked_node_modules and not tracked_venv:
        lines.append("- No high-risk structural flags detected with current thresholds.")
    else:
        for name, cnt in large_dirs:
            lines.append(f"- High file volume in `{name}`: {cnt} files (threshold: {noisy_threshold}).")
        if tracked_node_modules:
            lines.append("- Tracked `node_modules` content detected. This can create very noisy diffs and large commits.")
        if tracked_venv:
            lines.append("- Tracked `.venv` content detected. Virtual environments should typically be untracked.")
        if tracked_backups:
            lines.append("- Tracked `backups_reorg` content detected. Consider moving long-term backups to external storage.")
    lines.append("")

    lines.append("## Recommended next actions")
    lines.append("")
    lines.append("1. Untrack dependency/vendor trees gradually (start with `node_modules` and `.venv`) in controlled PRs.")
    lines.append("2. Keep archives in `archive/` or external object storage; retain only curated snapshots in Git.")
    lines.append("3. Add CI checks that run Python tests and selected app checks on each PR.")
    lines.append("4. Continue modular documentation under `docs/` to reduce README bloat.")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate codex-web repository health report")
    parser.add_argument("--output", default="docs/reports/repo_health_report.md", help="Output markdown path")
    parser.add_argument("--top", type=int, default=15, help="Top directory count rows")
    parser.add_argument("--threshold", type=int, default=1000, help="Noisy directory threshold")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    report = generate_report(root=root, top_n=args.top, noisy_threshold=args.threshold)
    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote report: {out_path}")


if __name__ == "__main__":
    main()
