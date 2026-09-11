#!/usr/bin/env python3
"""Ejercicio 4 — Índice de Coincidencia (IC).

Calcula IC = Σf_i(f_i-1) / (N(N-1)) sobre los mismos archivos del
Ejercicio 3, en dos alfabetos: bytes (k=256) y letras españolas (k=27).

Uso:
    python3 ejercicio_4.py --archivo ../ejercicio_3/archivos/corpus.txt
    python3 ejercicio_4.py                      # pide la ruta por teclado
"""
from __future__ import annotations
import argparse
import os
import sys
import unicodedata
from pathlib import Path
import numpy as np

# --------------------------------------------------------------------------- #
# Paso 1 — Constantes
# --------------------------------------------------------------------------- #
DIR_SCRIPT = Path(__file__).resolve().parent      # salida/ se ubica SIEMPRE junto al script
DIR_SALIDA = DIR_SCRIPT / "salida"
TAM_CHUNK = 1 << 20                                # 1 MiB por lectura al contar frecuencias
MAX_ENTROPIA_BYTES = 8.0                           # log2(256)
LETRAS = "abcdefghijklmnñopqrstuvwxyz"              # alfabeto español de 27 letras
MAX_ENTROPIA_LETRAS = float(np.log2(len(LETRAS)))  # log2(27) ≈ 4.7549
IC_REF_ESPANOL = 0.074
IC_REF_ALEATORIO_27 = 0.038                        # ≈ 1/27


class ErrorEntrada(Exception):
    """Entrada inválida del usuario (ruta o archivo)."""


def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    try:
        ruta = resolver_ruta(args.archivo, "archivo")
        validar_archivo(ruta)
        print("[1/5] Validando archivo...")
        print(f"      Archivo: {ruta}  ({ruta.stat().st_size} bytes)")

        print("[2/5] Calculando distribución sobre el alfabeto de bytes (256 símbolos, "
              "igual que en el Ejercicio 3)...")
        conteos_bytes = contar_bytes(ruta)
        prob_bytes = a_probabilidades(conteos_bytes)
        h_bytes = entropia_shannon(prob_bytes)
        ic_bytes = calcular_ic(conteos_bytes)
        print(f"      {int(conteos_bytes.sum())} bytes, {simbolos_distintos(conteos_bytes)} símbolos "
              f"distintos, H = {h_bytes:.4f} bits/símbolo, IC = {ic_bytes:.6f}")

        print("[3/5] Extrayendo letras (alfabeto español de 27 letras: a-z, ñ)...")
        conteos_letras, codificacion, n_letras, n_total = extraer_conteos_letras(ruta)
        cobertura = n_letras / n_total if n_total else 0.0
        print(f"      Decodificado como {codificacion}: {n_letras} letras de {n_total} bytes "
              f"({cobertura * 100:.2f} % del archivo)")

        print("[4/5] Calculando entropía e IC sobre el alfabeto de 27 letras...")
        if n_letras >= 2:
            prob_letras = a_probabilidades(conteos_letras)
            h_letras = entropia_shannon(prob_letras)
            ic_letras = calcular_ic(conteos_letras)
            print(f"      H = {h_letras:.4f} bits/símbolo (máximo {MAX_ENTROPIA_LETRAS:.4f}), "
                  f"IC = {ic_letras:.6f}  (referencia: ~{IC_REF_ESPANOL} español real, "
                  f"~{IC_REF_ALEATORIO_27} alfabeto aleatorio de 27 letras)")
        else:
            h_letras = ic_letras = None
            print("      No hay letras suficientes en el archivo para calcular IC/H sobre este alfabeto.")

        print("[5/5] Generando resumen...")
        texto = resumen(ruta, conteos_bytes, h_bytes, ic_bytes,
                        n_letras, n_total, codificacion, h_letras, ic_letras)
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
        description="Ejercicio 4 — Índice de Coincidencia (IC): calcula el IC de "
                     "los mismos archivos a los que se les calculó la Entropía en "
                     "el Ejercicio 3, y compara Entropía vs. IC.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--archivo", type=str, default=None,
        help="Ruta del archivo a analizar (el mismo que se usó para la Entropía "
             "en el Ejercicio 3). Si se omite, se solicita por teclado.",
    )
    return parser.parse_args(argv)


def resolver_ruta(ruta: str | None, etiqueta: str) -> Path:
    if ruta is None:
        ruta = input(f"Ruta del {etiqueta}: ")
        while not ruta.strip():
            ruta = input(f"Ruta del {etiqueta}: ")
    return Path(os.path.expanduser(ruta))


def validar_archivo(ruta: Path) -> None:
    if not ruta.is_file():
        raise ErrorEntrada(f"No existe el archivo: {ruta}")
    if ruta.stat().st_size == 0:
        raise ErrorEntrada(f"El archivo está vacío: {ruta}")


# --------------------------------------------------------------------------- #
# Paso 2 — Distribución sobre bytes (reutilizado literal de ejercicio_3.py)
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


