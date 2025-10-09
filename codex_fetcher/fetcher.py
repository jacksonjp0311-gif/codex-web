# codex_fetcher/fetcher.py

import json
import yaml
import requests
import feedparser
from pathlib import Path

CONFIG_PATH = Path("mirrors.yml")
INBOX_DIR   = Path("inbox")
STATE_FILE  = Path(".fetcher_state.json")

def load_state():
    if STATE_FILE.exists():
        text = STATE_FILE.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else {}
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def fetch_github(repo, path, seen_files):
    """
    repo: "org/repo"
    path: subfolder in that repo
    seen_files: list of filenames already fetched
    """
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    resp = requests.get(url)
    resp.raise_for_status()
    items = resp.json()
    new_files = []

    for item in items:
        if item.get("type") != "file":
            continue
        name = item["name"]
        if name in seen_files:
            continue
        raw = requests.get(item["download_url"]).text
        file_path = INBOX_DIR / name
        file_path.write_text(raw, encoding="utf-8")
        new_files.append(name)

    return new_files

def fetch_rss(mirror_name, feed_url, seen_ids):
    """
    mirror_name: used to prefix filenames
    feed_url: RSS/Atom feed URL
    seen_ids: list of entry.id values already fetched
    """
    feed = feedparser.parse(feed_url)
    new_ids = []

    for entry in feed.entries:
        eid = entry.id
        if eid in seen_ids:
            continue
        # assume the full canonical JSON is in entry.content[0].value
        content = entry.content[0].value
        filename = f"{mirror_name}_{eid}.json"
        (INBOX_DIR / filename).write_text(content, encoding="utf-8")
        new_ids.append(eid)

    return new_ids

def main():
    INBOX_DIR.mkdir(exist_ok=True)
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    state = load_state()

    for mirror in cfg.get("mirrors", []):
        name = mirror["name"]
        mtype = mirror["type"]
        seen = state.get(name, [])

        if mtype == "github":
            repo = mirror["repo"]
            path = mirror["path"]
            added = fetch_github(repo, path, seen)
        elif mtype == "rss":
            added = fetch_rss(name, mirror["url"], seen)
        else:
            print(f"⚠️  Unknown mirror type: {mtype}")
            continue

        # update state only if there are new items
        if added:
            state[name] = seen + added

    save_state(state)
    print("Fetched mirrors. New stones per mirror:", {k: len(v) for k, v in state.items()})

if __name__ == "__main__":
    main()
