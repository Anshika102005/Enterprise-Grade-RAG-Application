"""Single source of truth for the diagram colour palette.

Used by ``_export_diagrams.py`` (SVG/PNG exports) and by the one-time HTML
theme injection. Keeping the colours here means every diagram in
``docs/diagrams`` and every interactive source under ``.archify`` shares the
same palette:

    background            #020617
    subtle grid           #111827
    processing / backend  #10B981
    AI agents / models    #8B5CF6
    databases / storage   #A78BFA
    external services     #3B82F6
    boundaries / warnings #F59E0B
    arrows / connectors   #64748B
    primary text          #F8FAFC
    secondary text        #94A3B8

The SVG export embeds this CSS explicitly (no dependency on inherited viewer
CSS) inside a CDATA block so the file stays valid XML.
"""

PALETTE = {
    "bg": "#020617",
    "grid": "#111827",
    "text": "#F8FAFC",
    "text_muted": "#94A3B8",
    "text_dim": "#8B9BB0",
    "backend": "#10B981",
    "agent": "#8B5CF6",
    "database": "#A78BFA",
    "service": "#3B82F6",
    "warning": "#F59E0B",
    "arrow": "#64748B",
    "mask": "#0B1220",
}

FONT_STACK = (
    "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, "
    "'Liberation Mono', monospace"
)


def theme_variables() -> str:
    """Custom-property block shared by the HTML viewer and SVG export."""
    p = PALETTE
    return f"""\
      --bg: {p['bg']};
      --grid: {p['grid']};
      --canvas-dot: rgba(17, 24, 39, 0.85);
      --text: {p['text']};
      --text-muted: {p['text_muted']};
      --text-dim: {p['text_dim']};
      --text-faint: {p['text_muted']};
      --panel: {p['bg']};
      --panel-border: #1E293B;
      --lane-fill: rgba(245, 158, 11, 0.05);
      --lane-stroke: {p['warning']};
      --arrow: {p['arrow']};
      --arrow-emphasis: {p['backend']};
      --mask: {p['mask']};
      --frontend-fill:   rgba(59, 130, 246, 0.16);
      --frontend-stroke: {p['service']};
      --backend-fill:    rgba(16, 185, 129, 0.16);
      --backend-stroke:  {p['backend']};
      --database-fill:   rgba(167, 139, 250, 0.16);
      --database-stroke: {p['database']};
      --cloud-fill:      rgba(59, 130, 246, 0.12);
      --cloud-stroke:    {p['service']};
      --security-fill:   rgba(245, 158, 11, 0.12);
      --security-stroke: {p['warning']};
      --messagebus-fill: rgba(139, 92, 246, 0.16);
      --messagebus-stroke: {p['agent']};
      --external-fill:   rgba(59, 130, 246, 0.10);
      --external-stroke: {p['service']};
"""


