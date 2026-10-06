#!/usr/bin/env python3
"""Benchmark extra: ¿en qué tipo de datos rinde mejor RLE + Shannon?

Complementa a ``benchmark.py`` (corpus oficial de la cátedra) con un corpus
propio, generado de forma determinística (semillas fijas), pensado para
explorar los tipos de redundancia en los que el algoritmo propio se destaca:
rachas largas de bytes idénticos *sin* patrones que se repitan a distancia.

Genera los archivos en ``corpus_extra/`` y escribe los resultados en:

    results/benchmark_extra_resultados.csv   una fila por (archivo, algoritmo)
    results/benchmark_extra_resumen.md       tabla resumida e interpretación

Uso:
    python3 Practico_TDI_Codificacion/benchmark_extra.py

Las mediciones reutilizan exactamente las mismas funciones de ``benchmark.py``
(mismas tres soluciones: propio, ``xz -6`` y ``gzip -n -6``, misma validación
SHA-256). Estos archivos NO forman parte del corpus oficial ni del ranking de
la cátedra: son una prueba adicional del grupo.

Solo usa la biblioteca estándar (las imágenes BMP se escriben a mano).
"""

from __future__ import annotations

import csv
import math
import random
import struct
import sys
from pathlib import Path

import benchmark

HERE = Path(__file__).resolve().parent
EXTRA_DIR = HERE / "corpus_extra"
RESULTS_DIR = HERE / "results"

SIZE = 1024 * 1024  # 1 MiB, tamaño recomendado por el enunciado para las pruebas de rendimiento
IMG_SIDE = 1024  # imágenes de 1024 x 1024 píxeles, 1 byte por píxel (~1 MiB)

BLACK, WHITE = 0, 255


# --------------------------------------------------------------------------
# Generadores (todos determinísticos)
# --------------------------------------------------------------------------


def random_runs(symbols: bytes, min_run: int, max_run: int, seed: int) -> bytes:
    """Rachas de símbolo y largo aleatorios: hay rachas, pero ningún patrón se repite."""
    rng = random.Random(seed)
    out = bytearray()
    while len(out) < SIZE:
        out += bytes([rng.choice(symbols)]) * rng.randint(min_run, max_run)
    return bytes(out[:SIZE])


def gen_senal_digital() -> bytes:
    return random_runs(bytes([0x00, 0xFF]), 1, 200, seed=7)


