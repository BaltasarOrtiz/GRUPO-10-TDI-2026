#!/usr/bin/env python3
"""Compresor propio RLE + Shannon (Práctico de Máquina 2).

Uso:
    python compressor.py entrada.txt salida.tdi

Lee ``entrada.txt`` en modo binario, aplica RLE seguido de codificación
Shannon canónica (independiente para el stream de símbolos y el de
longitudes de racha) y escribe el resultado en ``salida.tdi``. El archivo
``.tdi`` es autocontenido: no depende del archivo original para poder
descomprimirse (ver ``decompressor.py``).

Solo usa la biblioteca estándar de Python. El núcleo del algoritmo vive en
``tdi_format.py``, en esta misma carpeta.
"""

from __future__ import annotations

import sys
import time

import tdi_format


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Uso: python compressor.py <entrada> <salida.tdi>", file=sys.stderr)
        return 1

    input_path, output_path = argv[1], argv[2]

    try:
        with open(input_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo de entrada '{input_path}'.", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error al leer '{input_path}': {exc}", file=sys.stderr)
        return 1

    start = time.perf_counter()
    try:
        tdi_bytes = tdi_format.encode(data)
    except Exception as exc:  # defensivo: nunca queremos un traceback crudo
        print(f"Error durante la compresión: {exc}", file=sys.stderr)
        return 1
    elapsed_ms = (time.perf_counter() - start) * 1000

    try:
        with open(output_path, "wb") as f:
            f.write(tdi_bytes)
    except OSError as exc:
        print(f"Error al escribir '{output_path}': {exc}", file=sys.stderr)
        return 1

    original_size = len(data)
    compressed_size = len(tdi_bytes)

    print(f"Entrada:  {input_path}")
    print(f"Salida:   {output_path}")
    print(f"Tamaño original:   {original_size} bytes")
    print(f"Tamaño comprimido: {compressed_size} bytes")
    if original_size > 0:
        ratio = original_size / compressed_size
        saved = (1 - compressed_size / original_size) * 100
        print(f"Ratio de compresión (R = original/comprimido): {ratio:.4f}")
        print(f"Espacio ahorrado (A): {saved:.2f}%")
    else:
        print("Ratio de compresión (R): N/A (archivo de entrada vacío)")
    print(f"Tiempo de compresión: {elapsed_ms:.3f} ms")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
