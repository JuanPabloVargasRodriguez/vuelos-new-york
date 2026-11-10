import csv
import pytest
from scripts.validar_datos import CAMPOS, ErrorValidacion, validar_archivo


def ejemplo(**cambios):
    fila = dict(zip(CAMPOS, ["1", "2013-01-05", "JFK", "LAX", "-4", "0", "2475", "referencia"]))
    fila.update(cambios)
    return fila


def escribir(tmp_path, filas, campos=CAMPOS):
    ruta = tmp_path / "muestra.csv"
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(filas)
    return ruta


def falla(tmp_path, filas, campo, campos=CAMPOS):
    ruta = escribir(tmp_path, filas, campos)
    with pytest.raises(ErrorValidacion) as err:
        validar_archivo(ruta, "referencia")
    assert campo in str(err.value)
    assert str(ruta) in str(err.value)


def test_registro_valido(tmp_path):
    assert validar_archivo(escribir(tmp_path, [ejemplo()]), "referencia") == 1


def test_demora_negativa_y_cero_validos(tmp_path):
    assert validar_archivo(escribir(tmp_path, [ejemplo(demora_salida_min="-35", demora_llegada_min="0")]), "referencia") == 1


def test_encabezado_faltante(tmp_path):
    faltantes = [x for x in CAMPOS if x != "destino"]
    falla(tmp_path, [ejemplo()], "encabezados", faltantes)


def test_fecha_invalida(tmp_path):
    falla(tmp_path, [ejemplo(fecha="2013-01-32")], "fecha")


def test_identificador_duplicado(tmp_path):
    falla(tmp_path, [ejemplo(), ejemplo(destino="MIA")], "vuelo_id")


def test_distancia_cero(tmp_path):
    falla(tmp_path, [ejemplo(distancia_millas="0")], "distancia_millas")


def test_distancia_negativa(tmp_path):
    falla(tmp_path, [ejemplo(distancia_millas="-3")], "distancia_millas")


def test_origen_invalido(tmp_path):
    falla(tmp_path, [ejemplo(origen="BOG")], "origen")


def test_destino_minuscula(tmp_path):
    falla(tmp_path, [ejemplo(destino="lax")], "destino")


def test_mes_incompatible(tmp_path):
    falla(tmp_path, [ejemplo(fecha="2013-02-12")], "fecha")


def test_csv_vacio(tmp_path):
    falla(tmp_path, [], "filas")


def test_decimales_invalidos(tmp_path):
    falla(tmp_path, [ejemplo(demora_llegada_min="1.5")], "demora_llegada_min")


def test_lote_invalido(tmp_path):
    falla(tmp_path, [ejemplo(lote="nuevo")], "lote")


def test_lote_control_valido(tmp_path):
    ruta = escribir(tmp_path, [ejemplo(fecha="2013-02-05", lote="control")])
    assert validar_archivo(ruta, "actual") == 1


def test_lotes_mezclados_invalidos(tmp_path):
    ruta = escribir(tmp_path, [ejemplo(fecha="2013-02-05", lote="control"),
                               ejemplo(vuelo_id="2", fecha="2013-07-05", lote="nuevo")])
    with pytest.raises(ErrorValidacion, match="mezclados"):
        validar_archivo(ruta, "actual")
