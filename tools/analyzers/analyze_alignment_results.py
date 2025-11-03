# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
import json, os, statistics, math
from datetime import datetime

SUMMARY_FILE = os.path.join(os.getcwd(), 'codex_alignment_summary.json')

def load_summary(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze(data):
    total = len(data)
    passed = sum(1 for d in data if d.get('ok'))
    avg_G = statistics.mean(d.get('G', 0) for d in data if 'G' in d)
    high_align = [d for d in data if d.get('G', 0) >= 0.8]
    low_align = [d for d in data if d.get('G', 0) < 0.5]

    print("===========================================================")
    print("🧩 Codex Alignment Analysis —", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("-----------------------------------------------------------")
    print(f"Files audited: {total}")
    print(f"Passed alignment threshold: {passed} ({(passed/total)*100:.2f}%)")
    print(f"Average coherence (G): {avg_G:.3f}")
    print(f"High-alignment cluster (>0.8): {len(high_align)} files")
    print(f"Low-alignment cluster (<0.5): {len(low_align)} files")
    print("-----------------------------------------------------------")

    # Triadic dispersion metric
    G_values = [d['G'] for d in data if 'G' in d]
    triadic_dispersion = statistics.stdev(G_values) if len(G_values) > 1 else 0
    print(f"Triadic dispersion σ(G): {triadic_dispersion:.3f}")
    print("===========================================================")

    # Output a ranked coherence table
    ranked = sorted(data, key=lambda d: d.get('G', 0), reverse=True)
    print("\nTop 10 Most Coherent Files:")
    for r in ranked[:10]:
        print(f" - {r['file']} | G={r['G']:.3f}")

    with open('codex_alignment_insights.json', 'w', encoding='utf-8') as out:
        json.dump({
            'timestamp': datetime.now().timestamp(),
            'stats': {
                'total': total,
                'passed': passed,
                'avg_G': avg_G,
                'triadic_dispersion': triadic_dispersion
            },
            'high_align_files': [r['file'] for r in high_align],
            'low_align_files': [r['file'] for r in low_align],
        }, out, indent=4)

    print("\n✅ Insights saved to codex_alignment_insights.json")

if __name__ == '__main__':
    if os.path.exists(SUMMARY_FILE):
        data = load_summary(SUMMARY_FILE)
        analyze(data)
    else:
        print("⚠️ codex_alignment_summary.json not found.")

