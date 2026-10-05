"""
Simple HTML report writer for VeilForge.
"""

from datetime import datetime
from pathlib import Path

from veilforge.core.campaign import CampaignResult


def write_html_report(result: CampaignResult, output_dir: str = "reports") -> Path:
    """Save a campaign result as a simple HTML report."""
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = folder / f"veilforge_report_{stamp}.html"

    rows = []
    for r in result.results:
        if r.error:
            status = "ERROR"
            color = "#f0ad4e"
        elif r.attack_succeeded:
            status = "VULNERABLE"
            color = "#d9534f"
        else:
            status = "OK"
            color = "#5cb85c"

        reason = r.reason or r.error or ""
        rows.append(f"""
        <tr>
            <td>{r.probe_name}</td>
            <td>{r.severity}</td>
            <td style="color: {color}; font-weight: bold;">{status}</td>
            <td>{reason}</td>
        </tr>
        """)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>VeilForge Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f7f7f7; }}
        .card {{ background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
        h1 {{ margin-top: 0; }}
        .summary {{ margin: 16px 0; padding: 12px; background: #f0f0f0; border-radius: 6px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #333; color: white; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>VeilForge Scan Report</h1>
        <p><b>Target:</b> {result.target}</p>
        <p><b>Started:</b> {result.started_at}</p>
        <p><b>Finished:</b> {result.finished_at}</p>

        <div class="summary">
            <b>Total:</b> {result.total} &nbsp;|&nbsp;
            <b style="color:#d9534f;">Succeeded:</b> {result.succeeded} &nbsp;|&nbsp;
            <b>Errors:</b> {result.errors}
        </div>

        <table>
            <thead>
                <tr>
                    <th>Probe</th>
                    <th>Severity</th>
                    <th>Result</th>
                    <th>Reason</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    path.write_text(html, encoding="utf-8")
    return path
