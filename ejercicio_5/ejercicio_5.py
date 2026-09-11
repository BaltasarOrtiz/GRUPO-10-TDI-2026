#!/usr/bin/env python3
"""Ejercicio 5 — Eficiencia de Almacenamiento y Empaquetado a Nivel de Bits (Bitwise).

Genera 20 personas ficticias, las guarda en CSV (longitud variable) y en
binario de longitud fija con los 8 booleanos empaquetados en 1 byte
(bitwise), compara tamaños y permite releer ambos formatos.

Uso:
    python3 ejercicio_5.py generar
    python3 ejercicio_5.py leer --formato texto
    python3 ejercicio_5.py leer --formato binario
"""
from __future__ import annotations
import argparse
import csv
import struct
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #
DIR_SCRIPT = Path(__file__).resolve().parent      # salida/ se ubica SIEMPRE junto al script
DIR_SALIDA = DIR_SCRIPT / "salida"
RUTA_CSV = DIR_SALIDA / "personas_variable.csv"
RUTA_BIN = DIR_SALIDA / "personas_fijo.bin"
RUTA_RESUMEN = DIR_SALIDA / "resumen.txt"

CAMPOS_BOOL = ["estudios_primarios", "estudios_secundarios", "estudios_universitarios",
               "vivienda_propia", "obra_social", "trabaja", "posee_vehiculo",
               "posee_seguro_medico"]
ETIQUETAS_BOOL = ["Estudios primarios", "Estudios secundarios", "Estudios universitarios",
                   "Vivienda propia", "Obra social", "Trabaja", "Posee vehículo",
                   "Posee seguro médico"]

TAM_APELLIDO_NOMBRE = 40   # bytes UTF-8, fijo
TAM_DIRECCION = 50         # bytes UTF-8, fijo
FORMATO_REGISTRO = f"<{TAM_APELLIDO_NOMBRE}s{TAM_DIRECCION}sIB"
TAM_REGISTRO = struct.calcsize(FORMATO_REGISTRO)   # 40+50+4+1 = 95 bytes/persona


class ErrorEntrada(Exception):
    """Entrada inválida (archivo faltante, corrupto o campo que excede el ancho fijo)."""


