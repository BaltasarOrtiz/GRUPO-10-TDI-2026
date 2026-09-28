#!/usr/bin/env python3
"""Ejercicio 3 — Entropía Empírica en Archivos (Texto vs. Comprimidos).

Lee un archivo arbitrario byte a byte en O(N) y calcula la frecuencia
relativa de cada byte, la entropía empírica de Shannon y la redundancia.

Uso:
    python3 ejercicio_3.py --archivo archivos/corpus.txt
    python3 ejercicio_3.py                      # pide la ruta por teclado
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path
import numpy as np

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #
DIR_SCRIPT = Path(__file__).resolve().parent      # salida/ se ubica SIEMPRE junto al script
DIR_SALIDA = DIR_SCRIPT / "salida"
MAX_ENTROPIA = 8.0        # log2(256) bits/byte
TAM_CHUNK = 1 << 20       # 1 MiB por lectura al contar frecuencias


class ErrorEntrada(Exception):
    """Entrada inválida del usuario (ruta o archivo)."""


def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    try:
        ruta = resolver_ruta(args.archivo, "archivo")
        validar_archivo(ruta)
        print("[1/4] Validando archivo...")
        print(f"      Archivo: {ruta}  ({ruta.stat().st_size} bytes, "
              f"{ruta.stat().st_size / 1048576:.2f} MiB)")

        print("[2/4] Leyendo el archivo byte a byte en O(N) y calculando "
              "la distribución de probabilidad (256 símbolos)...")
        t0 = time.perf_counter()
        conteos = contar_bytes(ruta)
        t1 = time.perf_counter()
        prob = a_probabilidades(conteos)
        print(f"      {int(conteos.sum())} bytes leídos en {t1 - t0:.4f} s "
              f"({simbolos_distintos(conteos)} símbolos distintos de 256)")

        print("[3/4] Calculando entropía empírica H(S) = -Σ p(i)·log2(p(i))...")
        h = entropia_shannon(prob)
        r = redundancia(h)
        print(f"      H = {h:.4f} bits/byte (máximo {MAX_ENTROPIA:.4f}) "
              f"| redundancia {r * 100:.2f} %")

        print("[4/4] Generando resumen...")
        texto = resumen(ruta, conteos, h)
        print(texto)
        DIR_SALIDA.mkdir(parents=True, exist_ok=True)
        ruta_resumen = DIR_SALIDA / f"resumen_{ruta.name}.txt"
        ruta_resumen.write_text(texto + "\n", encoding="utf-8")
        print(f"Salida guardada: {ruta_resumen}")
    except ErrorEntrada as e:
        print(f"ERROR: {e}", file=sys.stderr); return 1
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr); return 1
    return 0


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejercicio 3 — Entropía empírica en archivos (texto vs. "
                     "comprimidos): frecuencia relativa de bytes, entropía "
                     "de Shannon y redundancia de un archivo arbitrario.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--archivo", type=str, default=None,
        help="Ruta del archivo a analizar (cualquier tipo). Si se omite, "
             "se solicita por teclado.",
    )
    return parser.parse_args(argv)


def resolver_ruta(ruta: str | None, etiqueta: str) -> Path:
    if ruta is None:
        ruta = input(f"Ruta del {etiqueta}: ")
        while not ruta.strip():
            ruta = input(f"Ruta del {etiqueta}: ")
    return Path(os.path.expanduser(ruta))


# --------------------------------------------------------------------------- #
# Paso 3 — Validación (sin extensión: archivo arbitrario)
# --------------------------------------------------------------------------- #
def validar_archivo(ruta: Path) -> None:
    if not ruta.is_file():
        raise ErrorEntrada(f"No existe el archivo: {ruta}")
    if ruta.stat().st_size == 0:
        raise ErrorEntrada(f"El archivo está vacío: {ruta}")


# --------------------------------------------------------------------------- #
# Paso 4 — Distribución de probabilidad
# --------------------------------------------------------------------------- #
def contar_bytes(ruta: Path) -> np.ndarray:
    conteos = np.zeros(256, dtype=np.int64)
    try:
        with open(ruta, "rb") as f:
            while True:
                bloque = f.read(TAM_CHUNK)
                if not bloque:
                    break
                conteos += np.bincount(np.frombuffer(bloque, dtype=np.uint8), minlength=256)
    except OSError as e:
        raise ErrorEntrada(f"No se pudo leer {ruta}: {e}") from e
    return conteos


def a_probabilidades(conteos: np.ndarray) -> np.ndarray:
    total = int(conteos.sum())
    if total == 0:
        raise ErrorEntrada("No hay datos para calcular la distribución.")
    return conteos.astype(np.float64) / total


def simbolos_distintos(conteos: np.ndarray) -> int:
    return int((conteos > 0).sum())


# --------------------------------------------------------------------------- #
# Paso 5 — Entropía empírica de Shannon
# --------------------------------------------------------------------------- #
def entropia_shannon(prob: np.ndarray) -> float:
    # H(S) = -Σ p(i)·log2(p(i)); convención 0·log2(0) = 0.
    p = prob[prob > 0]
    return float(-(p * np.log2(p)).sum())


def redundancia(h: float) -> float:
    return 1.0 - h / MAX_ENTROPIA


# --------------------------------------------------------------------------- #
# Paso 6 — Resumen final: consola + salida/resumen_<nombre>.txt
# --------------------------------------------------------------------------- #
def top_bytes(conteos: np.ndarray, n: int = 5) -> list[tuple[int, int]]:
    valores = sorted(range(256), key=lambda v: (-int(conteos[v]), v))[:n]
    return [(v, int(conteos[v])) for v in valores]


def resumen(ruta: Path, conteos: np.ndarray, h: float) -> str:
    tam = ruta.stat().st_size
    simb = simbolos_distintos(conteos)
    r = redundancia(h)
    total = int(conteos.sum())
    top_txt = ", ".join(f"0x{v:02X}: {(c / total) * 100:.2f}%" for v, c in top_bytes(conteos))

    return (
        "================ RESUMEN (Ejercicio 3) ================\n"
        f"Archivo             : {ruta}\n"
        f"   tamaño            : {tam} bytes ({tam / 1048576:.2f} MiB)\n"
        f"   símbolos distintos: {simb}/256\n"
        f"   entropía empírica : {h:.4f} bits/byte   (máximo teórico 8.0000)\n"
        f"   redundancia       : {r * 100:.2f} %\n"
        f"   bytes más frecuentes: {top_txt}\n"
        "======================================================="
    )


if __name__ == "__main__":
    sys.exit(main())
