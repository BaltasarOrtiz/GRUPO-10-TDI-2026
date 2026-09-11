"""Ejercicio 6 -- Distancia entre cadenas (Hamming / Levenshtein).

Sin argumentos corre la demo de los 3 casos del enunciado. Con --a/--b compara
dos cadenas propias.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata


class ErrorEntrada(Exception):
    """Entrada invalida provista por el usuario o incompatible con el algoritmo."""


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compara dos cadenas de texto con distancia de Hamming y de Levenshtein."
    )
    parser.add_argument(
        "--a",
        type=str,
        default=None,
        help="Primera cadena a comparar. Si se omite junto con --b, se corre la demo del enunciado.",
    )
    parser.add_argument(
        "--b",
        type=str,
        default=None,
        help="Segunda cadena a comparar.",
    )
    args = parser.parse_args(argv)
    if (args.a is None) != (args.b is None):
        raise ErrorEntrada(
            "Hay que pasar --a y --b juntos, o ninguna de las dos para correr la demo del enunciado."
        )
    return args


# --------------------------------------------------------------------------
# Paso 2 -- Distancia de Hamming
# --------------------------------------------------------------------------


def distancia_hamming(a: str, b: str) -> int:
    """Cuenta las posiciones en que a y b difieren. Solo definida para cadenas de igual longitud."""
    if len(a) != len(b):
        raise ErrorEntrada(
            f"Distancia de Hamming no aplicable: las cadenas tienen longitudes distintas "
            f"({len(a)} y {len(b)}). Un desfase (una letra de mas o de menos) desalinea todos "
            f"los caracteres siguientes; Hamming compara posicion a posicion y no tiene forma "
            f"de 'correr' el desfase, por eso ni siquiera esta definida en este caso."
        )
    return sum(1 for x, y in zip(a, b) if x != y)


# --------------------------------------------------------------------------
# Paso 3 -- Distancia de Levenshtein
# --------------------------------------------------------------------------


def distancia_levenshtein(a: str, b: str) -> int:
    """Minimo numero de inserciones/eliminaciones/sustituciones para transformar a en b.
    dp[i][j] = distancia entre a[:i] y b[:j]; dp[i][j] = dp[i-1][j-1] si a[i-1]==b[j-1],
    si no, 1 + min(dp[i-1][j] (eliminar), dp[i][j-1] (insertar), dp[i-1][j-1] (sustituir))."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    fila_anterior = list(range(m + 1))
    for i in range(1, n + 1):
        fila_actual = [i] + [0] * m
        for j in range(1, m + 1):
            costo_sustitucion = 0 if a[i - 1] == b[j - 1] else 1
            fila_actual[j] = min(
                fila_anterior[j] + 1,               # eliminar a[i-1]
                fila_actual[j - 1] + 1,              # insertar b[j-1]
                fila_anterior[j - 1] + costo_sustitucion,  # sustituir o coincidir
            )
        fila_anterior = fila_actual
    return fila_anterior[m]


# --------------------------------------------------------------------------
# Paso 4 -- Similitud normalizada y clasificacion (heuristica practica, punto d)
# --------------------------------------------------------------------------


def similitud(a: str, b: str) -> float:
    """1 - distancia/largo_max: 1.0 = identicas, 0.0 = totalmente distintas (cota inferior)."""
    largo_max = max(len(a), len(b))
    if largo_max == 0:
        return 1.0
    return 1.0 - distancia_levenshtein(a, b) / largo_max


def clasificar_similitud(pct: float) -> str:
    if pct >= 1.0:
        return "Identicas"
    if pct >= 0.85:
        return "Muy similares (probable error de tipeo/transcripcion)"
    if pct >= 0.50:
        return "Parcialmente similares"
    return "Distintas"


def normalizar(texto: str) -> str:
    """minusculas + sin acentos (NFD, descarta marcas combinantes)."""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", texto.lower())
        if not unicodedata.combining(ch)
    )


# --------------------------------------------------------------------------
# Paso 5 -- Demo del enunciado (modo sin argumentos)
# --------------------------------------------------------------------------


def _mostrar_par(a: str, b: str) -> None:
    print(f'  A: "{a}"  ({len(a)} caracteres)')
    print(f'  B: "{b}"  ({len(b)} caracteres)')


