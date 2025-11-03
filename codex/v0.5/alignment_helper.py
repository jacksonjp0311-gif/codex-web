# codex/core/alignment_helper.py
# Helper utilities for the Codex Alignment OS bootstrapper.
import os, json, time
from codex.core.seal_protocol import SealController
from codex.core.gates import PhiGate, FreqGate, AlignmentGate

def discover_repo_files(root_dir):
    '''Return all text/code files to audit (py, js, html, md).'''
    exts = ('.py', '.js', '.html', '.md', '.json')
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # skip hidden/git folders
        if '.git' in dirpath.split(os.sep):
            continue
        for f in filenames:
            if f.lower().endswith(exts):
                files.append(os.path.join(dirpath, f))
    return files

def build_payload_for_file(file_path):
    '''Construct a payload dict for a single file (basic heuristics).'''
    try:
        txt = open(file_path, 'r', encoding='utf-8').read()
    except Exception:
        txt = ''
    # heuristics: try to estimate phi or freq if present in code comments
    phi = None
    freq = None
    # simple pattern search for numeric tokens that look like phi or frequency anchors
    if 'phi' in txt.lower():
        phi = 1.6180339887
    if '432' in txt or '7.83' in txt:
        freq = 7.83
    payload = {
        'human_text': 'codex intent',   # placeholder, can be replaced with richer metadata
        'ai_text': txt[:20000],         # truncated content for evaluation
        'phi_estimate': phi if phi is not None else 1.61,
        'freq_peak': freq if freq is not None else 7.75,
        'file_path': file_path
    }
    return payload

def make_default_gates(ref_vectors=None):
    '''Return a default gates list wired to your existing gate classes.'''
    gates = [
        PhiGate('phi_core', threshold=0.7, weight=2.0, critical=True),
        FreqGate('freq_shuaamun', threshold=0.65, weight=1.0, critical=False),
        AlignmentGate('align_code', ref_vectors=ref_vectors, threshold=0.72, weight=1.5, critical=True)
    ]
    return gates

def run_audit_on_file(file_path, ref_vectors=None):
    payload = build_payload_for_file(file_path)
    gates = make_default_gates(ref_vectors)
    ctrl = SealController(gates, global_threshold=0.7)
    ok, out = ctrl.sync_and_adjust(payload, max_cycles=4, cooldown=0.05)
    summary = {
        'file': file_path,
        'ok': bool(ok),
        'G': out.get('G') if isinstance(out, dict) else None,
        'results': out.get('results') if isinstance(out, dict) else None,
        'timestamp': time.time()
    }
    return summary

def run_audit_on_repo(root_dir, ref_vectors=None, limit=None):
    files = discover_repo_files(root_dir)
    if limit:
        files = files[:limit]
    results = []
    for f in files:
        print(f'-- auditing: {f}')
        r = run_audit_on_file(f, ref_vectors)
        results.append(r)
    return results
