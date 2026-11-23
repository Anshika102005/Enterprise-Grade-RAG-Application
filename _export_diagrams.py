"""Re-export the delivered diagrams: inline SVG -> docs/diagrams/*.svg, plus a 2x PNG.

The SVG is rebuilt as a self-contained, XML-valid document:

* colours come from ``_diagram_theme.py`` as explicit literals, so nothing
  depends on the viewer's stylesheet being inherited by the image;
* the stylesheet is wrapped in ``<![CDATA[ ... ]]>`` because CSS comments are
  not XML-safe (an unescaped ``&`` made the previous exports unparseable and
  browsers dropped the whole stylesheet — the black-on-black symptom);
* a font-only stylesheet is kept for faithful typography;
* an opaque background rect guarantees the dark canvas on light hosts.

The interactive Archify HTML sources are also given the same palette override
(``id="cb-palette-theme"``) so the dark theme matches the exported assets.
"""

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from _diagram_theme import PALETTE, html_theme_override, svg_style_block

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
    f"--default-background-color={PALETTE['bg'].lstrip('#')}",
]


def apply_html_theme(html: str) -> str:
    """Inject (or refresh) the palette override in the interactive HTML."""
    block = html_theme_override()
    pattern = re.compile(r'<style id="cb-palette-theme">.*?</style>', re.S)
    if pattern.search(html):
        return pattern.sub(lambda _: block, html, count=1)
    return html.replace("</head>", block + "\n</head>", 1)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def extract_font_css(html: str) -> str:
    """Return only the bundled @font-face rules (the HTML head carries them)."""
    for block in re.findall(r"<style[^>]*>(.*?)</style>", html, re.S):
        i = block.find("@font-face")
        if i >= 0:
            return block[i:]
    return ""


def build_svg(html: str) -> str:
    start = html.index("<svg ")
    svg = html[start : html.index("</svg>", start) + len("</svg>")].strip()

    viewbox = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if not viewbox:
        raise ValueError("diagram has no viewBox")
    w, h = (int(float(v)) for v in viewbox.groups())

    open_tag = svg.split(">", 1)[0]
    if ' width="' not in open_tag:
        svg = svg.replace("<svg ", f'<svg width="{w}" height="{h}" ', 1)
    if 'xmlns=' not in open_tag:
        svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    if 'data-theme=' not in open_tag:
        svg = svg.replace("<svg ", '<svg data-theme="dark" ', 1)

    # Drop every inherited viewer stylesheet; keep only the bundled font faces.
    font_css = extract_font_css(html)
    svg = re.sub(r"<style[^>]*>.*?</style>", "", svg, flags=re.S)

    # The geometry may reference the mask token from presentation attributes;
    # resolve it to the literal colour so nothing depends on CSS inheritance.
    svg = svg.replace("var(--mask)", PALETTE["mask"])

    # Explicit, XML-valid stylesheet + opaque canvas.
    style = svg_style_block(font_css)
    background = (
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{PALETTE["bg"]}"/>'
    )
    svg = svg.replace(">", ">" + style + background, 1)

    return svg


def main() -> int:
    for html_rel, name in CHARTS.items():
        html_path = ROOT / ".archify" / html_rel
        html = html_path.read_text(encoding="utf-8")

        themed = apply_html_theme(html)
        if themed != html:
            html_path.write_text(themed, encoding="utf-8")
            html = themed

        svg = build_svg(html)
        try:
            ET.fromstring(svg)
        except ET.ParseError as exc:
            print(f"{name}: INVALID SVG XML — {exc}", file=sys.stderr)
            return 1

        viewbox = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
        w, h = (int(float(v)) for v in viewbox.groups())

        svg_path = OUT / f"{name}.svg"
        svg_path.write_text(svg + "\n", encoding="utf-8")

        png = OUT / f"{name}.png"
        subprocess.run(
            [
                str(CHROME),
                *CHROME_FLAGS,
                "--force-device-scale-factor=2",
                f"--window-size={w},{h}",
                "--virtual-time-budget=3000",
                f"--screenshot={png}",
                svg_path.as_uri(),
            ],
            check=True,
            capture_output=True,
        )
        pw, ph = png_size(png)
        if (pw, ph) != (w * 2, h * 2):
            print(
                f"{name}: unexpected PNG size {pw}x{ph} (want {w * 2}x{h * 2})",
                file=sys.stderr,
            )
            return 1
        print(
            f"{name}: svg {w}x{h} ({svg_path.stat().st_size} B), "
            f"png {pw}x{ph} ({png.stat().st_size} B)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
