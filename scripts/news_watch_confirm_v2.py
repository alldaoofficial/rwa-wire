#!/usr/bin/env python3
"""Run source confirmation with the same curated classifier as the scanner."""
import news_watch as nw
import news_watch_v2 as catalog
import news_watch_confirm as confirm

# news_watch_v2 patches news_watch on import; assign explicitly for clarity and to
# keep scanner/confirmation classification identical if import behavior changes.
nw.normalize_source = catalog.normalize_source
nw.source_tier = catalog.source_tier

if __name__ == "__main__":
    confirm.main()
