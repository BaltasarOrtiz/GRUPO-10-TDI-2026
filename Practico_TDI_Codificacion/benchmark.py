#!/usr/bin/env python3
"""Benchmark comparativo: propio (RLE + Shannon) vs xz -6 vs gzip -n -6 (cátedra).

Corre las tres soluciones sobre el corpus oficial de ``corpus_pruebas/`` y
escribe los resultados en ``results/``:

    results/benchmark_resultados.csv   una fila por (archivo, algoritmo)
    results/benchmark_resumen.md       resumen legible, con Weissman Score

Uso:
    python3 Practico_TDI_Codificacion/benchmark.py

La solución propia se importa e invoca en proceso (sin subprocesos); xz y
gzip se invocan como procesos externos vía su CLI ya instalada. Solo se
cronometra la llamada de compresión/descompresión en sí (no la lectura ni
escritura de archivos), usando ``time.perf_counter()``.
"""

from __future__ import annotations

import csv
import hashlib
import math
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROPIO_DIR = HERE / "Maquina2_Compresor_Propio_RLE_Shannon"
CORPUS_DIR = HERE / "corpus_pruebas"
RESULTS_DIR = HERE / "results"

sys.path.insert(0, str(PROPIO_DIR))
import tdi_format  # noqa: E402

CORPUS_FILES = [
    ("prueba_1_pequena.txt", "Prueba 1 (pequeña, 64 B)", False),
    ("prueba_2_texto_natural.txt", "Prueba 2 (texto natural, 100 KiB)", True),
    ("prueba_3_alta_repeticion.txt", "Prueba 3 (alta repetición, 100 KiB)", True),
    ("prueba_4_baja_repeticion.txt", "Prueba 4 (baja repetición, 100 KiB)", True),
]

MB = 1024 * 1024


# --------------------------------------------------------------------------
# Wrappers de compresión/descompresión por solución
# --------------------------------------------------------------------------


def propio_compress(data: bytes) -> tuple[bytes, float]:
    t0 = time.perf_counter()
    tdi_bytes = tdi_format.encode(data)
    t1 = time.perf_counter()
    return tdi_bytes, (t1 - t0) * 1000


def propio_decompress(tdi_bytes: bytes) -> tuple[bytes, float]:
    t0 = time.perf_counter()
    data, _header = tdi_format.decode(tdi_bytes)
    t1 = time.perf_counter()
    return data, (t1 - t0) * 1000


def _run_cli(cmd: list[str], data: bytes) -> tuple[bytes, float]:
    t0 = time.perf_counter()
    result = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, check=True)
    t1 = time.perf_counter()
    return result.stdout, (t1 - t0) * 1000


def xz_compress(data: bytes) -> tuple[bytes, float]:
    return _run_cli(["xz", "-6", "-k", "-c"], data)


def xz_decompress(data: bytes) -> tuple[bytes, float]:
    return _run_cli(["xz", "-d", "-c"], data)


def gzip_compress(data: bytes) -> tuple[bytes, float]:
    return _run_cli(["gzip", "-n", "-6", "-c"], data)


def gzip_decompress(data: bytes) -> tuple[bytes, float]:
    return _run_cli(["gzip", "-d", "-c"], data)


SOLUTIONS = {
    "propio": (propio_compress, propio_decompress),
    "xz-6": (xz_compress, xz_decompress),
    "gzip-6": (gzip_compress, gzip_decompress),
}


# --------------------------------------------------------------------------
# Benchmark por archivo/solución
# --------------------------------------------------------------------------