# --------------------------------------------------------------------------- #
# Paso 1 — Datos: 20 personas ficticias
# --------------------------------------------------------------------------- #
PERSONAS: list[dict] = [
    {"apellido_nombre": "Gómez, Martina", "direccion": "Av. San Martín 1450, Rosario, Santa Fe",
     "dni": 30123456, "booleanos": [True, True, True, True, True, True, True, True]},
    {"apellido_nombre": "Fernández, Bruno", "direccion": "Calle Belgrano 320, Córdoba, Córdoba",
     "dni": 28456789, "booleanos": [False, False, False, False, False, False, False, False]},
    {"apellido_nombre": "Rodríguez, Camila", "direccion": "Av. Colón 875, Mendoza, Mendoza",
     "dni": 32567890, "booleanos": [True, True, False, True, True, True, False, False]},
    {"apellido_nombre": "López, Agustín", "direccion": "Calle Mitre 210, La Plata, Buenos Aires",
     "dni": 27890123, "booleanos": [True, True, True, False, False, True, True, False]},
    {"apellido_nombre": "Díaz, Valentina", "direccion": "Av. Rivadavia 4521, Salta, Salta",
     "dni": 35678901, "booleanos": [True, False, False, False, True, False, False, True]},
    {"apellido_nombre": "Pérez, Tomás", "direccion": "Calle Sarmiento 678, Neuquén, Neuquén",
     "dni": 29345678, "booleanos": [True, True, True, True, False, True, True, True]},
    {"apellido_nombre": "Sánchez, Lucía", "direccion": "Av. Pellegrini 1200, Rosario, Santa Fe",
     "dni": 33456789, "booleanos": [True, True, False, False, True, False, False, False]},
    {"apellido_nombre": "Romero, Mateo", "direccion": "Calle Alberdi 55, Resistencia, Chaco",
     "dni": 26789012, "booleanos": [True, False, False, True, False, True, True, False]},
    {"apellido_nombre": "Torres, Sofía", "direccion": "Av. Independencia 980, Tucumán, Tucumán",
     "dni": 31234567, "booleanos": [True, True, True, True, True, False, False, True]},
    {"apellido_nombre": "Flores, Ignacio", "direccion": "Calle Urquiza 145, Paraná, Entre Ríos",
     "dni": 24567890, "booleanos": [True, True, False, False, False, True, False, False]},
    {"apellido_nombre": "Acosta, Catalina", "direccion": "Av. Libertador 3300, Jujuy, Jujuy",
     "dni": 37890123, "booleanos": [True, True, True, False, True, True, True, False]},
    {"apellido_nombre": "Molina, Santiago", "direccion": "Calle 9 de Julio 410, Santa Fe, Santa Fe",
     "dni": 25678901, "booleanos": [True, False, False, False, False, False, True, False]},
    {"apellido_nombre": "Suárez, Julieta", "direccion": "Av. Corrientes 2200, Posadas, Misiones",
     "dni": 34567890, "booleanos": [True, True, True, True, False, False, False, True]},
    {"apellido_nombre": "Ortiz, Nicolás", "direccion": "Calle Moreno 89, San Juan, San Juan",
     "dni": 23456789, "booleanos": [True, True, False, True, True, True, False, True]},
    {"apellido_nombre": "Silva, Renata", "direccion": "Av. Yrigoyen 670, Comodoro Rivadavia, Chubut",
     "dni": 38901234, "booleanos": [True, False, False, False, True, True, False, False]},
    {"apellido_nombre": "Cabrera, Joaquín", "direccion": "Calle Lavalle 560, San Luis, San Luis",
     "dni": 22345678, "booleanos": [True, True, True, False, False, False, True, True]},
    {"apellido_nombre": "Núñez, Abril", "direccion": "Av. Roca 1120, Río Cuarto, Córdoba",
     "dni": 36789012, "booleanos": [True, True, False, True, False, True, False, False]},
    {"apellido_nombre": "Benítez, Franco", "direccion": "Calle Güemes 340, Bahía Blanca, Buenos Aires",
     "dni": 21234567, "booleanos": [True, False, False, False, False, True, True, False]},
    {"apellido_nombre": "Herrera, Milagros", "direccion": "Av. San Juan 780, Formosa, Formosa",
     "dni": 39012345, "booleanos": [True, True, True, True, True, True, False, False]},
    {"apellido_nombre": "Vega, Emiliano", "direccion": "Calle Rivadavia 990, Santa Rosa, La Pampa",
     "dni": 20123456, "booleanos": [True, True, False, False, True, False, True, True]},
]


# --------------------------------------------------------------------------- #
# Paso 2 — Empaquetado y desempaquetado bitwise
# Un booleano tiene máximo 1 bit de información, así que 8 booleanos caben
# exactos en 1 byte.
# --------------------------------------------------------------------------- #
def empaquetar_booleanos(valores: list[bool]) -> int:
    """Empaqueta 8 booleanos en 1 byte: bit i = 1 si valores[i] es True."""
    byte = 0
    for i, v in enumerate(valores):
        if v:
            byte |= (1 << i)
    return byte


def desempaquetar_booleanos(byte: int) -> list[bool]:
    """Inverso de empaquetar_booleanos: extrae los 8 bits de vuelta a una lista de bool."""
    return [bool(byte & (1 << i)) for i in range(8)]


# --------------------------------------------------------------------------- #
# Paso 3 — Archivo de longitud variable (CSV)
# --------------------------------------------------------------------------- #
def escribir_csv(personas: list[dict], ruta: Path) -> None:
    """Escribe `personas` como CSV de longitud variable (booleanos como texto)."""
    encabezado = ["apellido_nombre", "direccion", "dni"] + CAMPOS_BOOL
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(encabezado)
        for persona in personas:
            fila = [persona["apellido_nombre"], persona["direccion"], persona["dni"]]
            fila += [str(valor) for valor in persona["booleanos"]]
            writer.writerow(fila)


