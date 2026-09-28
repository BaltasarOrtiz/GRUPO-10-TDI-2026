from __future__ import annotations

import argparse
import math
import sys


class ErrorEntrada(Exception):
    pass


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejercicio 8 — Capacidad de Canal por búsqueda exhaustiva (binario a cuaternario)."
    )
    parser.add_argument(
        "--matriz",
        type=str,
        default=None,
        help=(
            "Los 8 valores P(Y=j|X=i) separados por comas, fila por fila: "
            "p(Y0|X0),p(Y1|X0),p(Y2|X0),p(Y3|X0),p(Y0|X1),p(Y1|X1),p(Y2|X1),p(Y3|X1). "
            "Si se omite, se piden uno por uno por teclado."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Imprime las 101 iteraciones de la búsqueda exhaustiva "
            "(por defecto solo se muestra el resultado final)."
        ),
    )
    return parser.parse_args(argv)


def parsear_matriz_cli(texto: str) -> list[list[float]]:
    partes = [p.strip() for p in texto.split(",")]
    if len(partes) != 8:
        raise ErrorEntrada(f"Se esperaban 8 valores separados por coma, se recibieron {len(partes)}.")
    try:
        valores = [float(p) for p in partes]
    except ValueError as e:
        raise ErrorEntrada(f"Valor no numérico en la matriz: {e}")
    return [valores[0:4], valores[4:8]]


def pedir_matriz_interactiva() -> list[list[float]]:
    matriz = []
    for i in range(2):
        fila = []
        for j in range(4):
            texto = input(f"P(Y={j} | X={i}): ")
            try:
                fila.append(float(texto))
            except ValueError:
                raise ErrorEntrada(f"Valor no numérico para P(Y={j}|X={i}): {texto!r}")
        matriz.append(fila)
    return matriz


def validar_matriz(matriz: list[list[float]]) -> None:
    for i, fila in enumerate(matriz):
        for j, valor in enumerate(fila):
            if not (0.0 <= valor <= 1.0):
                raise ErrorEntrada(f"P(Y={j}|X={i}) = {valor} está fuera de [0, 1].")
        suma = sum(fila)
        if abs(suma - 1.0) > 1e-6:
            raise ErrorEntrada(
                f"La fila X={i} no suma 1 (suma = {suma:.6f}). Cada fila de P(Y|X) es una "
                f"distribución de probabilidad y debe sumar exactamente 1."
            )


def entropia(probs: list[float]) -> float:
    """H = -Sum p*log2(p), convencion 0*log2(0)=0. Generica: sirve para H(Y) y para H(Y|X=i)."""
    return -sum(p * math.log2(p) for p in probs if p > 0)


def probabilidad_salida(p_x: list[float], matriz: list[list[float]]) -> list[float]:
    """P(Y=j) = Sum_i P(X=i)*P(Y=j|X=i) -- Teorema de la Probabilidad Total."""
    return [sum(p_x[i] * matriz[i][j] for i in range(2)) for j in range(4)]


def entropia_condicional(p_x: list[float], matriz: list[list[float]]) -> float:
    """H(Y|X) = Sum_i P(X=i)*H(Y|X=i), con H(Y|X=i) = entropia de la fila i (ruido del canal)."""
    return sum(p_x[i] * entropia(matriz[i]) for i in range(2))


def informacion_mutua(p_x: list[float], matriz: list[list[float]]) -> tuple[float, float, float]:
    """Devuelve (I(X;Y), H(Y), H(Y|X)) para una distribucion de entrada p_x dada."""
    p_y = probabilidad_salida(p_x, matriz)
    h_y = entropia(p_y)
    h_y_dado_x = entropia_condicional(p_x, matriz)
    return h_y - h_y_dado_x, h_y, h_y_dado_x


def buscar_capacidad(matriz: list[list[float]], verbose: bool = False) -> dict:
    """Barre P(X=0) de 0.00 a 1.00 en pasos de 0.01 y se queda con el maximo de I(X;Y)
    (Capacidad del Canal C). Empate: se conserva el primer maximo encontrado."""
    mejor = None
    for paso in range(101):
        p0 = paso / 100
        p_x = [p0, 1.0 - p0]
        i_xy, h_y, h_y_dado_x = informacion_mutua(p_x, matriz)
        es_nuevo_maximo = mejor is None or i_xy > mejor["i_xy"]
        if verbose:
            marca = "  <-- nuevo maximo" if es_nuevo_maximo else ""
            print(f"      P(X=0)={p0:.2f}  H(Y)={h_y:.4f}  H(Y|X)={h_y_dado_x:.4f}  "
                  f"I(X;Y)={i_xy:.4f}{marca}")
        if es_nuevo_maximo:
            mejor = {"p0": p0, "p1": 1.0 - p0, "i_xy": i_xy, "h_y": h_y, "h_y_dado_x": h_y_dado_x}
    return mejor


def main(argv: list[str] | None = None) -> int:
    try:
        args = parsear_argumentos(argv)
        print("[1/4] Cargando matriz del canal P(Y|X) (2x4)...")
        matriz = parsear_matriz_cli(args.matriz) if args.matriz else pedir_matriz_interactiva()
        validar_matriz(matriz)
        for i, fila in enumerate(matriz):
            print(f"      Fila X={i}: {fila}  (suma = {sum(fila):.4f}, OK)")

        print("\n[2/4] Búsqueda exhaustiva de P(X=0) en pasos de 0.01 (101 iteraciones)...")
        mejor = buscar_capacidad(matriz, verbose=args.verbose)

        print("\n[3/4] Mejor punto encontrado:")
        print(f"      P(X=0) = {mejor['p0']:.2f}, P(X=1) = {mejor['p1']:.2f}")
        print(f"      H(Y)    = {mejor['h_y']:.4f} bits/símbolo")
        print(f"      H(Y|X)  = {mejor['h_y_dado_x']:.4f} bits/símbolo")
        print(f"      I(X;Y)  = {mejor['i_xy']:.4f} bits/símbolo   <- máximo (Capacidad de Canal C)")

        print("\n[4/4] Resultado final")
        print(f"      Capacidad del Canal C = {mejor['i_xy']:.4f} bits/símbolo")
        print(f"      Distribución óptima   : P(X=0) = {mejor['p0']:.2f}, P(X=1) = {mejor['p1']:.2f}")
    except ErrorEntrada as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
