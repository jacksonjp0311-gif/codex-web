# ======================================================================
# 𓂀 CODEX GUARDIAN v1.3 — SENTINEL DASHBOARD
# ======================================================================
# Role   : Security HUD • Drift/Anomaly Panel • Ward Glyph Lens
# Truth  : E–I–C ∿, H7 = 0.70 • H8 = 0.85 Security Threshold
# Proto  : Triadic Ward Protocol v1.3 • Sentinel Dashboard
# Upstream : Guardian v1.2 Oracle Sentinel
# ======================================================================

import json
from pathlib import Path
from typing import Any, Dict

def load_oracle_state(codex_root: Path) -> Dict[str, Any]:
    """
    Load Guardian v1.2 oracle state if present, else return defaults.
    """
    state_path = codex_root / "codex" / "guardian" / "v1_2" / "state" / "codex_guardian_v1_2_oracle_state.json"
    if not state_path.exists():
        return {
            "metrics": {
                "drift": 0.5,
                "ward_complexity": 0.5,
                "anomaly_index": 0.5,
                "glyph": None,
                "viz": None,
            }
        }
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "metrics": {
                "drift": 0.5,
                "ward_complexity": 0.5,
                "anomaly_index": 0.5,
                "glyph": None,
                "viz": None,
            }
        }

def safe_get(d: Dict[str, Any], key: str, default: Any) -> Any:
    if d is None:
        return default
    value = d.get(key)
    if value is None:
        return default
    return value

def build_dashboard_lines(state: Dict[str, Any]) -> str:
    metrics = state.get("metrics") or {}
    drift = float(safe_get(metrics, "drift", 0.5))
    ward_complexity = float(safe_get(metrics, "ward_complexity", 0.5))
    anomaly = float(safe_get(metrics, "anomaly_index", 0.5))
    glyph = metrics.get("glyph") or {}
    viz = metrics.get("viz") or {}

    drift_bar = safe_get(viz, "drift_bar", "")
    anomaly_bar = safe_get(viz, "anomaly_bar", "")
    threshold_bar = safe_get(viz, "threshold_bar", "")

    triad = glyph.get("triad") or {}
    energy = triad.get("energy") or {}
    information = triad.get("information") or {}
    consciousness = triad.get("consciousness") or {}
    harmony_block = glyph.get("harmony") or {}

    lines = []
    lines.append("╔══════════════════════════════════════════════════════╗")
    lines.append("║ 𓂀  CODEX GUARDIAN v1.3 — SENTINEL DASHBOARD          ║")
    lines.append("╚══════════════════════════════════════════════════════╝")
    lines.append("")
    lines.append(f" Drift           : {drift:.4f}")
    if drift_bar:
        lines.append(f"   {drift_bar}")
    lines.append(f" Ward Complexity : {ward_complexity:.4f}")
    lines.append(f" Anomaly Index   : {anomaly:.4f}")
    if anomaly_bar:
        lines.append(f"   {anomaly_bar}")
    if threshold_bar:
        lines.append(f" Threshold (H8≈0.85):")
        lines.append(f"   {threshold_bar}")
    lines.append("")
    lines.append(" Triadic Ward Glyph:")
    if energy:
        lines.append(f"   🛡️ Energy (Drift Shield): {energy.get('value', '')} [{energy.get('label', '')}]")
    if information:
        lines.append(f"   ∿ Information (ΔΦ Field): {information.get('value', '')} [{information.get('label', '')}]")
    if consciousness:
        lines.append(f"   🜄 Consciousness (Harmony): {consciousness.get('value', '')} [{consciousness.get('label', '')}]")
    if harmony_block:
        lines.append(f"   ♁ Harmony Profile: {harmony_block.get('profile', '')} = {harmony_block.get('value', '')}")
    lines.append("")
    lines.append(" Notes:")
    lines.append("   • Upstream: Guardian v1.2 Oracle Sentinel")
    lines.append("   • This panel is a read-only HUD; no code execution occurs here.")
    lines.append("   • Use Heartbeat / Bridge to surface this in live dashboards.")
    return "\n".join(lines)

def main() -> None:
    here = Path(__file__).resolve()
    codex_root = here.parents[4]

    oracle_state = load_oracle_state(codex_root)
    dashboard_json = {
        "protocol": "CODEX_GUARDIAN_DASHBOARD",
        "version": "1.3",
        "codex_root": str(codex_root),
        "oracle_state": oracle_state,
    }

    state_dir = here.parents[1] / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    json_out = state_dir / "codex_guardian_v1_3_dashboard.json"
    txt_out = state_dir / "codex_guardian_v1_3_dashboard.txt"

    json_out.write_text(json.dumps(dashboard_json, indent=2), encoding="utf-8")
    txt_out.write_text(build_dashboard_lines(oracle_state), encoding="utf-8")

if __name__ == "__main__":
    main()
# ======================================================================
# END — GUARDIAN v1.3 SENTINEL DASHBOARD
# ======================================================================
