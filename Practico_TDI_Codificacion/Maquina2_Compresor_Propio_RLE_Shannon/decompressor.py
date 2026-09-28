#!/usr/bin/env python3
"""Descompresor propio RLE + Shannon (Práctico de Máquina 2).

Uso:
    python decompressor.py salida.tdi reconstruido.txt

Lee únicamente el archivo ``.tdi`` (no depende del archivo original en
tiempo de ejecución), reconstruye los bytes originales y valida la
integridad comparando SHA-256(reconstruido) contra el hash guardado en la
cabecera del ``.tdi``.

Códigos de salida:
    0  éxito, integridad OK
    1  error de uso / lectura / escritura / compresión
    2  cabecera inválida o incompatible
    3  datos insuficientes para completar la decodificación (archivo truncado)
    4  se pudo decodificar pero la verificación de integridad SHA-256 falló
"""

from __future__ import annotations

import hashlib
import sys
import time

import tdi_format


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Uso: python decompressor.py <entrada.tdi> <salida>", file=sys.stderr)
        return 1

    input_path, output_path = argv[1], argv[2]

    try:
        with open(input_path, "rb") as f:
            tdi_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{input_path}'.", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error al leer '{input_path}': {exc}", file=sys.stderr)
        return 1

    start = time.perf_counter()
    try:
        data, header = tdi_format.decode(tdi_bytes)
    except tdi_format.InvalidHeaderError as exc:
        print(f"Error: cabecera inválida ({exc}).", file=sys.stderr)
        return 2
    except tdi_format.InsufficientDataError as exc:
        print(f"Error: datos insuficientes para completar la decodificación ({exc}).", file=sys.stderr)
        return 3
    except Exception as exc:  # defensivo: nunca queremos un traceback crudo
        print(f"Error durante la descompresión: {exc}", file=sys.stderr)
        return 1
    elapsed_ms = (time.perf_counter() - start) * 1000

    try:
        with open(output_path, "wb") as f:
            f.write(data)
    except OSError as exc:
        print(f"Error al escribir '{output_path}': {exc}", file=sys.stderr)
        return 1

    sha256_reconstructed = hashlib.sha256(data).digest()
    integrity_ok = sha256_reconstructed == header.sha256_original

    print(f"Entrada:  {input_path}")
    print(f"Salida:   {output_path}")
    print(f"Tamaño reconstruido: {len(data)} bytes")
    print(f"Tiempo de descompresión: {elapsed_ms:.3f} ms")
    print(f"Integridad: {'OK' if integrity_ok else 'FALLÓ'}")

    return 0 if integrity_ok else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv))
