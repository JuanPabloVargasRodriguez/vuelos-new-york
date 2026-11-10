"""Separa el CSV ORIGINAL (sin modificarlo) en 3 lotes de 12.000 filas."""
import csv
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from scripts.validar_datos import CAMPOS, ErrorValidacion, validar_archivo

ORIGEN = Path("fuente/vuelos_nyc_2013.csv")
SALIDA = Path("datos")
LOTES = {1: ("referencia", "referencia.csv"),
         2: ("control", "control.csv"),
         7: ("nuevo", "nuevo.csv")}


def ejecutar():
    if not ORIGEN.is_file():
        raise FileNotFoundError(
            f"Falta {ORIGEN}. Descárgalo del enlace de la práctica y no lo edites."
        )
    bloques = {mes: [] for mes in LOTES}
    etiquetas = Counter()
    with ORIGEN.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        if lector.fieldnames != CAMPOS:
            raise ErrorValidacion(f"Encabezados originales no coinciden: {lector.fieldnames}")
        for r in lector:
            if None in r or any(v is None for v in r.values()):
                raise ErrorValidacion(f"CSV de origen: fila {lector.line_num} mal formada")
            try:
                f = date.fromisoformat(r["fecha"])
            except ValueError as e:
                raise ErrorValidacion(f"CSV de origen: fila {lector.line_num}, fecha inválida") from e
            if f.year != 2013 or f.month not in LOTES:
                raise ErrorValidacion(f"CSV de origen: fila {lector.line_num}, mes no esperado")
            etiquetas[(f.month, r["lote"])] += 1
            nombre, _ = LOTES[f.month]
            # Los CSV derivados usan etiquetas canónicas. El original permanece intacto.
            bloques[f.month].append({**r, "lote": nombre})
    print("Etiquetas de lote observadas en origen:", dict(etiquetas))
    for mes, filas in bloques.items():
        if len(filas) != 12000:
            raise ErrorValidacion(f"Mes {mes}: se esperaban 12000 filas y hay {len(filas)}")
    SALIDA.mkdir(exist_ok=True)
    for mes, (lote, nombre) in LOTES.items():
        destino = SALIDA / nombre
        if destino.exists():
            print(f"Conservado (ya existía): {destino}")
            continue
        with destino.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=CAMPOS, lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(bloques[mes])
        print(f"Creado: {destino} ({len(bloques[mes])} filas)")
    actual = SALIDA / "actual.csv"
    if not actual.exists():
        shutil.copyfile(SALIDA / "control.csv", actual)
        print(f"Primera publicación preparada: {actual} = febrero")
    validar_archivo(SALIDA / "referencia.csv", "referencia")
    validar_archivo(SALIDA / "actual.csv", "actual")
    print("Lotes preparados. Nota: 'actual.csv' se conserva si ya existe.")


if __name__ == "__main__":
    try:
        ejecutar()
    except (OSError, ErrorValidacion) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