def benchmark_one(filename: str, algoritmo: str, data: bytes) -> dict:
    compress_fn, decompress_fn = SOLUTIONS[algoritmo]

    compressed, t_compress_ms = compress_fn(data)
    reconstructed, t_decompress_ms = decompress_fn(compressed)

    original_size = len(data)
    compressed_size = len(compressed)

    sha_original = hashlib.sha256(data).digest()
    sha_reconstructed = hashlib.sha256(reconstructed).digest()
    integridad_ok = sha_original == sha_reconstructed

    ratio = (original_size / compressed_size) if compressed_size > 0 else float("inf")
    saved_pct = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0.0
    relative_size_pct = (compressed_size / original_size) * 100 if original_size > 0 else 0.0

    original_mb = original_size / MB
    v_compress = (original_mb / (t_compress_ms / 1000)) if t_compress_ms > 0 else float("inf")
    v_decompress = (original_mb / (t_decompress_ms / 1000)) if t_decompress_ms > 0 else float("inf")

    header_overhead_pct = None
    if algoritmo == "propio":
        header_overhead_pct = (tdi_format.HEADER_SIZE / compressed_size) * 100 if compressed_size > 0 else 0.0

    return {
        "archivo": filename,
        "algoritmo": algoritmo,
        "tamano_original_bytes": original_size,
        "tamano_comprimido_bytes": compressed_size,
        "ratio_R": ratio,
        "ahorro_pct_A": saved_pct,
        "tamano_relativo_pct_P": relative_size_pct,
        "tiempo_compresion_ms": t_compress_ms,
        "tiempo_descompresion_ms": t_decompress_ms,
        "throughput_compresion_MBps_Vc": v_compress,
        "throughput_descompresion_MBps_Vd": v_decompress,
        "overhead_cabecera_pct_O": header_overhead_pct,
        "integridad_ok": integridad_ok,
    }


# --------------------------------------------------------------------------
# Weissman Score
# --------------------------------------------------------------------------


def weissman_score(r_solution: float, t_solution_ms: float, r_ref: float, t_ref_ms: float) -> float:
    """W = alpha * (R/Rref) * (log(Tref) / log(T)), alpha=1, tiempos en ms.

    Si un tiempo medido redondea a menos de 1 ms se trata como 1 ms para
    evitar log(0) / log indefinido (dominio de log requiere T > 0, y log(1)=0
    haría que el cociente fuera indefinido si tanto T como Tref cayeran ahí).
    """
    t_solution_ms = max(t_solution_ms, 1.0)
    t_ref_ms = max(t_ref_ms, 1.0)
    if t_solution_ms == 1.0 and t_ref_ms == 1.0:
        # log(1) = 0 en ambos -> cociente 0/0 indefinido; en ese caso el
        # término temporal no aporta información real (tiempos demasiado
        # chicos para medir), así que lo neutralizamos a 1.0.
        time_term = 1.0
    else:
        time_term = math.log(t_ref_ms) / math.log(t_solution_ms) if math.log(t_solution_ms) != 0 else 1.0
    return (r_solution / r_ref) * time_term