def entropia_shannon(prob: np.ndarray) -> float:
    # H(S) = -Σ p(i)·log2(p(i)); convención 0·log2(0) = 0.
    p = prob[prob > 0]
    return float(-(p * np.log2(p)).sum())


# --------------------------------------------------------------------------- #
# Paso 3 — Índice de Coincidencia (función genérica, cualquier alfabeto)
# --------------------------------------------------------------------------- #
def calcular_ic(conteos: np.ndarray) -> float:
    """IC = Σ f_i·(f_i - 1) / (N·(N - 1)); genérica para cualquier alfabeto."""
    n = int(conteos.sum())
    if n < 2:
        raise ErrorEntrada("Se necesitan al menos 2 símbolos para calcular el IC.")
    conteos = conteos.astype(np.float64)
    numerador = float((conteos * (conteos - 1)).sum())
    return numerador / (n * (n - 1))


# --------------------------------------------------------------------------- #
# Paso 4 — Extracción del alfabeto de 27 letras españolas
# --------------------------------------------------------------------------- #
def extraer_conteos_letras(ruta: Path) -> tuple[np.ndarray, str, int, int]:
    """Devuelve (conteos[27], nombre_codificacion_usada, letras_encontradas, bytes_totales)."""
    datos = ruta.read_bytes()
    try:
        texto = datos.decode("utf-8")
        codificacion = "UTF-8"
    except UnicodeDecodeError:
        texto = datos.decode("latin-1")   # nunca falla: mapeo 1 a 1 de byte a código de punto
        codificacion = "Latin-1 (el archivo no decodificó como UTF-8 válido)"

    indice = {c: i for i, c in enumerate(LETRAS)}
    conteos = np.zeros(len(LETRAS), dtype=np.int64)
    letras_normalizadas: list[str] = []
    for ch in unicodedata.normalize("NFD", texto.lower()):
        if ch == "̃" and letras_normalizadas and letras_normalizadas[-1] == "n":
            letras_normalizadas[-1] = "ñ"          # 'n' + tilde combinante -> 'ñ'
            continue
        if unicodedata.combining(ch):
            continue                                # descarta otros acentos: á->a, é->e, ...
        letras_normalizadas.append(ch)

    for ch in letras_normalizadas:
        i = indice.get(ch)
        if i is not None:
            conteos[i] += 1

    return conteos, codificacion, int(conteos.sum()), len(datos)


# --------------------------------------------------------------------------- #
# Paso 5 — Resumen final: consola + salida/resumen_<nombre>.txt
# --------------------------------------------------------------------------- #
def top_bytes(conteos: np.ndarray, n: int = 5) -> list[tuple[int, int]]:
    valores = sorted(range(256), key=lambda v: (-int(conteos[v]), v))[:n]
    return [(v, int(conteos[v])) for v in valores]


def resumen(ruta: Path, conteos_bytes: np.ndarray, h_bytes: float, ic_bytes: float,
            n_letras: int, n_total: int, codificacion: str,
            h_letras: float | None, ic_letras: float | None) -> str:
    tam = ruta.stat().st_size
    simb = simbolos_distintos(conteos_bytes)
    total_bytes = int(conteos_bytes.sum())
    top_txt = ", ".join(
        f"0x{v:02X}: {(c / total_bytes) * 100:.2f}%" for v, c in top_bytes(conteos_bytes)
    )
    cobertura = n_letras / n_total if n_total else 0.0

    if n_letras >= 2:
        bloque_letras = (
            f"   entropía H         : {h_letras:.4f} bits/símbolo   (máximo teórico {MAX_ENTROPIA_LETRAS:.4f})\n"
            f"   índice de coincidencia IC : {ic_letras:.6f}   (referencia: ~{IC_REF_ESPANOL} español real, "
            f"~{IC_REF_ALEATORIO_27} alfabeto aleatorio de 27 letras)"
        )
    else:
        bloque_letras = "   No hay letras suficientes en el archivo para este análisis."

    return (
        "================ RESUMEN (Ejercicio 4) ================\n"
        f"Archivo              : {ruta}\n"
        f"   tamaño             : {tam} bytes ({tam / 1048576:.2f} MiB)\n"
        "\n"
        "   -- Alfabeto de bytes (256 símbolos, igual que la Entropía del Ejercicio 3) --\n"
        f"   símbolos distintos : {simb}/256\n"
        f"   entropía H         : {h_bytes:.4f} bits/símbolo   (máximo teórico 8.0000)\n"
        f"   índice de coincidencia IC : {ic_bytes:.6f}   (mínimo teórico si fuera uniforme: 1/256 = 0.003906)\n"
        f"   bytes más frecuentes: {top_txt}\n"
        "\n"
        f"   -- Alfabeto de 27 letras españolas (a-z, ñ), decodificado como {codificacion} --\n"
        f"   letras encontradas : {n_letras}/{n_total} bytes ({cobertura * 100:.2f} % del archivo)\n"
        f"{bloque_letras}\n"
        "======================================================="
    )


if __name__ == "__main__":
    sys.exit(main())
