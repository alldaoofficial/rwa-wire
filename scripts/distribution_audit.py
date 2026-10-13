#!/usr/bin/env python3
"""Read-only distribution status. Never approve, send or retry a post."""
import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def audit(root=ROOT):
    config_path = root / "publish/channel-config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    rows = []
    for path in sorted((root / "publish/candidates").glob("*.json"), reverse=True):
        try:
            d = json.loads(path.read_text()); pid = d.get("id", path.stem)
            if not isinstance(pid, str) or not pid or pathlib.Path(pid).name != pid:
                continue
            rejected = (root / "publish/rejected" / (pid + ".json")).exists()
            approved = (root / "publish/approved" / (pid + ".json")).exists()
            posted = (root / "publish/posted" / (pid + ".json")).exists()
            x_posted = (root / "publish/x-posted" / (pid + ".json")).exists()
            status = "rejected" if rejected else "telegram-posted" if posted else "approved-awaiting-telegram" if approved else "awaiting-editorial-approval"
            x = "posted" if x_posted else "paused" if config.get("x_enabled") is False else "awaiting-distribution" if not posted else "awaiting-x"
            rows.append({"id": pid, "title": d.get("title", ""), "article_url": d.get("article_url", ""), "status": status, "x": x})
        except (ValueError, TypeError, KeyError):
            continue
    return {"x_enabled": config.get("x_enabled") is not False, "candidates": rows}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--summary", action="store_true"); args = p.parse_args()
    d = audit()
    if not args.summary:
        print(json.dumps(d, indent=2, ensure_ascii=False)); return
    print("## RWA Wire distribution status\n")
    pending = [r for r in d["candidates"] if r["status"] not in {"rejected", "telegram-posted"}]
    print(f"{len(pending)} candidates await editorial approval or Telegram publication.\n")
    if not d["x_enabled"]:
        print("X API publishing is paused by the existing channel configuration. Prepared copy is not a published post. No paid API calls are made by this audit.\n")
    for row in pending[:10]:
        title = str(row["title"]).replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")
        print(f"- {title}: `{row['status']}`; X: `{row['x']}`")


if __name__ == "__main__":
    main()
