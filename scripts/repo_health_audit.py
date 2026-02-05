#!/usr/bin/env python3
"""Repository health audit for codex-web.

Generates markdown (and optional JSON) health reports with structural metrics,
risk flags, and an actionable cleanup roadmap.
"""

from __future__ import annotations

import argparse
import json
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


def compute_metrics(root: Path, top_n: int = 15, noisy_threshold: int = 1000) -> dict:
    counts = top_level_file_counts(root)
    tracked = git_ls_files(root)

    tracked_node_modules = [p for p in tracked if "/node_modules/" in p]
    tracked_venv = [p for p in tracked if p.startswith(".venv/") or "/.venv/" in p]
    tracked_backups = [p for p in tracked if p.startswith("backups_reorg/")]

    large_dirs = [(name, cnt) for name, cnt in counts.most_common() if cnt >= noisy_threshold]
    top_density = [{"directory": name, "file_count": cnt} for name, cnt in counts.most_common(top_n)]

    risk_score = 0
    risk_score += min(40, len(tracked_node_modules) // 5000)
    risk_score += min(30, len(tracked_venv) // 1000)
    risk_score += min(30, len(tracked_backups) // 2000)
    risk_score = min(100, risk_score)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_level_directories_scanned": len(counts),
        "tracked_file_count": len(tracked),
        "tracked_node_modules_files": len(tracked_node_modules),
        "tracked_venv_files": len(tracked_venv),
        "tracked_backups_reorg_files": len(tracked_backups),
        "top_level_file_density": top_density,
        "high_volume_directories": [{"directory": n, "file_count": c} for n, c in large_dirs],
        "risk_score_0_to_100": risk_score,
        "noisy_threshold": noisy_threshold,
        "recommended_actions": [
            "Untrack dependency/vendor trees gradually (start with node_modules and .venv) in controlled PRs.",
            "Move long-term backups to external object storage and keep curated snapshots only.",
            "Add CI checks for Python tests and selected app checks on each PR.",
            "Continue modular docs under docs/ and keep README focused on onboarding.",
        ],
    }


def generate_markdown_report(metrics: dict) -> str:
    lines: list[str] = []
    lines.append("# codex-web Repository Health Report")
    lines.append("")
    lines.append(f"Generated: {metrics['generated_at']}")
    lines.append("")

    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Structural risk score: **{metrics['risk_score_0_to_100']}/100**")
    lines.append(f"- Tracked files: **{metrics['tracked_file_count']}**")
    lines.append(f"- Tracked `node_modules` files: **{metrics['tracked_node_modules_files']}**")
    lines.append(f"- Tracked `.venv` files: **{metrics['tracked_venv_files']}**")
    lines.append(f"- Tracked `backups_reorg` files: **{metrics['tracked_backups_reorg_files']}**")
    lines.append("")

    lines.append("## Top-level file density")
    lines.append("")
    lines.append("| Directory | File count |")
    lines.append("|---|---:|")
    for row in metrics["top_level_file_density"]:
        lines.append(f"| `{row['directory']}` | {row['file_count']} |")
    lines.append("")

    lines.append("## Risk flags")
    lines.append("")
    hv = metrics["high_volume_directories"]
    if not hv and metrics["tracked_node_modules_files"] == 0 and metrics["tracked_venv_files"] == 0:
        lines.append("- No high-risk structural flags detected with current thresholds.")
    else:
        for row in hv:
            lines.append(
                f"- High file volume in `{row['directory']}`: {row['file_count']} files "
                f"(threshold: {metrics['noisy_threshold']})."
            )
        if metrics["tracked_node_modules_files"]:
            lines.append("- Tracked `node_modules` content detected. This creates noisy diffs and large commits.")
        if metrics["tracked_venv_files"]:
            lines.append("- Tracked `.venv` content detected. Virtual environments should usually be untracked.")
        if metrics["tracked_backups_reorg_files"]:
            lines.append("- Tracked `backups_reorg` content detected. Prefer external long-term backup storage.")
    lines.append("")

    lines.append("## Recommended next actions")
    lines.append("")
    for i, action in enumerate(metrics["recommended_actions"], start=1):
        lines.append(f"{i}. {action}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate codex-web repository health report")
    parser.add_argument("--output", default="docs/reports/repo_health_report.md", help="Output markdown path")
    parser.add_argument(
        "--json-output",
        default="docs/reports/repo_health_report.json",
        help="Output JSON path",
    )
    parser.add_argument("--top", type=int, default=15, help="Top directory count rows")
    parser.add_argument("--threshold", type=int, default=1000, help="Noisy directory threshold")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    metrics = compute_metrics(root=root, top_n=args.top, noisy_threshold=args.threshold)

    md = generate_markdown_report(metrics)
    out_md = root / args.output
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md + "\n", encoding="utf-8")

    out_json = root / args.json_output
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote markdown report: {out_md}")
    print(f"Wrote JSON report: {out_json}")


if __name__ == "__main__":
    main()
