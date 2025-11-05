import json, importlib.util, os, datetime, numpy as np

root = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
kernel_path = os.path.join(root, "codex", "core", "laws.py")
spec = importlib.util.spec_from_file_location("laws", kernel_path)
laws = importlib.util.module_from_spec(spec)
spec.loader.exec_module(laws)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_path = os.path.join(root, "codex", "logs", f"kernel_validation_{timestamp}.json")

# === Placeholder model ===
results = {}
try:
    fields = [getattr(laws, name) for name in dir(laws) if callable(getattr(laws, name)) and not name.startswith("__")]
    results["num_laws_detected"] = len(fields)
    energies = []
    for f in fields:
        try:
            val = f(1.0) if callable(f) else None
            if isinstance(val, (int, float)):
                energies.append(val)
        except Exception:
            continue
    mean_energy = float(np.mean(energies)) if energies else 0.0
    deviation = float(np.std(energies)) if energies else 0.0
    results.update({
        "mean_energy": mean_energy,
        "std_dev": deviation,
        "stability_ratio": 0.0 if mean_energy == 0 else abs(deviation/mean_energy),
        "status": "stable" if deviation < abs(mean_energy)*0.1 else "unstable"
    })
except Exception as e:
    results = {"error": str(e)}

with open(log_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"✅ Kernel validation log written to: {log_path}")
