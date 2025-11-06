import os, hashlib, json, time

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
scan_report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "modules": []}

def checksum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

for dirpath, _, files in os.walk(root):
    for f in files:
        if f.endswith((".py", ".ps1", ".json")) and "handoff" not in dirpath:
            p = os.path.join(dirpath, f)
            scan_report["modules"].append({"file": p, "hash": checksum(p)})

out = os.path.join(root, "jackson_os_kernel", "kernel_scan_report.json")
with open(out, "w") as f:
    json.dump(scan_report, f, indent=2)

print("🧩 Codex Kernel Scan Complete")
print(f"📁 Modules scanned: {len(scan_report['modules'])}")
print(f"📦 Report saved → {out}")
