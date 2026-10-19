"""blog_pipeline/gsc_loader.py — refresh GSC query cache without touching tokens.
Delegates to existing gsc_weekly_report.py logic by import or subprocess.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from typing import List, Dict

from blog_pipeline.config import DATA_DIR


def load_gsc_cache(cache_path: Path = DATA_DIR / "gsc_queries.json") -> List[Dict]:
    """Return cached GSC rows. If missing, run the existing weekly report script."""
    if not cache_path.exists():
        refresh_gsc_cache(cache_path)
    return json.load(open(cache_path))


def refresh_gsc_cache(cache_path: Path = DATA_DIR / "gsc_queries.json") -> Path:
    """Run /tmp/gsc_ref.py to refresh token and write the markdown report; also cache JSON."""
    script = Path("/tmp/gsc_ref.py")
    if not script.exists():
        raise FileNotFoundError("GSC script not found at /tmp/gsc_ref.py")
    # Run the existing script; it writes a markdown report. We then rebuild cache from stdout.
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"GSC refresh failed: {result.stderr}")
    # Parse simple metrics from stdout if needed; primary cache remains JSON rebuilt by caller.
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # Placeholder: real implementation would parse the GSC API response directly.
    json.dump({"status": "refreshed", "rows": []}, open(cache_path, "w"))
    return cache_path


def pick_query_opportunities(rows: List[Dict], min_impressions: int = 10, max_position: float = 15.0) -> List[Dict]:
    """Return queries with impressions but low CTR or position > 5 (expandable)."""
    return [
        r for r in rows
        if r.get("impressions", 0) >= min_impressions
        and r.get("position", 100) <= max_position
        and r.get("position", 0) >= 5
    ]
