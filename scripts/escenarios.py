"""Reproduce los cuatro escenarios sin tocar referencia.csv ni nuevo.csv."""
import argparse
import csv
import shutil
from pathlib import Path
from scripts.validar_datos import CAMPOS

DATOS = Path("datos")


def ejecutar(accion):
    actual = DATOS / "actual.csv"
    fuente = DATOS / ("control.csv" if accion == "febrero" else "nuevo.csv")
    if not fuente.exists():
        raise FileNotFoundError(f"Primero prepara los lotes: {fuente}")
    if accion in ("febrero", "julio", "recuperar"):
        shutil.copyfile(fuente, actual)
        print(f"{accion}: copia exacta de {fuente} a {actual}")
        return
    with fuente.open(encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        filas = list(lector)
        if not filas:
            raise ValueError("Lote de julio sin datos")
        if lector.fieldnames != CAMPOS:
            raise ValueError("Encabezados inesperados")
    original = filas[0]["distancia_millas"]
    filas[0]["distancia_millas"] = "0"
    with actual.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"Fallo intencional: {actual}, fila 2, distancia {original} -> 0")
    print("Para recuperar: python -m scripts.escenarios recuperar")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("accion", choices=["febrero", "julio", "romper", "recuperar"])
    ejecutar(parser.parse_args().accion)
