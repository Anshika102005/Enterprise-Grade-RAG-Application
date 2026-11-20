"""Re-export the delivered diagrams: inline SVG -> docs/diagrams/*.svg, plus a 2x PNG preview."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "diagrams"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

CHARTS = {
    "architecture-rag-system-20261028-021934/advanced-rag.architecture.html": "architecture",
    "workflow-self-rag-loop-20261028-022233/self-rag-loop.workflow.html": "self-rag-loop",
    "sequence-request-lifecycle-20261028-022800/request-lifecycle.sequence.html": "request-lifecycle",
    "dataflow-ingestion-pipeline-20261028-023107/ingestion-pipeline.dataflow.html": "ingestion-pipeline",
}

OUT.mkdir(parents=True, exist_ok=True)
CHROME_FLAGS = [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--force-device-scale-factor=2",
    "--default-background-color=00000000",
]

for html_rel, name in CHARTS.items():
    html = (ROOT / ".archify" / html_rel).read_text(encoding="utf-8")
    start = html.index("<svg ")
    svg = html[start : html.index("</svg>", start) + len("</svg>")]

    viewbox = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    w, h = (int(float(v)) for v in viewbox.groups())
    if ' width="' not in svg.split(">", 1)[0]:
        svg = svg.replace("<svg ", f'<svg width="{w}" height="{h}" ', 1)

    # Add xmlns so the standalone SVG is a valid SVG document and CSS
    # custom properties (var(--text), var(--backend-fill), etc.) resolve
    # correctly in browsers, GitHub, and headless Chrome.
    svg_tag_start = svg.split(">", 1)[0]
    if 'xmlns=' not in svg_tag_start:
        svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    if 'data-theme=' not in svg_tag_start:
        svg = svg.replace("<svg ", '<svg data-theme="dark" ', 1)

    # The SVG paints through the viewer's stylesheet (theme variables, semantic
    # classes, bundled font), so a standalone copy needs that CSS inlined.
    styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    if "<style" not in svg:
        svg = svg.replace(">", f"><style>{styles}</style>", 1)

    # Opaque canvas so the dark-theme art stays legible on light hosts (README, GitHub).
    if 'fill="#020617"' not in svg:
        svg = svg.replace(">", f'><rect x="0" y="0" width="{w}" height="{h}" fill="#020617"/>', 1)

    svg_path = OUT / f"{name}.svg"
    svg_path.write_text(svg + "\n", encoding="utf-8")

    # Render the PNG from the standalone SVG at 2x, on an opaque dark canvas.
    wrapper = ROOT / ".archify" / f"_pngwrap-{name}.html"
    wrapper.write_text(
        "<!doctype html><html data-theme=\"dark\"><meta charset=utf-8>"
        "<style>html,body{margin:0;padding:0;background:#020617}"
        f"svg{{width:{w * 2}px;height:{h * 2}px}}</style>" + svg,
        encoding="utf-8",
    )
    (OUT / wrapper.name).write_bytes(wrapper.read_bytes())
    png = OUT / f"{name}.png"
    subprocess.run(
        [
            str(CHROME),
            *CHROME_FLAGS,
            f"--window-size={w * 2},{h * 2}",
            "--virtual-time-budget=3000",
            f"--screenshot={png}",
            (OUT / wrapper.name).as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    (OUT / wrapper.name).unlink()
    print(f"{name}: svg {w}x{h} ({svg_path.stat().st_size} B), png {png.stat().st_size} B")

sys.exit(0)
