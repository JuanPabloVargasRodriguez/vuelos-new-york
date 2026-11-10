"""Crea una portada estática y el informe Evidently del lote válido."""
from __future__ import annotations
import html
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

from scripts.validar_datos import ErrorValidacion, validar_proyecto

COLUMNAS = ["demora_salida_min", "demora_llegada_min"]
TITULOS = {"control": "Febrero de 2013", "nuevo": "Julio de 2013"}


def commit_actual() -> str:
    if os.getenv("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"][:7]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=7", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "local"


def tabla_aeropuertos(df: pd.DataFrame) -> str:
    res = df.groupby("origen", as_index=False).agg(
        vuelos=("vuelo_id", "size"),
        mediana_salida=("demora_salida_min", "median"),
        mediana_llegada=("demora_llegada_min", "median"),
    ).sort_values("origen")
    trs = "".join(
        f"<tr><td>{html.escape(str(r.origen))}</td><td>{r.vuelos:,}</td>"
        f"<td>{r.mediana_salida:.1f}</td><td>{r.mediana_llegada:.1f}</td></tr>"
        for r in res.itertuples(index=False)
    )
    return f"<table><thead><tr><th>Origen</th><th>Vuelos</th><th>Med. salida</th><th>Med. llegada</th></tr></thead><tbody>{trs}</tbody></table>"


def tabla_rutas(df: pd.DataFrame) -> str:
    res = df.groupby(["origen", "destino"], as_index=False).agg(
        vuelos=("vuelo_id", "size"),
        mediana_llegada=("demora_llegada_min", "median"),
    )
    res = res[res["vuelos"] >= 10].sort_values(
        ["mediana_llegada", "vuelos"], ascending=[False, False]
    ).head(10)
    trs = "".join(
        f"<tr><td>{html.escape(str(r.origen))}–{html.escape(str(r.destino))}</td>"
        f"<td>{r.vuelos}</td><td>{r.mediana_llegada:.1f} min</td></tr>"
        for r in res.itertuples(index=False)
    )
    return f"<table><thead><tr><th>Ruta</th><th>Vuelos</th><th>Med. llegada</th></tr></thead><tbody>{trs}</tbody></table>"


def ejecutar():
    validar_proyecto()  # Si es inválido, jamás se genera un sitio nuevo.
    referencia = pd.read_csv("datos/referencia.csv")
    actual = pd.read_csv("datos/actual.csv")
    lote = str(actual["lote"].iloc[0])
    titulo = TITULOS[lote]
    carpeta = Path("sitio")
    carpeta.mkdir(exist_ok=True)
    nombre_informe = f"evidently-enero-vs-{'febrero' if lote == 'control' else 'julio'}.html"
    # La misma configuración de Evidently para ambas comparaciones.
    report = Report([DataDriftPreset(columns=COLUMNAS)])
    snapshot = report.run(actual[COLUMNAS], referencia[COLUMNAS])
    snapshot.save_html(str(carpeta / nombre_informe))

    sello = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    commit = html.escape(commit_actual())
    med_s = actual["demora_salida_min"].median()
    med_l = actual["demora_llegada_min"].median()
    base_s = referencia["demora_salida_min"].median()
    base_l = referencia["demora_llegada_min"].median()
    tardios = (actual["demora_llegada_min"] > 15).mean() * 100
    por_origen = tabla_aeropuertos(actual)
    por_ruta = tabla_rutas(actual)
    pagina = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NYC FlightOps | {titulo}</title>
