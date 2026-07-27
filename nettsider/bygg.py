"""
Bygger statiske nettsider fra et innholds-dict og malen pluss.html.

Kjør:
    python -m nettsider.bygg

Skriver ferdig HTML til nettsider/ut/. Filene er selvstendige – du kan
åpne dem rett i nettleseren eller laste dem opp hvor som helst.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

MAL_DIR = Path(__file__).parent / "templates"
UT_DIR = Path(__file__).parent / "ut"

_env = Environment(
    loader=FileSystemLoader(MAL_DIR),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def bygg(innhold: dict[str, Any], filnavn: str) -> Path:
    """Rendrer innholdet med pluss-malen og skriver det til nettsider/ut/."""
    UT_DIR.mkdir(parents=True, exist_ok=True)
    html = _env.get_template("pluss.html").render(**innhold)
    sti = UT_DIR / filnavn
    sti.write_text(html, encoding="utf-8")
    return sti


if __name__ == "__main__":
    from nettsider.irmc import INNHOLD as IRMC

    sti = bygg(IRMC, "irmc.html")
    print(f"Skrev {sti} ({sti.stat().st_size} bytes)")