def leer_csv(ruta: Path) -> list[dict]:
    """Lee un CSV escrito por escribir_csv y devuelve la misma forma que PERSONAS."""
    if not ruta.exists():
        raise ErrorEntrada(f"No se encontró {ruta}. Corré primero: python3 ejercicio_5.py generar")
    personas = []
    with open(ruta, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            personas.append({
                "apellido_nombre": fila["apellido_nombre"],
                "direccion": fila["direccion"],
                "dni": int(fila["dni"]),
                "booleanos": [fila[campo] == "True" for campo in CAMPOS_BOOL],
            })
    return personas


# --------------------------------------------------------------------------- #
# Paso 4 — Archivo binario de longitud fija (bitwise)
# --------------------------------------------------------------------------- #
def _empaquetar_texto_fijo(texto: str, ancho: int, ruta_campo: str) -> bytes:
    """Codifica `texto` en UTF-8 y lo rellena con ceros hasta `ancho` bytes fijos."""
    datos = texto.encode("utf-8")
    if len(datos) > ancho:
        raise ErrorEntrada(f"{ruta_campo} ({len(datos)} bytes UTF-8) excede el ancho fijo de {ancho} bytes: {texto!r}")
    return datos.ljust(ancho, b"\x00")


def escribir_binario(personas: list[dict], ruta: Path) -> None:
    """Escribe `personas` como registros binarios de longitud fija (bitwise)."""
    with open(ruta, "wb") as f:
        for persona in personas:
            apellido_bytes = _empaquetar_texto_fijo(
                persona["apellido_nombre"], TAM_APELLIDO_NOMBRE, "apellido_nombre")
            direccion_bytes = _empaquetar_texto_fijo(
                persona["direccion"], TAM_DIRECCION, "direccion")
            byte_booleanos = empaquetar_booleanos(persona["booleanos"])
            registro = struct.pack(FORMATO_REGISTRO, apellido_bytes, direccion_bytes,
                                    persona["dni"], byte_booleanos)
            f.write(registro)


def leer_binario(ruta: Path) -> list[dict]:
    """Lee registros binarios de longitud fija y desempaqueta el byte de booleanos."""
    if not ruta.exists():
        raise ErrorEntrada(f"No se encontró {ruta}. Corré primero: python3 ejercicio_5.py generar")
    tamano = ruta.stat().st_size
    if tamano % TAM_REGISTRO != 0:
        raise ErrorEntrada(
            f"El archivo binario no tiene un tamaño múltiplo de {TAM_REGISTRO} bytes/registro "
            f"(posible corrupción): {tamano} bytes")
    personas = []
    with open(ruta, "rb") as f:
        for _ in range(tamano // TAM_REGISTRO):
            apellido_raw, direccion_raw, dni, byte_booleanos = struct.unpack(
                FORMATO_REGISTRO, f.read(TAM_REGISTRO))
            personas.append({
                "apellido_nombre": apellido_raw.rstrip(b"\x00").decode("utf-8"),
                "direccion": direccion_raw.rstrip(b"\x00").decode("utf-8"),
                "dni": dni,
                "booleanos": desempaquetar_booleanos(byte_booleanos),
            })
    return personas


# --------------------------------------------------------------------------- #
# Paso 5 — Comparación de tamaños y conclusión (punto c)
# --------------------------------------------------------------------------- #
def comparar_tamanos(ruta_csv: Path, ruta_bin: Path, n_personas: int) -> str:
    """Compara los tamaños reales (en disco) del CSV y el binario, y proyecta a escala."""
    n1 = ruta_csv.stat().st_size
    n2 = ruta_bin.stat().st_size
    n = n_personas
    return (
        "================ COMPARACIÓN DE TAMAÑOS (Ejercicio 5) ================\n"
        f"Archivo de longitud variable (CSV) : {n1} bytes   ({n1 / n:.2f} bytes/persona en promedio)\n"
        f"Archivo binario de longitud fija   : {n2} bytes   ({TAM_REGISTRO} bytes/persona, fijo)\n"
        f"Ahorro del binario vs. el texto    : {n1 - n2} bytes  ({(1 - n2 / n1) * 100:.2f} %)\n"
        "\n"
        "Desglose del campo de 8 booleanos (el punto central del ejercicio):\n"
        "   En texto  : hasta 8 x \"False\" (5 car.) + 7 comas = 47 bytes/persona en el peor caso\n"
        "   En binario: 1 byte/persona, empaquetado con operadores bitwise (|=, <<, &)\n"
        "   Ahorro solo en ese campo: ~46 bytes/persona (~46x más chico)\n"
        "\n"
        "Proyección a la misma estructura, a escala:\n"
        f"   20 personas (este ejercicio) : {n1 - n2} bytes de diferencia\n"
        f"   1.000.000 de personas        : {(n1 - n2) / n * 1_000_000 / 1048576:.1f} MiB de diferencia\n"
        f"   10.000.000 de personas       : {(n1 - n2) / n * 10_000_000 / 1048576:.1f} MiB de diferencia\n"
        "========================================================================"
    )


# --------------------------------------------------------------------------- #
# Paso 6 — Impresión de una persona (usado por `leer`)
# --------------------------------------------------------------------------- #
def imprimir_persona(persona: dict, indice: int) -> None:
    """Imprime una persona con sus datos y sus 8 booleanos en formato legible."""
    print(f"--- Persona {indice:02d} ---")
    print(f"Apellido y Nombre : {persona['apellido_nombre']}")
    print(f"Dirección         : {persona['direccion']}")
    print(f"DNI               : {persona['dni']}")
    for etiqueta, valor in zip(ETIQUETAS_BOOL, persona["booleanos"]):
        print(f"   {etiqueta:<24}: {'Sí' if valor else 'No'}")


# --------------------------------------------------------------------------- #
# Paso 7 — main() y subcomandos
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    try:
        if args.comando == "generar":
            return _comando_generar()
        else:  # "leer"
            return _comando_leer(args.formato)
    except ErrorEntrada as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def _comando_generar() -> int:
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    print(f"[1/3] Generando datos de {len(PERSONAS)} personas (ficticias) y escribiendo "
          "el archivo de longitud variable (CSV)...")
    escribir_csv(PERSONAS, RUTA_CSV)
    print(f"      Escrito: {RUTA_CSV} ({RUTA_CSV.stat().st_size} bytes)")

    print("[2/3] Empaquetando y escribiendo el archivo binario de longitud fija (bitwise)...")
    escribir_binario(PERSONAS, RUTA_BIN)
    print(f"      Escrito: {RUTA_BIN} ({RUTA_BIN.stat().st_size} bytes, "
          f"{TAM_REGISTRO} bytes/registro x {len(PERSONAS)})")

    print("[3/3] Comparando tamaños...")
    texto = comparar_tamanos(RUTA_CSV, RUTA_BIN, len(PERSONAS))
    print(texto)
    RUTA_RESUMEN.write_text(texto + "\n", encoding="utf-8")
    print(f"Salida guardada: {RUTA_RESUMEN}")
    return 0


def _comando_leer(formato: str) -> int:
    if formato == "texto":
        print(f"Leyendo archivo de longitud variable (CSV): {RUTA_CSV}")
        personas = leer_csv(RUTA_CSV)
    else:
        print(f"Leyendo archivo binario de longitud fija (desempaquetado bitwise): {RUTA_BIN}")
        personas = leer_binario(RUTA_BIN)
    for i, persona in enumerate(personas, start=1):
        imprimir_persona(persona, i)
    print(f"\nTotal: {len(personas)} personas leídas.")
    return 0


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejercicio 5 — Eficiencia de almacenamiento y empaquetado bitwise.")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    subparsers.add_parser("generar", help="Genera los 20 registros y escribe CSV + binario.")

    parser_leer = subparsers.add_parser("leer", help="Lee y muestra los registros generados.")
    parser_leer.add_argument("--formato", choices=["texto", "binario"], required=True,
                              help="Formato a leer: 'texto' (CSV) o 'binario' (bitwise).")

    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