<style>
:root{{--bg:#0b1020;--card:#161f35;--t:#eaf1fc;--muted:#9eafcb;--line:#293950;--accent:#75c9d7}}
*{{box-sizing:border-box}}body{{font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--t);margin:0}}
main{{max-width:1130px;margin:auto;padding:36px 20px 72px}}header{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px}}
.brand{{font-size:14px;letter-spacing:.15em;color:var(--accent);font-weight:800}}.tag{{background:#26344f;color:#b4e9e8;border-radius:32px;padding:8px 14px;font-size:13px}}
h1{{font-size:clamp(33px,5vw,56px);margin:26px 0 8px;letter-spacing:-.04em;line-height:1.12}}p,small{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:26px 0}}
.card,.panel{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px;box-shadow:0 10px 28px #0002}}
.card h2{{font-size:13px;font-weight:600;color:var(--muted);margin:0 0 14px}}.value{{font-size:33px;font-weight:750;letter-spacing:-.035em}}.sub{{font-size:13px;margin-top:5px}}
section{{margin-top:22px}}h3{{margin:0 0 10px;font-size:22px}}a.btn{{display:inline-block;background:var(--accent);color:#091322;text-decoration:none;font-weight:750;border-radius:11px;padding:13px 22px;margin-top:10px}}
table{{border-collapse:collapse;width:100%}}th,td{{padding:11px 8px;text-align:left;border-bottom:1px solid var(--line)}}th{{color:var(--muted);font-size:13px}}.tables{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
footer{{border-top:1px solid var(--line);margin-top:33px;padding-top:17px;color:var(--muted);font-size:13px}}code{{color:#b7f2ec}}@media(max-width:800px){{.tables{{grid-template-columns:1fr}}.panel{{overflow-x:auto}}}}
</style></head><body><main>
<header><span class="brand">✈ NYC FLIGHTOPS · MONITOREO</span><span class="tag">Referencia fija: Enero 2013</span></header>
<h1>Demoras de vuelos<br>{titulo}</h1><p>Seguimiento operativo basado en muestras históricas de aeropuertos de Nueva York.</p>
<div class="grid">
<article class="card"><h2>Vuelos analizados</h2><div class="value">{len(actual):,}</div><div class="sub">Lote publicado: {titulo}</div></article>
<article class="card"><h2>Mediana demora de salida</h2><div class="value">{med_s:.1f} <small>min</small></div><div class="sub">Enero: {base_s:.1f} min · Diferencia: {med_s-base_s:+.1f} min</div></article>
<article class="card"><h2>Mediana demora de llegada</h2><div class="value">{med_l:.1f} <small>min</small></div><div class="sub">Enero: {base_l:.1f} min · Diferencia: {med_l-base_l:+.1f} min</div></article>
<article class="card"><h2>Llegadas con más de 15 min de demora</h2><div class="value">{tardios:.1f}%</div><div class="sub">Indicador exploratorio del lote actual</div></article>
</div>
<section class="panel"><h3>¿Cambió la distribución?</h3>
<p>Analiza las dos variables de demoras con Evidently. El informe compara <strong>enero de 2013</strong> con <strong>{titulo.lower()}</strong>.
El drift es una señal para investigar, no un error que bloquee el despliegue.</p>
<a class="btn" href="{nombre_informe}">Abrir informe Evidently · enero vs. {titulo.split()[0].lower()}</a></section>
<div class="tables">
<section class="panel"><h3>Detalle por aeropuerto</h3><p>Medianas en minutos (pueden ser negativas).</p>{por_origen}</section>
<section class="panel"><h3>Rutas a revisar</h3><p>Top 10 por mediana de demora en llegada; mínimo 10 vuelos por ruta.</p>{por_ruta}</section>
</div>
<footer>Fuente: nycflights13 · Autor: estudiante responsable · Generado: {sello} · Commit: <code>{commit}</code> ·
Datos observados de 2013 (no es información en tiempo real). Las muestras por mes son de tamaño fijo.</footer>
</main></body></html>'''
    (carpeta / "index.html").write_text(pagina, encoding="utf-8")
    (carpeta / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Sitio generado: {carpeta / 'index.html'}")
    print(f"Informe generado: {carpeta / nombre_informe}")
    print(f"Mes publicado: {titulo} | commit: {commit}")


if __name__ == "__main__":
    try:
        ejecutar()
    except (ErrorValidacion, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
