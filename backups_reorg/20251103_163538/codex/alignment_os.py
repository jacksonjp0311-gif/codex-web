# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
# codex/alignment_os.py
# Alignment OS bootstrapper for Codex Fractal Seal (v0.1)
# Usage: python -m codex.alignment_os   OR   python codex/alignment_os.py

import os, json, argparse
from codex.core.alignment_helper import run_audit_on_repo

def main(root_dir='.', out_path=None, limit=None):
    root = os.path.abspath(root_dir)
    print('Codex Alignment OS scanning root:', root)
    results = run_audit_on_repo(root, limit=limit)
    # write results summary
    if out_path is None:
        out_path = os.path.join(root, 'codex_alignment_summary.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    good = sum(1 for r in results if r.get('ok'))
    total = len(results)
    print(f'Finished audit: {good}/{total} files passed. Summary ->', out_path)
    return 0 if good==total else 2

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Codex Alignment OS bootstrapper')
    ap.add_argument('--root', '-r', default='.', help='Repo root to scan')
    ap.add_argument('--out', help='Output summary path')
    ap.add_argument('--limit', type=int, help='Limit number of files to scan')
    args = ap.parse_args()
    rc = main(root_dir=args.root, out_path=args.out, limit=args.limit)
    exit(rc)

