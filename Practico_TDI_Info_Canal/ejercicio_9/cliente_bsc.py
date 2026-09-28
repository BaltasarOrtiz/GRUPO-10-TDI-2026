#!/usr/bin/env python3
"""Ejercicio 9 — Cliente del Canal Binario Simétrico (BSC) por sockets TCP.

Fase 1: mide el BER empírico con tramas de 100 / 10.000 / 1.000.000 de bits
y pasa una frase por el canal. Fase 2: modela el canal como BSC (matriz
P(Y|X), I(X;Y), Capacidad C = 1 - H(p)) usando el BER como estimación de p.
"""

from __future__ import annotations

import argparse
import math
import random
import socket
import struct
import sys


class ErrorEntrada(Exception):
    pass


# ============================================================
# CONSTANTES
# ============================================================
HOST_DEFECTO = "127.0.0.1"
PUERTO_DEFECTO = 5555
TAMANIOS_PRUEBA = [100, 10_000, 1_000_000]   # los mismos del enunciado
FRASE_DEMO = "Teoria de la Informacion"        # solo ASCII (ver texto_a_binario, 8 bits por caracter)


# ============================================================
# PROTOCOLO DE RED (idéntico al del servidor)
# ============================================================
def recibir_exactamente(sock: socket.socket, cantidad: int) -> bytes:
    datos = bytearray()
    while len(datos) < cantidad:
        bloque = sock.recv(cantidad - len(datos))
        if not bloque:
            raise ErrorEntrada("Conexión cerrada por el servidor de forma inesperada.")
        datos.extend(bloque)
    return bytes(datos)


def recibir_mensaje(sock: socket.socket) -> str:
    encabezado = recibir_exactamente(sock, 4)
    longitud = struct.unpack("!I", encabezado)[0]
    datos = recibir_exactamente(sock, longitud)
    return datos.decode("ascii")


def enviar_mensaje(sock: socket.socket, mensaje: str) -> None:
    datos = mensaje.encode("ascii")
    encabezado = struct.pack("!I", len(datos))
    sock.sendall(encabezado + datos)


def conectar(host: str, puerto: int) -> socket.socket:
    try:
        sock = socket.create_connection((host, puerto), timeout=10)
    except OSError as e:
        raise ErrorEntrada(
            f"No se pudo conectar a {host}:{puerto} -- ¿está corriendo servidor_bsc.py? ({e})"
        )
    return sock


# ============================================================
# FASE 1: generación de tramas, envío y BER empírico
# ============================================================
def generar_trama_aleatoria(n: int, rng: random.Random) -> str:
    return "".join(rng.choice("01") for _ in range(n))


def contar_errores(original: str, recibida: str) -> int:
    return sum(1 for a, b in zip(original, recibida) if a != b)


def medir_ber(sock: socket.socket, n: int, rng: random.Random) -> dict:
    trama = generar_trama_aleatoria(n, rng)
    enviar_mensaje(sock, trama)
    recibida = recibir_mensaje(sock)
    if len(recibida) != n:
        raise ErrorEntrada(f"El servidor devolvió {len(recibida)} bits, se esperaban {n}.")
    errores = contar_errores(trama, recibida)
    ber = errores / n
    return {"n": n, "trama": trama, "recibida": recibida, "errores": errores, "ber": ber}


# ============================================================
# FASE 1, punto 5: mensaje de texto a través del canal
# ============================================================
def texto_a_binario(texto: str) -> str:
    """Cada caracter -> 8 bits (ASCII, ord(c) < 256)."""
    for c in texto:
        if ord(c) > 255:
            raise ErrorEntrada(f"Caracter fuera de rango de 1 byte para esta conversión simple: {c!r}")
    return "".join(format(ord(c), "08b") for c in texto)


def binario_a_texto(binario: str) -> str:
    """Inverso de texto_a_binario: agrupa de a 8 bits y los vuelve caracter."""
    caracteres = []
    for i in range(0, len(binario) - len(binario) % 8, 8):
        byte = binario[i:i + 8]
        caracteres.append(chr(int(byte, 2)))
    return "".join(caracteres)


# ============================================================
# FASE 2: matriz del canal, entropías e información mutua (BSC, 2x2)
# ============================================================
def entropia(probs: list[float]) -> float:
    return -sum(p * math.log2(p) for p in probs if p > 0)


def matriz_bsc(p: float) -> list[list[float]]:
    return [[1 - p, p], [p, 1 - p]]


def probabilidad_salida(p_x: list[float], matriz: list[list[float]]) -> list[float]:
    return [sum(p_x[i] * matriz[i][j] for i in range(2)) for j in range(2)]


def entropia_condicional(p_x: list[float], matriz: list[list[float]]) -> float:
    return sum(p_x[i] * entropia(matriz[i]) for i in range(2))


def informacion_mutua(p_x: list[float], matriz: list[list[float]]) -> tuple[float, float, float]:
    p_y = probabilidad_salida(p_x, matriz)
    h_y = entropia(p_y)
    h_y_dado_x = entropia_condicional(p_x, matriz)
    return h_y - h_y_dado_x, h_y, h_y_dado_x