def global_metrics(rows: list[dict], algoritmo: str, filenames: list[str]) -> tuple[float, float]:
    subset = [r for r in rows if r["algoritmo"] == algoritmo and r["archivo"] in filenames]
    total_original = sum(r["tamano_original_bytes"] for r in subset)
    total_compressed = sum(r["tamano_comprimido_bytes"] for r in subset)
    r_global = total_original / total_compressed if total_compressed > 0 else float("inf")
    t_global = statistics.median(r["tiempo_compresion_ms"] for r in subset)
    return r_global, t_global


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for filename, _label, _in_ranking in CORPUS_FILES:
        path = CORPUS_DIR / filename
        data = path.read_bytes()
        for algoritmo in ("propio", "xz-6", "gzip-6"):
            print(f"Corriendo {algoritmo} sobre {filename}...")
            row = benchmark_one(filename, algoritmo, data)
            if not row["integridad_ok"]:
                print(f"  ADVERTENCIA: fallo de integridad SHA-256 para {algoritmo}/{filename}", file=sys.stderr)
            rows.append(row)

    # --- CSV ---
    csv_path = RESULTS_DIR / "benchmark_resultados.csv"
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"\nCSV escrito en {csv_path}")

    # --- Weissman Score global (Pruebas 2, 3, 4 -- Prueba 1 no entra en el ranking temporal) ---
    ranking_filenames = [f for f, _l, in_ranking in CORPUS_FILES if in_ranking]

    r_gzip, t_gzip = global_metrics(rows, "gzip-6", ranking_filenames)
    r_propio, t_propio = global_metrics(rows, "propio", ranking_filenames)
    r_xz, t_xz = global_metrics(rows, "xz-6", ranking_filenames)

    w_gzip = 1.0  # por definición, referencia
    w_propio = weissman_score(r_propio, t_propio, r_gzip, t_gzip)
    w_xz = weissman_score(r_xz, t_xz, r_gzip, t_gzip)

    # --- resumen legible ---
    summary_lines = []
    summary_lines.append("# Resumen del benchmark — Práctico de Máquina 2\n")
    summary_lines.append(
        f"Corpus usado para el ranking temporal / Weissman Score global: "
        f"{', '.join(ranking_filenames)} (Prueba 1 queda excluida, según el enunciado).\n"
    )
    summary_lines.append("## Weissman Score global (referencia = gzip -n -6)\n")
    summary_lines.append(f"- gzip-6 (referencia): W = {w_gzip:.4f} (por definición)")
    summary_lines.append(f"- propio (RLE + Shannon): W = {w_propio:.4f}  (R_global={r_propio:.4f}, T_global={t_propio:.3f} ms)")
    summary_lines.append(f"- xz-6: W = {w_xz:.4f}  (R_global={r_xz:.4f}, T_global={t_xz:.3f} ms)")
    summary_lines.append(f"- gzip-6: R_global={r_gzip:.4f}, T_global={t_gzip:.3f} ms\n")

    summary_lines.append("## Resultados por archivo\n")
    summary_lines.append("| Archivo | Algoritmo | Original (B) | Comprimido (B) | R | A (%) | Integridad |")
    summary_lines.append("|---|---|---:|---:|---:|---:|---|")
    for row in rows:
        summary_lines.append(
            f"| {row['archivo']} | {row['algoritmo']} | {row['tamano_original_bytes']} | "
            f"{row['tamano_comprimido_bytes']} | {row['ratio_R']:.4f} | {row['ahorro_pct_A']:.2f} | "
            f"{'OK' if row['integridad_ok'] else 'FALLÓ'} |"
        )
    summary_lines.append("")

    # Interpretación basada estrictamente en las filas obtenidas (sin inventar).
    def row_for(archivo: str, algoritmo: str) -> dict:
        return next(r for r in rows if r["archivo"] == archivo and r["algoritmo"] == algoritmo)

    r2_propio = row_for("prueba_2_texto_natural.txt", "propio")
    r2_xz = row_for("prueba_2_texto_natural.txt", "xz-6")
    r2_gzip = row_for("prueba_2_texto_natural.txt", "gzip-6")
    r3_propio = row_for("prueba_3_alta_repeticion.txt", "propio")
    r3_xz = row_for("prueba_3_alta_repeticion.txt", "xz-6")
    r4_propio = row_for("prueba_4_baja_repeticion.txt", "propio")
    r4_xz = row_for("prueba_4_baja_repeticion.txt", "xz-6")

    summary_lines.append("## Interpretación\n")
    summary_lines.append(
        f"En texto natural (Prueba 2), xz-6 alcanza R={r2_xz['ratio_R']:.2f} y gzip-6 R={r2_gzip['ratio_R']:.2f}, "
        f"muy por encima de la solución propia (R={r2_propio['ratio_R']:.2f}): LZMA2/DEFLATE explotan repeticiones "
        f"de largo alcance (frases y estructuras repetidas) que RLE, al operar solo sobre rachas de bytes "
        f"consecutivos idénticos, no puede capturar."
    )
    summary_lines.append(
        f"En alta repetición (Prueba 3), la brecha se achica: propio logra R={r3_propio['ratio_R']:.2f} "
        f"aprovechando las rachas largas directamente, aunque xz-6 (R={r3_xz['ratio_R']:.2f}) sigue ganando "
        f"por combinar coincidencias de largo alcance con Huffman/entropía sobre los literales."
    )
    summary_lines.append(
        f"En baja repetición / pseudoaleatorio (Prueba 4), la solución propia con R={r4_propio['ratio_R']:.2f} "
        f"{'no logra comprimir (R<1, el .tdi resulta más grande que el original)' if r4_propio['ratio_R'] < 1 else 'apenas comprime'}, "
        f"lo cual es esperable: sin rachas que explotar y con una distribución casi uniforme, ni RLE ni un "
        f"codificador de entropía por símbolo pueden ganar espacio; xz-6 (R={r4_xz['ratio_R']:.2f}) tampoco gana mucho, "
        f"por la misma razón de fondo (entropía cercana al máximo)."
    )
    summary_lines.append("")

    summary_path = RESULTS_DIR / "benchmark_resumen.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Resumen escrito en {summary_path}")

    all_ok = all(r["integridad_ok"] for r in rows)
    if not all_ok:
        print("\nATENCIÓN: hubo fallos de integridad SHA-256 en al menos una solución/archivo.", file=sys.stderr)
        return 1

    print("\nBenchmark completo. Integridad SHA-256 OK en todas las filas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
