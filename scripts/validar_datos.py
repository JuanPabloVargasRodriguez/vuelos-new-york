"""Validador estricto: comprueba TODAS las filas de cada CSV."""
from __future__ import annotations
import csv
import re
import sys
from datetime import date
from pathlib import Path

CAMPOS = [
    "vuelo_id", "fecha", "origen", "destino",
    "demora_salida_min", "demora_llegada_min", "distancia_millas", "lote",
]
MESES = {"referencia": 1, "control": 2, "nuevo": 7}
ENTERO = re.compile(r"^-?\d+$")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DESTINO = re.compile(r"^[A-Z]{3}$")

class ErrorValidacion(ValueError):
    """Incluye nombre del archivo, fila y campo cuando procede."""


def _fallo(ruta: Path, fila: int, campo: str, mensaje: str) -> None:
    raise ErrorValidacion(f"{ruta} | fila {fila} | campo '{campo}': {mensaje}")


def _entero(valor: str, ruta: Path, fila: int, campo: str, positivo: bool = False) -> int:
    if not ENTERO.fullmatch(valor or ""):
        _fallo(ruta, fila, campo, f"se esperaba entero; recibido {valor!r}")
    n = int(valor)
    if positivo and n <= 0:
        _fallo(ruta, fila, campo, "debe ser entero positivo (> 0)")
    return n


def validar_archivo(ruta: str | Path, tipo: str) -> int:
    ruta = Path(ruta)
    if tipo not in {"referencia", "actual"}:
        raise ValueError("tipo debe ser 'referencia' o 'actual'")
    if not ruta.is_file():
        raise ErrorValidacion(f"{ruta}: archivo no encontrado")
    vistos: set[int] = set()
    conteo = 0
    try:
        with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            if lector.fieldnames != CAMPOS:
                raise ErrorValidacion(
                    f"{ruta} | encabezados incorrectos; esperados: {CAMPOS}; "
                    f"recibidos: {lector.fieldnames}"
                )
            for registro in lector:
                fila = lector.line_num
                if None in registro or any(valor is None for valor in registro.values()):
                    _fallo(ruta, fila, "columnas", "cantidad incorrecta de campos")
                lote = registro["lote"]
                if tipo == "referencia" and lote != "referencia":
                    _fallo(ruta, fila, "lote", "la referencia solo admite 'referencia'")
                if tipo == "actual" and lote not in {"control", "nuevo"}:
                    _fallo(ruta, fila, "lote", "actual solo admite 'control' o 'nuevo'")
                # No debe haber mezcla de lotes en actual.
                if conteo == 0:
                    lote_primero = lote
                elif lote != lote_primero:
                    _fallo(ruta, fila, "lote", "archivo con lotes mezclados")
                identificador = _entero(registro["vuelo_id"], ruta, fila, "vuelo_id", positivo=True)
                if identificador in vistos:
                    _fallo(ruta, fila, "vuelo_id", f"identificador duplicado: {identificador}")
                vistos.add(identificador)
                fecha_txt = registro["fecha"]
                if not FECHA.fullmatch(fecha_txt):
                    _fallo(ruta, fila, "fecha", "formato obligatorio AAAA-MM-DD")
                try:
                    fecha = date.fromisoformat(fecha_txt)
                except ValueError:
                    _fallo(ruta, fila, "fecha", "fecha inexistente")
                if fecha.year != 2013 or fecha.month != MESES[lote]:
                    _fallo(ruta, fila, "fecha", f"mes/año incompatibles con lote {lote}")
                if registro["origen"] not in {"JFK", "LGA", "EWR"}:
                    _fallo(ruta, fila, "origen", "solo JFK, LGA o EWR")
                if not DESTINO.fullmatch(registro["destino"]):
                    _fallo(ruta, fila, "destino", "debe tener tres letras mayúsculas")
                _entero(registro["demora_salida_min"], ruta, fila, "demora_salida_min")
                _entero(registro["demora_llegada_min"], ruta, fila, "demora_llegada_min")
                _entero(registro["distancia_millas"], ruta, fila, "distancia_millas", positivo=True)
                conteo += 1
    except UnicodeDecodeError as exc:
        raise ErrorValidacion(f"{ruta}: no se pudo leer como UTF-8: {exc}") from exc
    if conteo == 0:
        raise ErrorValidacion(f"{ruta}: el CSV no contiene filas de datos")
    return conteo


def validar_proyecto(carpeta: str | Path = "datos") -> tuple[int, int]:
    carpeta = Path(carpeta)
    nr = validar_archivo(carpeta / "referencia.csv", "referencia")
    na = validar_archivo(carpeta / "actual.csv", "actual")
    print(f"VALIDACIÓN CORRECTA: referencia={nr} filas; actual={na} filas")
    return nr, na


if __name__ == "__main__":
    try:
        validar_proyecto()
    except ErrorValidacion as exc:
        print(f"VALIDACIÓN FALLIDA: {exc}", file=sys.stderr)
        sys.exit(1)
