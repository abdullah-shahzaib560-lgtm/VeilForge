"""
JSON report writer for VeilForge.
"""

import json
from datetime import datetime
from pathlib import Path

from veilforge.core.campaign import CampaignResult


def write_json_report(result: CampaignResult, output_dir: str = "reports") -> Path:
    """Save a campaign result as JSON and return the file path."""
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = folder / f"veilforge_report_{stamp}.json"

    data = result.to_dict()
    data["tool"] = "VeilForge"
    data["report_version"] = "1.0"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path