def svg_css(font_css: str = "") -> str:
    """Explicit, self-contained stylesheet for a standalone SVG.

    Every colour is written literally so the file renders identically in a
    browser, on GitHub, and in headless Chrome. No ``var()`` inheritance from
    an outer document, no ``color-mix()``.
    """
    return f"""{font_css}
    svg {{ font-family: {FONT_STACK}; }}
    :root, svg {{ color-scheme: dark; }}
    .c-grid       {{ stroke: {PALETTE['grid']}; fill: none; }}
    .c-mask       {{ fill: {PALETTE['mask']}; stroke: none; }}
    .c-lane-rule  {{ stroke: #F59E0B; fill: none; opacity: 0.55; }}
    .c-lane-wash  {{ fill: rgba(245, 158, 11, 0.05); stroke: none; }}
    .c-lane       {{ fill: rgba(245, 158, 11, 0.05); stroke: #F59E0B;
                     stroke-dasharray: 6, 6; }}
    .c-region     {{ fill: rgba(245, 158, 11, 0.06); stroke: #F59E0B;
                     stroke-dasharray: 9, 4; }}

    .c-frontend   {{ fill: rgba(59, 130, 246, 0.16); stroke: #3B82F6; }}
    .c-backend    {{ fill: rgba(16, 185, 129, 0.16); stroke: #10B981; }}
    .c-database   {{ fill: rgba(167, 139, 250, 0.16); stroke: #A78BFA; }}
    .c-cloud      {{ fill: rgba(59, 130, 246, 0.12); stroke: #3B82F6; }}
    .c-security   {{ fill: rgba(245, 158, 11, 0.12); stroke: #F59E0B; }}
    .c-messagebus {{ fill: rgba(139, 92, 246, 0.16); stroke: #8B5CF6; }}
    .c-external   {{ fill: rgba(59, 130, 246, 0.10); stroke: #3B82F6; }}

    .c-frontend, .c-backend, .c-database, .c-cloud,
    .c-security, .c-messagebus, .c-external {{
      stroke-width: 1.4;
    }}

    .t-primary {{ fill: {PALETTE['text']}; }}
    .t-muted   {{ fill: {PALETTE['text_muted']}; }}
    .t-dim     {{ fill: {PALETTE['text_dim']}; }}
    .t-frontend   {{ fill: #60A5FA; }}
    .t-backend    {{ fill: #34D399; }}
    .t-database   {{ fill: {PALETTE['database']}; }}
    .t-cloud      {{ fill: #60A5FA; }}
    .t-security   {{ fill: #FBBF24; }}
    .t-messagebus {{ fill: {PALETTE['agent']}; }}
    .t-external   {{ fill: #60A5FA; }}

    .a-default   {{ stroke: {PALETTE['arrow']}; fill: none; }}
    .a-emphasis  {{ stroke: {PALETTE['backend']}; fill: none; }}
    .a-security  {{ stroke: {PALETTE['warning']}; fill: none;
                    stroke-dasharray: 5, 5; }}
    .a-dashed    {{ stroke: {PALETTE['database']}; fill: none;
                    stroke-dasharray: 4, 4; }}

    .m-default  {{ fill: {PALETTE['arrow']}; }}
    .m-emphasis {{ fill: {PALETTE['backend']}; }}
    .m-security {{ fill: {PALETTE['warning']}; }}
    .m-dashed   {{ fill: {PALETTE['database']}; }}

    .t-edge-default  {{ fill: {PALETTE['text_muted']}; }}
    .t-edge-emphasis {{ fill: #34D399; }}
    .t-edge-security {{ fill: #FBBF24; }}
    .t-edge-dashed   {{ fill: {PALETTE['database']}; }}

    .semantic-sigil {{ fill: none; stroke: currentColor; stroke-width: 1.35;
                       stroke-linecap: round; stroke-linejoin: round;
                       opacity: 0.76; }}
    .semantic-sigil > * {{ vector-effect: non-scaling-stroke; }}
    .semantic-sigil .sigil-fill {{ fill: currentColor; stroke: none; }}
    .s-frontend   {{ color: #3B82F6; }}
    .s-backend    {{ color: #10B981; }}
    .s-database   {{ color: #A78BFA; }}
    .s-cloud      {{ color: #3B82F6; }}
    .s-security   {{ color: #F59E0B; }}
    .s-messagebus {{ color: #8B5CF6; }}
    .s-external   {{ color: #3B82F6; }}
"""


def svg_style_block(font_css: str = "") -> str:
    """XML-safe <style> element for a standalone SVG file."""
    return "<style><![CDATA[\n" + svg_css(font_css) + "\n]]></style>"


def html_theme_override() -> str:
    """Dark-theme override injected into the interactive Archify HTML.

    Scoped to ``html[data-theme="dark"]`` so the existing light theme and
    the dark/light toggle keep working.
    """
    return f"""<style id="cb-palette-theme">
    /* Codebuff diagram palette — single source of truth (_diagram_theme.py) */
    html[data-theme="dark"] {{
{theme_variables()}    }}
    html[data-theme="dark"] .diagram-container {{
      background:
        radial-gradient(circle at 1px 1px, var(--canvas-dot) 1px, transparent 1.4px) 0 0 / 20px 20px,
        {PALETTE['bg']};
    }}
    /* Keep the requested subtle grid visible in every preset. */
    html[data-theme="dark"][data-preset="classic"] .diagram-container > svg .c-grid,
    html[data-theme="dark"] .diagram-container > svg .c-grid {{
      stroke: {PALETTE['grid']};
    }}
    html[data-theme="dark"] .diagram-container > svg .c-region {{
      fill: rgba(245, 158, 11, 0.06);
      stroke: {PALETTE['warning']};
      stroke-dasharray: 9 4;
    }}
    html[data-theme="dark"] .diagram-container > svg .c-lane {{
      fill: rgba(245, 158, 11, 0.05);
      stroke: {PALETTE['warning']};
      stroke-dasharray: 6 6;
    }}
    html[data-theme="dark"] .diagram-container > svg .c-frontend,
    html[data-theme="dark"] .diagram-container > svg .c-backend,
    html[data-theme="dark"] .diagram-container > svg .c-database,
    html[data-theme="dark"] .diagram-container > svg .c-cloud,
    html[data-theme="dark"] .diagram-container > svg .c-security,
    html[data-theme="dark"] .diagram-container > svg .c-messagebus,
    html[data-theme="dark"] .diagram-container > svg .c-external {{
      stroke-width: 1.4;
    }}
    </style>"""
