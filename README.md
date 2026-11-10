# Monitoreo de demoras NYC 2013: CI/CD + Evidently

Proyecto educativo: valida lotes de vuelos de enero, febrero y julio de 2013 y publica
el informe Evidently del **último lote validado** en GitHub Pages. Un error de calidad
bloquea el despliegue; detectar drift no lo bloquea.

## Inicio (Windows PowerShell)

1. Descarga `vuelos_nyc_2013.csv` desde el enlace de Google Drive del PDF de la práctica y
   guárdalo **sin editar** en `fuente/vuelos_nyc_2013.csv`.
2. `py -3.12 -m venv .venv`
3. `.\.venv\Scripts\Activate.ps1`
4. `python -m pip install -r requirements.txt`
5. `python -m scripts.preparar_lotes` (crea referencia, control, nuevo y actual=control).
6. `python -m pytest tests/ -v`
7. `python -m scripts.validar_datos`
8. `python -m scripts.generar_informe`
9. `python -m http.server 8000 --directory sitio` y abre http://localhost:8000/.

## Escenarios (cada cambio tiene su propio commit + push)

- Primera publicación: `python -m scripts.escenarios febrero`.
- Actualización válida: `python -m scripts.escenarios julio`.
- Error deliberado: `python -m scripts.escenarios romper`.
- Recuperación: `python -m scripts.escenarios recuperar`.

Antes de cada push válido, ejecuta `python -m pytest tests/ -v` y
`python -m scripts.validar_datos`. El escenario roto debe fallar y no debe generarse
una publicación nueva. Para probar el rechazo, sí haz push del CSV roto de forma consciente.

## Estructura

- `fuente/`: CSV original, intacto.
- `datos/`: tres lotes preparados más `actual.csv`.
- `scripts/`: preparación, validación, escenarios y generación web.
- `tests/`: 15 pruebas unitarias independientes.
- `sitio/`: HTML generado (se excluye del commit y se publica como artefacto de Actions).
- `.github/workflows/ci-cd.yml`: CI seguida de CD.

## Fuente

[`nycflights13`](https://nycflights13.tidyverse.org/) de datos de vuelos de 2013.
No representa tráfico aéreo en tiempo real.
