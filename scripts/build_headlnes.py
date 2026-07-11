#!/usr/bin/env python3
"""Builds headlines.json from the RSS feeds listed in outlets.json.
Runs on a schedule in GitHub Actions; tolerant of any single feed failing."""
import json, datetime
import feedparser

MAX_PER_FEED = 3
MAX_TOTAL = 40

def main():
    with open("outlets.json") as f:
        data = json.load(f)
    items = []
    for o in data["outlets"]:
        feed_url = o.get("rss")
        if not feed_url:
            continue
        try:
            feed = feedparser.parse(feed_url)
            for e in feed.entries[:MAX_PER_FEED]:
                items.append({
                    "outlet": o["name"],
                    "title": e.get("title", "").strip(),
                    "link": e.get("link", ""),
                    "published": e.get("published", e.get("updated", "")),
                })
            print(f"  OK   {o['name']}: {min(len(feed.entries), MAX_PER_FEED)} items")
        except Exception as ex:
            print(f"  SKIP {o['name']}: {type(ex).__name__}")
    # newest-ish first: feedparser dates vary, so just interleave by outlet order
    out = {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "count": min(len(items), MAX_TOTAL),
        "headlines": items[:MAX_TOTAL],
    }
    with open("headlines.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"\nWrote headlines.json with {out['count']} headlines")

if __name__ == "__main__":
    main()