def ejecutar_demo() -> None:
    # Nombres sin tilde para evitar ambiguedad de codificacion en la comparacion.
    print("=== Ejercicio 6: Distancia entre cadenas ===\n")

    print("[Caso 1] Distancia de Hamming -- mismo largo, transposicion de dos letras")
    _mostrar_par("Juan Perez", "Jaun Perez")
    d = distancia_hamming("Juan Perez", "Jaun Perez")
    print(f"  Distancia de Hamming: {d}")
    print("  (difieren en los indices 1 y 2: 'u' vs 'a', 'a' vs 'u' -- un solo error de "
          "tipeo humano, el intercambio de dos letras adyacentes, ya se cuenta como 2 "
          "posiciones distintas)\n")

    print("[Caso 2] Distancia de Hamming -- cadenas de distinta longitud (desfase real)")
    _mostrar_par("Juan Perez", "Juann Perez")
    try:
        distancia_hamming("Juan Perez", "Juann Perez")
    except ErrorEntrada as e:
        print(f"  Distancia de Hamming: ERROR -- {e}")
    d_lev = distancia_levenshtein("Juan Perez", "Juann Perez")
    print(f"  Distancia de Levenshtein: {d_lev} (una sola insercion: la 'n' extra de 'Juann')")
    print("  Esto es lo que el enunciado pide demostrar: frente a un desfase de longitud, "
          "Hamming ni siquiera puede calcularse, mientras que Levenshtein sigue dando el "
          "resultado intuitivamente correcto.\n")

    print("[Caso 3] Distancia de Levenshtein -- nombre mal tipeado")
    _mostrar_par("Horacio Lopez", "Oracio Lopez")
    d = distancia_levenshtein("Horacio Lopez", "Oracio Lopez")
    pct = similitud("Horacio Lopez", "Oracio Lopez")
    print(f"  Distancia de Levenshtein: {d} (no es una sola eliminacion: al sacar la 'H' de "
          "'Horacio' queda 'oracio' en minuscula, pero el destino tiene 'Oracio' con mayuscula "
          "inicial -- son 2 operaciones: 1 eliminacion + 1 sustitucion de mayuscula/minuscula)")
    print(f"  Similitud normalizada: {pct * 100:.2f} %  -> {clasificar_similitud(pct)}")
    d_norm = distancia_levenshtein(normalizar("Horacio Lopez"), normalizar("Oracio Lopez"))
    print(f"  Tras normalizar (minusculas): distancia = {d_norm} (ahi si es 1 sola eliminacion; "
          "ver punto d) -- muestra por que normalizar antes de medir es util)\n")


# --------------------------------------------------------------------------
# Paso 6 -- Modo de comparacion personalizada (--a/--b)
# --------------------------------------------------------------------------


def ejecutar_comparacion(a: str, b: str) -> None:
    print("=== Comparacion personalizada ===\n")
    _mostrar_par(a, b)
    try:
        d_hamming = distancia_hamming(a, b)
        print(f"  Distancia de Hamming: {d_hamming}")
    except ErrorEntrada as e:
        print(f"  Distancia de Hamming: ERROR -- {e}")

    d_lev = distancia_levenshtein(a, b)
    pct = similitud(a, b)
    print(f"  Distancia de Levenshtein: {d_lev}")
    print(f"  Similitud normalizada: {pct * 100:.2f} %  -> {clasificar_similitud(pct)}")

    a_norm, b_norm = normalizar(a), normalizar(b)
    if (a_norm, b_norm) != (a, b):
        d_lev_norm = distancia_levenshtein(a_norm, b_norm)
        pct_norm = similitud(a_norm, b_norm)
        print(f"\n  Tras normalizar (minusculas, sin acentos): \"{a_norm}\" vs \"{b_norm}\"")
        print(f"  Distancia de Levenshtein (normalizada): {d_lev_norm}")
        print(f"  Similitud normalizada: {pct_norm * 100:.2f} %  -> {clasificar_similitud(pct_norm)}")


# --------------------------------------------------------------------------
# Paso 7 -- main
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    try:
        args = parsear_argumentos(argv)
        if args.a is None and args.b is None:
            ejecutar_demo()
        else:
            ejecutar_comparacion(args.a, args.b)
    except ErrorEntrada as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