def capacidad_bsc(p: float) -> float:
    """C = 1 - H(p)."""
    return 1.0 - entropia([p, 1 - p])


def probabilidades_entrada(trama: str) -> tuple[float, float]:
    n = len(trama)
    p0 = trama.count("0") / n
    return p0, 1.0 - p0


# ============================================================
# main(): orquesta Fase 1 y Fase 2
# ============================================================
def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    try:
        print("=== Fase 1: Transmisión y BER empírico ===\n")
        sock = conectar(args.host, args.puerto)
        rng = random.Random(args.semilla_cliente)   # semilla propia del cliente, ver parsear_argumentos

        resultados = []
        for i, n in enumerate(TAMANIOS_PRUEBA, start=1):
            print(f"Prueba {i}/{len(TAMANIOS_PRUEBA)}: trama de {n:,} bits".replace(",", "."))
            r = medir_ber(sock, n, rng)
            resultados.append(r)
            print(f"   Errores: {r['errores']}/{n}   BER empírico: {r['ber']:.6f}")

        print("\nConvergencia (Ley de los Grandes Números): a medida que crece N, el BER "
              "empírico se estabiliza cada vez más cerca de la probabilidad de error real "
              "del canal (la varianza del estimador decrece como 1/N); compárense los tres "
              "valores de arriba: deberían acercarse entre sí a medida que N crece.")

        print(f"\nMensaje de texto a través del canal (frase: {FRASE_DEMO!r})...")
        binario_frase = texto_a_binario(FRASE_DEMO)
        enviar_mensaje(sock, binario_frase)
        binario_recibido = recibir_mensaje(sock)
        texto_recibido = binario_a_texto(binario_recibido)
        print(f"   Original : {FRASE_DEMO!r}")
        print(f"   Recibido : {texto_recibido!r}")
        n_dist = sum(1 for a, b in zip(FRASE_DEMO, texto_recibido) if a != b)
        print(f"   Caracteres distintos: {n_dist}/{len(FRASE_DEMO)}")

        enviar_mensaje(sock, "SALIR")
        sock.close()

        print("\n=== Fase 2: Modelado matemático y Capacidad del Canal ===\n")
        prueba_grande = resultados[-1]     # la de 1.000.000 de bits: mejor estimación de p
        p = prueba_grande["ber"]
        print(f"Usando p = {p:.6f} (BER empírico de la prueba de {prueba_grande['n']:,} bits, "
              "la mejor estimación disponible por Ley de los Grandes Números) "
              "como probabilidad de error teórica del BSC.\n")

        matriz = matriz_bsc(p)
        print("1. Matriz del canal P(Y|X):")
        print(f"      Fila X=0: {matriz[0]}")
        print(f"      Fila X=1: {matriz[1]}")

        p0, p1 = probabilidades_entrada(prueba_grande["trama"])
        print(f"\n2. Probabilidades de entrada (trama de {prueba_grande['n']:,} bits enviada):")
        print(f"      P(X=0) = {p0:.6f}")
        print(f"      P(X=1) = {p1:.6f}")

        i_xy, h_y, h_y_dado_x = informacion_mutua([p0, p1], matriz)
        print(f"\n3. Información mutua de esta transmisión: I(X;Y) = {i_xy:.6f} bits/símbolo")
        print(f"      (H(Y) = {h_y:.6f}, H(Y|X) = {h_y_dado_x:.6f})")

        c = capacidad_bsc(p)
        print(f"\n4. Capacidad del canal: C = 1 - H(p) = {c:.6f} bits/símbolo")

        diferencia_relativa = abs(c - i_xy) / c if c > 0 else 0.0
        dentro_de_margen = diferencia_relativa <= 0.10
        print(f"\n5. Comparación: I(X;Y) = {i_xy:.6f}, C = {c:.6f}, "
              f"diferencia relativa = {diferencia_relativa * 100:.2f} %")
        print(f"      {'Dentro' if dentro_de_margen else 'Fuera'} del margen de 5-10 % del enunciado.")
        # En un BSC, H(Y|X) = H(p) sin importar P(X), asi que I(X;Y) se maximiza con
        # P(X=0)=P(X=1)=0.5. Una trama aleatoria equiprobable se acerca a ese optimo.
    except ErrorEntrada as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except (OSError, ConnectionError) as e:
        print(f"ERROR de red: {e}", file=sys.stderr)
        return 1
    return 0


def parsear_argumentos(argv):
    parser = argparse.ArgumentParser(description="Cliente del Canal Binario Simétrico (BSC).")
    parser.add_argument("--host", default=HOST_DEFECTO, help=f"Host del servidor (default: {HOST_DEFECTO}).")
    parser.add_argument("--puerto", type=int, default=PUERTO_DEFECTO, help=f"Puerto del servidor (default: {PUERTO_DEFECTO}).")
    parser.add_argument("--semilla-cliente", type=int, default=None, dest="semilla_cliente",
                         help="Semilla para las tramas aleatorias del cliente (default: no determinista, "
                              "usa entropía del sistema). Fijarla solo para reproducir un informe.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
