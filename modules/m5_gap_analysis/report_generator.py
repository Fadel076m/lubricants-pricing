"""Report Generator — M5 Gap Analysis.

Génère un rapport HTML (et optionnellement PDF via WeasyPrint) du gap mensuel.
WeasyPrint est optionnel — si absent, seul l'HTML est produit.

Usage : pip install weasyprint
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

try:
    from weasyprint import HTML as WeasyHTML
    _WEASY_AVAILABLE = True
except ImportError:
    _WEASY_AVAILABLE = False
    logger.warning("WeasyPrint non installé — export PDF désactivé (HTML uniquement).")

from .gap_engine import STATUS_CRITIQUE, STATUS_DEFAV, STATUS_IN_TARGET, STATUS_FAVORABLE

_COLOR_MAP = {
    STATUS_CRITIQUE:  ("#C0392B", "#FDEDEC"),
    STATUS_DEFAV:     ("#E07B39", "#FEF9E7"),
    STATUS_IN_TARGET: ("#2980B9", "#EBF5FB"),
    STATUS_FAVORABLE: ("#27AE60", "#EAFAF1"),
}

_CSS = """
body { font-family: 'Arial', sans-serif; color: #2C3E50; margin: 40px; font-size: 13px; }
h1   { color: #1A6B9A; font-size: 22px; border-bottom: 3px solid #1A6B9A; padding-bottom: 6px; }
h2   { color: #2C3E50; font-size: 16px; margin-top: 28px; }
table{ border-collapse: collapse; width: 100%; margin-top: 10px; }
th   { background: #1A6B9A; color: white; padding: 8px 12px; text-align: left; font-size: 12px; }
td   { border: 1px solid #D5D8DC; padding: 7px 12px; font-size: 12px; }
tr:nth-child(even) { background: #F2F3F4; }
.badge { display:inline-block; padding:2px 10px; border-radius:12px; font-weight:bold; font-size:11px; }
.rec  { background:#EBF5FB; border-left:4px solid #2980B9; padding:8px 14px; margin:8px 0; }
.kpi  { display:inline-block; background:#F2F3F4; border-radius:8px; padding:12px 20px;
        margin:8px; text-align:center; min-width:130px; }
.kpi-val { font-size:22px; font-weight:bold; }
.kpi-lbl { font-size:11px; color:#7F8C8D; }
footer { margin-top:40px; color:#7F8C8D; font-size:10px; border-top:1px solid #D5D8DC; padding-top:8px; }
"""


def _badge(status: str) -> str:
    fg, bg = _COLOR_MAP.get(status, ("#7F8C8D", "#F2F3F4"))
    return f'<span class="badge" style="background:{bg};color:{fg}">{status}</span>'


def _gap_pct(val: float) -> str:
    if pd.isna(val):
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val * 100:.1f}%"


# ── Sections HTML ─────────────────────────────────────────────────────────────

def _section_executive_summary(gap_global: pd.DataFrame, alert_summary: dict) -> str:
    rows = ""
    for _, r in gap_global.iterrows():
        rows += (
            f"<tr><td>{r['target']}</td>"
            f"<td>{r['prevu']:,.2f}</td>"
            f"<td>{r['reel']:,.2f}</td>"
            f"<td>{r['gap_abs']:,.2f}</td>"
            f"<td>{_gap_pct(r['gap_rel'])}</td>"
            f"<td>{_badge(r['statut_gap'])}</td></tr>"
        )

    kpis = "".join([
        f'<div class="kpi"><div class="kpi-val" style="color:#C0392B">'
        f'{alert_summary.get("n_critique", 0)}</div>'
        f'<div class="kpi-lbl">CRITIQUE</div></div>',
        f'<div class="kpi"><div class="kpi-val" style="color:#E07B39">'
        f'{alert_summary.get("n_defavorable", 0)}</div>'
        f'<div class="kpi-lbl">DÉFAVORABLE</div></div>',
        f'<div class="kpi"><div class="kpi-val" style="color:#2980B9">'
        f'{alert_summary.get("n_dans_cible", 0)}</div>'
        f'<div class="kpi-lbl">DANS CIBLE</div></div>',
        f'<div class="kpi"><div class="kpi-val" style="color:#27AE60">'
        f'{alert_summary.get("n_favorable", 0)}</div>'
        f'<div class="kpi-lbl">FAVORABLE</div></div>',
    ])

    return f"""
    <h2>1. Résumé Exécutif</h2>
    <div>{kpis}</div>
    <table>
      <tr><th>Cible</th><th>Prévu</th><th>Réel</th><th>Gap Abs.</th><th>Gap %</th><th>Statut</th></tr>
      {rows}
    </table>
    """


def _section_top_skus(top_skus: pd.DataFrame) -> str:
    if top_skus.empty:
        return "<h2>2. Top SKUs Défavorables</h2><p>Aucune donnée disponible.</p>"

    rows = ""
    for _, r in top_skus.iterrows():
        rows += (
            f"<tr><td>{r['sku_code']}</td>"
            f"<td>{_gap_pct(r.get('gap_rel_moy', float('nan')))}</td>"
            f"<td>{r.get('gap_abs_total', 0):,.0f}</td>"
            f"<td>{_badge(r.get('statut_dominant', ''))}</td></tr>"
        )
    return f"""
    <h2>2. Top 5 SKUs Défavorables</h2>
    <table>
      <tr><th>SKU</th><th>Gap Moy %</th><th>Gap Abs Total</th><th>Statut Dominant</th></tr>
      {rows}
    </table>
    """


def _section_canal(gap_canal: pd.DataFrame) -> str:
    if gap_canal.empty:
        return "<h2>3. Analyse par Canal</h2><p>Aucune donnée.</p>"

    # Volume uniquement pour simplifier le rapport
    sub = gap_canal[gap_canal["target"] == "volume_vendu"].copy()
    rows = ""
    for _, r in sub.iterrows():
        rows += (
            f"<tr><td>{r.get('canal','')}</td>"
            f"<td>{_gap_pct(r.get('gap_rel_moy', float('nan')))}</td>"
            f"<td>{_badge(r.get('statut_dominant', ''))}</td></tr>"
        )
    return f"""
    <h2>3. Analyse par Canal (Volume)</h2>
    <table>
      <tr><th>Canal</th><th>Gap Moy %</th><th>Statut Dominant</th></tr>
      {rows}
    </table>
    """


def _section_region(gap_region: pd.DataFrame) -> str:
    if gap_region.empty:
        return "<h2>4. Analyse par Région</h2><p>Aucune donnée.</p>"

    sub = gap_region[gap_region["target"] == "volume_vendu"].copy()
    rows = ""
    for _, r in sub.iterrows():
        rows += (
            f"<tr><td>{r.get('region','')}</td>"
            f"<td>{_gap_pct(r.get('gap_rel_moy', float('nan')))}</td>"
            f"<td>{_badge(r.get('statut_dominant', ''))}</td></tr>"
        )
    return f"""
    <h2>4. Analyse par Région (Volume)</h2>
    <table>
      <tr><th>Région</th><th>Gap Moy %</th><th>Statut Dominant</th></tr>
      {rows}
    </table>
    """


def _section_recommendations(recs: list[str]) -> str:
    items = "".join(f'<div class="rec">• {r}</div>' for r in recs)
    return f"<h2>5. Recommandations Automatiques</h2>{items}"


# ── Constructeur rapport complet ──────────────────────────────────────────────

def build_html_report(
    gap_global: pd.DataFrame,
    alert_summary: dict,
    top_skus: pd.DataFrame,
    gap_canal: pd.DataFrame,
    gap_region: pd.DataFrame,
    recommendations: list[str],
    report_month: str | None = None,
) -> str:
    """Assemble le rapport HTML complet."""
    month_label = report_month or datetime.date.today().strftime("%Y-%m")
    today       = datetime.date.today().strftime("%d/%m/%Y")

    body = (
        _section_executive_summary(gap_global, alert_summary)
        + _section_top_skus(top_skus)
        + _section_canal(gap_canal)
        + _section_region(gap_region)
        + _section_recommendations(recommendations)
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8"/>
  <title>Gap Report — {month_label}</title>
  <style>{_CSS}</style>
</head>
<body>
  <h1>Rapport d'Écart Mensuel — {month_label}</h1>
  <p style="color:#7F8C8D">Généré le {today} · Lubricants Portfolio &amp; Pricing System</p>
  {body}
  <footer>Rapport automatique · Données synthétiques · Module M5 Gap Analysis</footer>
</body>
</html>"""


# ── Export ────────────────────────────────────────────────────────────────────

def export_report(
    html_content: str,
    output_dir: str,
    report_month: str | None = None,
) -> dict[str, Path]:
    """Écrit le rapport HTML (et PDF si WeasyPrint disponible).

    Returns : {'html': path_html, 'pdf': path_pdf or None}
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    month_label = (report_month or datetime.date.today().strftime("%Y_%m")).replace("-", "_")
    html_path   = out / f"gap_report_{month_label}.html"
    html_path.write_text(html_content, encoding="utf-8")
    logger.success("Rapport HTML → {}", html_path)

    pdf_path = None
    if _WEASY_AVAILABLE:
        pdf_path = out / f"gap_report_{month_label}.pdf"
        WeasyHTML(string=html_content).write_pdf(str(pdf_path))
        logger.success("Rapport PDF  → {}", pdf_path)
    else:
        logger.info("PDF ignoré (WeasyPrint absent). Installer : pip install weasyprint")

    return {"html": html_path, "pdf": pdf_path}