def gen_disperso() -> bytes:
    rng = random.Random(4)
    data = bytearray(SIZE)
    for _ in range(SIZE // 200):
        data[rng.randrange(SIZE)] = rng.randrange(1, 256)
    return bytes(data)


def gen_estados() -> bytes:
    return random_runs(b"ABCD", 1, 40, seed=6)


def gen_sensor() -> bytes:
    rng = random.Random(3)
    out = bytearray()
    value = 100
    while len(out) < SIZE:
        value = max(0, min(255, value + rng.randint(-3, 3)))
        out += bytes([value]) * rng.randint(5, 60)
    return bytes(out[:SIZE])


def gen_audio_silencios() -> bytes:
    rng = random.Random(5)
    out = bytearray()
    while len(out) < SIZE:
        if rng.random() < 0.5:
            out += bytes([128]) * rng.randint(2000, 20000)  # silencio (PCM 8 bits sin signo)
        else:
            n = rng.randint(1000, 5000)
            out += bytes(128 + int(60 * math.sin(i / 7)) + rng.randint(-20, 20) for i in range(n))
    return bytes(out[:SIZE])


def gen_texto_relleno() -> bytes:
    rng = random.Random(9)
    lines = []
    total = 0
    while total < SIZE:
        line = f"{rng.randrange(10**5):<10}{' ' * rng.randint(5, 30)}{rng.choice(['OK', 'ERROR', 'WARN'])}"
        line = line.ljust(79) + "\n"
        lines.append(line)
        total += len(line)
    return "".join(lines).encode("ascii")[:SIZE]


# --- imágenes BMP en escala de grises de 8 bits, en blanco y negro ---


def _fill_ellipse(pixels: bytearray, cx: float, cy: float, rx: float, ry: float, color: int) -> None:
    for y in range(max(0, int(cy - ry)), min(IMG_SIDE, int(cy + ry) + 1)):
        dy = (y - cy) / ry
        if abs(dy) > 1:
            continue
        half = rx * math.sqrt(1 - dy * dy)
        x0, x1 = max(0, int(cx - half)), min(IMG_SIDE, int(cx + half) + 1)
        if x1 > x0:
            pixels[y * IMG_SIDE + x0 : y * IMG_SIDE + x1] = bytes([color]) * (x1 - x0)


def _fill_rect(pixels: bytearray, x0: int, y0: int, x1: int, y1: int, color: int) -> None:
    for y in range(y0, y1):
        pixels[y * IMG_SIDE + x0 : y * IMG_SIDE + x1] = bytes([color]) * (x1 - x0)


def _to_bmp(pixels: bytearray) -> bytes:
    """BMP de 8 bits con paleta de grises; filas de abajo hacia arriba (1024 ya es múltiplo de 4)."""
    palette = b"".join(bytes([i, i, i, 0]) for i in range(256))
    offset = 14 + 40 + len(palette)
    file_header = struct.pack("<2sIHHI", b"BM", offset + len(pixels), 0, 0, offset)
    info_header = struct.pack("<IiiHHIIiiII", 40, IMG_SIDE, IMG_SIDE, 1, 8, 0, len(pixels), 2835, 2835, 256, 0)
    rows = [pixels[y * IMG_SIDE : (y + 1) * IMG_SIDE] for y in range(IMG_SIDE)]
    return file_header + info_header + palette + b"".join(reversed(rows))


def gen_mascara_bn() -> bytes:
    rng = random.Random(8)
    pixels = bytearray([BLACK]) * (IMG_SIDE * IMG_SIDE)
    for _ in range(60):
        _fill_ellipse(pixels, rng.randrange(IMG_SIDE), rng.randrange(IMG_SIDE),
                      rng.randrange(10, 75), rng.randrange(10, 75), WHITE)
    return _to_bmp(pixels)


def gen_logo_bn() -> bytes:
    pixels = bytearray([WHITE]) * (IMG_SIDE * IMG_SIDE)
    _fill_ellipse(pixels, 512, 420, 320, 320, BLACK)
    _fill_rect(pixels, 384, 292, 640, 548, WHITE)
    _fill_rect(pixels, 128, 800, 896, 950, BLACK)
    return _to_bmp(pixels)


# (archivo, descripción, ejemplo real, generador)
EXTRA_FILES = [
    ("extra_1_senal_digital.bin", "Señal digital de 2 niveles", "bits de un canal, línea B/N de un fax", gen_senal_digital),
    ("extra_2_disperso.bin", "Archivo disperso (99,5 % ceros)", "matriz dispersa, disco casi vacío", gen_disperso),
    ("extra_3_estados.txt", "Registro de estados (4 valores)", "estado de una máquina muestreado", gen_estados),
    ("extra_4_mascara_bn.bmp", "Imagen B/N con manchas", "máscara, plano escaneado", gen_mascara_bn),
    ("extra_5_logo_bn.bmp", "Imagen B/N tipo logo", "logo, ícono, dibujo simple", gen_logo_bn),
    ("extra_6_sensor.bin", "Sensor que mantiene su valor", "temperatura, nivel de un tanque", gen_sensor),
    ("extra_7_audio_silencios.raw", "Audio 8 bits con silencios", "grabación de voz con pausas", gen_audio_silencios),
    ("extra_8_texto_relleno.txt", "Texto de ancho fijo con relleno", "log o reporte tabulado", gen_texto_relleno),
]


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def veredicto(r_propio: float, r_xz: float, r_gzip: float) -> str:
    if r_propio > r_xz and r_propio > r_gzip:
        return "gana a xz y a gzip"
    if r_propio > r_gzip:
        return "gana a gzip"
    if r_propio > r_xz:
        return "gana a xz"
    return "pierde"


def main() -> int:
    EXTRA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for filename, _desc, _ejemplo, generator in EXTRA_FILES:
        data = generator()
        (EXTRA_DIR / filename).write_bytes(data)
        for algoritmo in ("propio", "xz-6", "gzip-6"):
            print(f"Corriendo {algoritmo} sobre {filename}...")
            row = benchmark.benchmark_one(filename, algoritmo, data)
            if not row["integridad_ok"]:
                print(f"  ADVERTENCIA: fallo de integridad SHA-256 para {algoritmo}/{filename}", file=sys.stderr)
            rows.append(row)

    # --- CSV (mismas columnas que benchmark_resultados.csv) ---
    csv_path = RESULTS_DIR / "benchmark_extra_resultados.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCSV escrito en {csv_path}")

    # --- resumen legible ---
    def ratio(archivo: str, algoritmo: str) -> float:
        return next(r["ratio_R"] for r in rows if r["archivo"] == archivo and r["algoritmo"] == algoritmo)

    lines = [
        "# Resumen del benchmark extra — ¿dónde rinde mejor RLE + Shannon?\n",
        "Corpus propio del grupo, generado con semillas fijas por `benchmark_extra.py` (ver "
        "[`../corpus_extra/README_extra.txt`](../corpus_extra/README_extra.txt)). **No forma parte del corpus "
        "oficial de la cátedra ni del ranking**: es una prueba adicional para identificar en qué tipo de datos "
        "se destaca el algoritmo propio. Mismas tres soluciones y misma medición que `benchmark.py`.\n",
        "## Ratio de compresión R por archivo\n",
        "| Tipo de dato | Ejemplo real | Propio | xz-6 | gzip-6 | Propio vs. resto |",
        "|---|---|---:|---:|---:|---|",
    ]
    for filename, desc, ejemplo, _gen in EXTRA_FILES:
        rp, rx, rg = ratio(filename, "propio"), ratio(filename, "xz-6"), ratio(filename, "gzip-6")
        lines.append(f"| {desc} | {ejemplo} | {rp:.2f} | {rx:.2f} | {rg:.2f} | {veredicto(rp, rx, rg)} |")

    all_ok = all(r["integridad_ok"] for r in rows)
    lines += [
        "",
        f"Integridad SHA-256: {'OK en todas las filas' if all_ok else 'FALLÓ en al menos una fila'} "
        f"({len(rows)} = 3 soluciones × {len(EXTRA_FILES)} archivos). Detalle completo (tamaños, tiempos, "
        "throughput) en `benchmark_extra_resultados.csv`.\n",
        "## Interpretación\n",
        "El algoritmo propio supera a gzip-6 (y en algunos casos también a xz-6) cuando el archivo tiene "
        "**rachas largas de bytes idénticos cuyo largo y orden no siguen un patrón que se repita**. "
        "xz y gzip comprimen buscando secuencias que ya aparecieron antes en el archivo (diccionario LZ); "
        "si las rachas tienen largos aleatorios, casi nunca encuentran una copia exacta y cada racha les "
        "cuesta una referencia nueva. RLE, en cambio, no necesita que nada se repita: cada racha se guarda "
        "como (símbolo, largo) y Shannon asigna códigos cortos a los símbolos y largos más frecuentes.",
        "",
        "Cuando los datos tienen poca racha y mucha repetición a distancia (audio con forma de onda, texto "
        "con columnas y palabras que se repiten), la ventaja vuelve a ser de xz y gzip, igual que en el "
        "corpus oficial. Es el mismo principio que usa el fax (RLE + código de longitud variable) para "
        "documentos en blanco y negro.",
        "",
    ]
    summary_path = RESULTS_DIR / "benchmark_extra_resumen.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Resumen escrito en {summary_path}\n")
    print("\n".join(lines[5 : 5 + len(EXTRA_FILES) + 1]))

    if not all_ok:
        print("\nATENCIÓN: hubo fallos de integridad SHA-256.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
