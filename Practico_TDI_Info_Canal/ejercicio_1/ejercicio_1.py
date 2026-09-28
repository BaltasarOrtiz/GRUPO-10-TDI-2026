#!/usr/bin/env python3
"""Ejercicio 1 — Análisis de Información en Señales de Audio (WAV vs MP3).

Dados un .wav y un .mp3 con la misma pista: valida formato, lee cabeceras,
calcula distribución de probabilidad y entropía de Shannon por byte, y
grafica los histogramas comparativos.

Uso:
    python3 ejercicio_1.py --wav audio/pista.wav --mp3 audio/pista.mp3
    python3 ejercicio_1.py                      # pide las rutas por teclado
    python3 ejercicio_1.py --wav ... --mp3 ... --no-show   # sin ventana
"""
from __future__ import annotations
import argparse
import os
import struct
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #
DIR_SCRIPT = Path(__file__).resolve().parent      # salida/ se ubica SIEMPRE junto al script
DIR_SALIDA = DIR_SCRIPT / "salida"
RUTA_PNG = DIR_SALIDA / "histogramas.png"
RUTA_RESUMEN = DIR_SALIDA / "resumen.txt"
MAX_ENTROPIA = 8.0        # log2(256) bits/byte
TAM_CHUNK = 1 << 20       # 1 MiB por lectura al contar frecuencias
FIRMA_RIFF = b"RIFF"; FIRMA_WAVE = b"WAVE"; ID_ID3 = b"ID3"


class ErrorEntrada(Exception):
    """Entrada inválida del usuario (ruta, extensión o formato)."""


def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    try:
        # --- rutas + validación (paso 3) ---
        ruta_wav = resolver_ruta(args.wav, "WAV")
        ruta_mp3 = resolver_ruta(args.mp3, "MP3")
        validar_extension(ruta_wav, ".wav")
        validar_extension(ruta_mp3, ".mp3")
        print("[1/6] Validando archivos...")
        print(f"      WAV: {ruta_wav}  (extensión .wav OK)")
        print(f"      MP3: {ruta_mp3}  (extensión .mp3 OK)")

        # --- cabeceras (pasos 4 y 5) ---
        print("[2/6] Analizando cabecera WAV (RIFF/WAVE)...")
        cab_wav = leer_cabecera_wav(ruta_wav)          # valida firma RIFF/WAVE
        print(volcado_hex(ruta_wav)); print(tabla_cabecera_wav(cab_wav))
        print(f"      {detalle_coherencia_wav(cab_wav)}")

        print("[3/6] Analizando cabecera MP3 (ID3v2 / trama MPEG)...")
        cab_mp3 = leer_cabecera_mp3(ruta_mp3)          # valida ID3v2 o sync MPEG
        print(tabla_cabecera_mp3(cab_mp3))
        print(f"      MP3: {ruta_mp3}  ({resumen_validacion_mp3(cab_mp3)} OK)")

        # --- distribuciones y entropías (pasos 6 y 7) ---
        print("[4/6] Calculando distribuciones de probabilidad (256 símbolos)...")
        conteos_wav = contar_bytes(ruta_wav); conteos_mp3 = contar_bytes(ruta_mp3)
        prob_wav = a_probabilidades(conteos_wav); prob_mp3 = a_probabilidades(conteos_mp3)
        print(f"      WAV: {int(conteos_wav.sum())} bytes leídos, "
              f"{simbolos_distintos(conteos_wav)} símbolos distintos")
        print(f"      MP3: {int(conteos_mp3.sum())} bytes leídos, "
              f"{simbolos_distintos(conteos_mp3)} símbolos distintos")

        print("[5/6] Calculando entropía empírica H(S) = -Σ p(i)·log2(p(i))...")
        h_wav = entropia_shannon(prob_wav); h_mp3 = entropia_shannon(prob_mp3)
        print(f"      WAV: H = {h_wav:.4f} bits/byte (máximo {MAX_ENTROPIA:.4f}) "
              f"| redundancia {redundancia(h_wav)*100:.2f} %")
        print(f"      MP3: H = {h_mp3:.4f} bits/byte (máximo {MAX_ENTROPIA:.4f}) "
              f"| redundancia {redundancia(h_mp3)*100:.2f} %")

        # --- gráfico (paso 8) ---
        print("[6/6] Generando histogramas comparativos...")
        graficar_histogramas(prob_wav, prob_mp3, ruta_wav, ruta_mp3, h_wav, h_mp3)
        print(f"      Figura guardada: {RUTA_PNG}")
        if not args.no_show:
            print("      (cerrá la ventana de matplotlib para finalizar)")
            plt.show()
        else:
            plt.close("all")

        # --- resumen (paso 9) ---
        texto = resumen(ruta_wav, ruta_mp3, cab_wav, cab_mp3,
                        conteos_wav, conteos_mp3, h_wav, h_mp3)
        print(texto)
        DIR_SALIDA.mkdir(parents=True, exist_ok=True)
        RUTA_RESUMEN.write_text(texto + "\n", encoding="utf-8")
    except ErrorEntrada as e:
        print(f"ERROR: {e}", file=sys.stderr); return 1
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr); return 1
    return 0


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejercicio 1 — Análisis de información en señales de audio "
                     "(WAV vs MP3): cabecera, distribución de probabilidad, "
                     "histogramas y entropía de Shannon.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--wav", type=str, default=None,
        help="Ruta del archivo WAV (PCM). Si se omite, se solicita por teclado.",
    )
    parser.add_argument(
        "--mp3", type=str, default=None,
        help="Ruta del archivo MP3. Si se omite, se solicita por teclado.",
    )
    parser.add_argument(
        "--no-show", action="store_true",
        help="No abrir la ventana de matplotlib (solo genera y guarda el PNG).",
    )
    return parser.parse_args(argv)


def resolver_ruta(ruta: str | None, etiqueta: str) -> Path:
    if ruta is None:
        ruta = input(f"Ruta del archivo {etiqueta} (.{etiqueta.lower()}): ")
        while not ruta.strip():
            ruta = input(f"Ruta del archivo {etiqueta} (.{etiqueta.lower()}): ")
    return Path(os.path.expanduser(ruta))


# --------------------------------------------------------------------------- #
# Paso 3 — Validación de extensiones
# --------------------------------------------------------------------------- #
def validar_extension(ruta: Path, extension: str) -> None:
    if not ruta.is_file():
        raise ErrorEntrada(f"No existe el archivo: {ruta}")
    if ruta.stat().st_size == 0:
        raise ErrorEntrada(f"El archivo está vacío: {ruta}")
    if ruta.suffix.lower() != extension:
        raise ErrorEntrada(f"El archivo {ruta.name} debe tener extensión {extension} (recibido: {ruta.suffix or 'sin extensión'}).")


# --------------------------------------------------------------------------- #
# Paso 4 — Cabecera WAV (manipulación de bytes con seek)
# --------------------------------------------------------------------------- #
def _recorrer_chunks(f, ruta: Path) -> list[dict]:
    """Devuelve [{'id','offset','size','orden'}]; offset = posición de los datos del chunk."""
    tam_total = os.fstat(f.fileno()).st_size
    chunks: list[dict] = []
    f.seek(12)
    orden = 0
    while True:
        cabecera = f.read(8)
        if len(cabecera) < 8:
            break
        id_chunk = cabecera[0:4]
        (size,) = struct.unpack("<I", cabecera[4:8])
        offset = f.tell()
        if offset + size > tam_total:
            raise ErrorEntrada(
                f"Chunk {id_chunk!r} con tamaño {size} excede el tamaño del archivo: {ruta}"
            )
        chunks.append({"id": id_chunk, "offset": offset, "size": size, "orden": orden})
        orden += 1
        f.seek(size + (size & 1), 1)
    return chunks


def leer_cabecera_wav(ruta: Path) -> dict:
    try:
        with open(ruta, "rb") as f:
            datos = f.read(12)
            if len(datos) < 12 or datos[0:4] != FIRMA_RIFF or datos[8:12] != FIRMA_WAVE:
                raise ErrorEntrada(f"El archivo no es un WAV RIFF/WAVE válido: {ruta}")
            (chunk_size,) = struct.unpack("<I", datos[4:8])

            chunks = _recorrer_chunks(f, ruta)

            fmt_chunk = None
            data_chunk = None
            otros: list[tuple[bytes, int]] = []
            for c in chunks:
                if c["id"] == b"fmt " and fmt_chunk is None:
                    fmt_chunk = c
                elif c["id"] == b"data" and data_chunk is None:
                    data_chunk = c
                else:
                    otros.append((c["id"], c["size"]))

            if fmt_chunk is None:
                raise ErrorEntrada(f"El archivo WAV no tiene chunk 'fmt ': {ruta}")
            if data_chunk is None:
                raise ErrorEntrada(f"El archivo WAV no tiene chunk 'data': {ruta}")

            f.seek(fmt_chunk["offset"])
            fmt_datos = f.read(16)
            (audio_format, num_channels, sample_rate, byte_rate,
             block_align, bits_per_sample) = struct.unpack("<HHIIHH", fmt_datos[:16])
    except OSError as e:
        raise ErrorEntrada(f"No se pudo leer {ruta}: {e}") from e

    tam_archivo = ruta.stat().st_size

    return {
        "ChunkID": "RIFF",
        "ChunkSize": chunk_size,
        "Format": "WAVE",
        "Subchunk1ID": fmt_chunk["id"].decode("latin-1"),
        "Subchunk1Size": fmt_chunk["size"],
        "AudioFormat": audio_format,
        "NumChannels": num_channels,
        "SampleRate": sample_rate,
        "ByteRate": byte_rate,
        "BlockAlign": block_align,
        "BitsPerSample": bits_per_sample,
        "Subchunk2ID": data_chunk["id"].decode("latin-1"),
        "Subchunk2Size": data_chunk["size"],
        "DataOffset": data_chunk["offset"],
        "TamanoArchivo": tam_archivo,
        "OtrosChunks": [(cid.decode("latin-1"), csize) for cid, csize in otros],
    }


def volcado_hex(ruta: Path, limite: int = 44) -> str:
    try:
        with open(ruta, "rb") as f:
            datos = f.read(limite)
    except OSError as e:
        raise ErrorEntrada(f"No se pudo leer {ruta}: {e}") from e

    lineas = [f"---------------- VOLCADO HEXADECIMAL (primeros {limite} bytes) ----------------"]
    for off in range(0, len(datos), 16):
        fila = datos[off:off + 16]
        hex_cols = " ".join(f"{b:02X}" for b in fila).ljust(16 * 3 - 1)
        ascii_repr = "".join(chr(b) if 32 <= b <= 126 else "." for b in fila)
        lineas.append(f"{off:06X}  {hex_cols}  {ascii_repr}")
    return "\n".join(lineas)


def tabla_cabecera_wav(cab: dict) -> str:
    def campo_id(valor: str) -> str:
        # repr() para que el espacio final de IDs como "fmt " quede visible
        return repr(valor) if valor != valor.rstrip() else valor

    audio_format = cab["AudioFormat"]
    audio_format_txt = "1 (PCM)" if audio_format == 1 else f"{audio_format} (<sin nombre>)"

    filas = [
        ("0", "ChunkID", "4", cab["ChunkID"]),
        ("4", "ChunkSize", "4", f'{cab["ChunkSize"]}   (tamaño del archivo menos 8)'),
        ("8", "Format", "4", cab["Format"]),
        ("12", "Subchunk1ID", "4", campo_id(cab["Subchunk1ID"])),
        ("16", "Subchunk1Size", "4", str(cab["Subchunk1Size"])),
        ("20", "AudioFormat", "2", audio_format_txt),
        ("22", "NumChannels", "2", str(cab["NumChannels"])),
        ("24", "SampleRate", "4", str(cab["SampleRate"])),
        ("28", "ByteRate", "4", str(cab["ByteRate"])),
        ("32", "BlockAlign", "2", str(cab["BlockAlign"])),
        ("34", "BitsPerSample", "2", str(cab["BitsPerSample"])),
        ("36", "Subchunk2ID", "4", campo_id(cab["Subchunk2ID"])),
        ("40", "Subchunk2Size", "4", str(cab["Subchunk2Size"])),
        ("44", "Data", "*", "inicio de las muestras"),
    ]

    lineas = [
        "---------------- CABECERA WAV (RIFF/WAVE) ----------------",
        f"{'Offset':<8}{'Campo':<17}{'Size':<6}{'Valor'}",
    ]
    for offset, campo, size, valor in filas:
        lineas.append(f"{offset:<8}{campo:<17}{size:<6}{valor}")
    return "\n".join(lineas)


def detalle_coherencia_wav(cab: dict) -> str:
    chunk_ok = cab["ChunkSize"] + 8 == cab["TamanoArchivo"]
    if chunk_ok:
        l1 = "Coherencia: ChunkSize+8 coincide con el tamaño del archivo"
    else:
        l1 = (f"Coherencia: INCOHERENTE (ChunkSize+8={cab['ChunkSize'] + 8} "
              f"vs tamaño real={cab['TamanoArchivo']})")

    block_align_esperado_exacto = cab["NumChannels"] * cab["BitsPerSample"] / 8
    block_align_esperado = cab["NumChannels"] * cab["BitsPerSample"] // 8
    if block_align_esperado_exacto != block_align_esperado:
        l2 = (f"      Coherencia: BlockAlign no resulta un número entero de bytes "
              f"(NumChannels*BitsPerSample/8 = {block_align_esperado_exacto})")
    elif cab["BlockAlign"] == block_align_esperado:
        l2 = "      Coherencia: BlockAlign coincide con NumChannels*BitsPerSample/8"
    else:
        l2 = (f"      Coherencia: INCOHERENTE BlockAlign={cab['BlockAlign']} "
              f"(esperado {block_align_esperado})")

    byte_rate_esperado = cab["SampleRate"] * cab["BlockAlign"]
    if cab["ByteRate"] == byte_rate_esperado:
        l3 = "      Coherencia: ByteRate coincide con SampleRate*BlockAlign"
    else:
        l3 = (f"      Coherencia: INCOHERENTE ByteRate={cab['ByteRate']} "
              f"(esperado {byte_rate_esperado})")

    if cab["ByteRate"] > 0:
        duracion_seg = cab["Subchunk2Size"] / cab["ByteRate"]
        l4 = f"      Duración: {formatear_duracion(duracion_seg)}"
    else:
        l4 = "      Duración: indeterminada (ByteRate = 0)"

    return f"{l1}\n{l2}\n{l3}\n{l4}\n"


# --------------------------------------------------------------------------- #
# Paso 5 — Cabecera MP3
# --------------------------------------------------------------------------- #
BITRATES_MPEG1 = {1: [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448],
                  2: [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384],
                  3: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]}
BITRATES_MPEG2 = {1: [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256],
                  2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
                  3: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160]}
SR = {"MPEG-1": [44100, 48000, 32000], "MPEG-2": [22050, 24000, 16000], "MPEG-2.5": [11025, 12000, 8000]}
MODOS = {0: "Estéreo", 1: "Joint stereo", 2: "Dual channel", 3: "Mono"}
VERSIONES = {0b00: "MPEG-2.5", 0b10: "MPEG-2", 0b11: "MPEG-1"}
CAPAS = {0b01: "III", 0b10: "II", 0b11: "I"}
CAPA_NUM = {"I": 1, "II": 2, "III": 3}


def leer_cabecera_mp3(ruta: Path) -> dict:
    try:
        with open(ruta, "rb") as f:
            cabecera = f.read(10)

            id3 = False
            id3_version = None
            id3_tamano = None
            audio_offset = 0

            if cabecera[:3] == ID_ID3:
                id3 = True
                major, revision, flags = cabecera[3], cabecera[4], cabecera[5]
                b0, b1s, b2s, b3s = cabecera[6], cabecera[7], cabecera[8], cabecera[9]
                tam_id3 = 10 + (((b0 & 0x7F) << 21) | ((b1s & 0x7F) << 14) |
                                 ((b2s & 0x7F) << 7) | (b3s & 0x7F))
                if flags & 0x10:
                    tam_id3 += 10
                id3_version = f"2.{major}.{revision}"
                id3_tamano = tam_id3 - 10
                audio_offset = tam_id3

                f.seek(tam_id3)
                datos = f.read(4)
                if len(datos) < 4:
                    raise ErrorEntrada(
                        f"El archivo no parece ser un MP3 válido (ni etiqueta ID3v2 "
                        f"ni sincronización de trama MPEG): {ruta}"
                    )
                offset_sync = tam_id3
            else:
                f.seek(0)
                ventana = f.read(65536)
                offset_sync = -1
                for idx in range(len(ventana) - 1):
                    if ventana[idx] == 0xFF and (ventana[idx + 1] & 0xE0) == 0xE0:
                        version_bits = (ventana[idx + 1] >> 3) & 0b11
                        layer_bits = (ventana[idx + 1] >> 1) & 0b11
                        if version_bits != 0b01 and layer_bits != 0b00:
                            offset_sync = idx
                            break
                if offset_sync == -1 or offset_sync + 4 > len(ventana):
                    raise ErrorEntrada(
                        f"El archivo no parece ser un MP3 válido (ni etiqueta ID3v2 "
                        f"ni sincronización de trama MPEG): {ruta}"
                    )
                datos = ventana[offset_sync:offset_sync + 4]

            b1, b2, b3 = datos[1], datos[2], datos[3]
            version_bits = (b1 >> 3) & 0b11          # 0b00 MPEG-2.5 | 0b10 MPEG-2 | 0b11 MPEG-1
            layer_bits = (b1 >> 1) & 0b11             # 0b01 Layer III | 0b10 Layer II | 0b11 Layer I
            bitrate_idx = (b2 >> 4) & 0b1111
            sr_idx = (b2 >> 2) & 0b11
            modo = (b3 >> 6) & 0b11

            if version_bits not in VERSIONES or layer_bits not in CAPAS:
                raise ErrorEntrada(
                    f"El archivo no parece ser un MP3 válido (ni etiqueta ID3v2 "
                    f"ni sincronización de trama MPEG): {ruta}"
                )

            version_mpeg = VERSIONES[version_bits]
            capa_txt = CAPAS[layer_bits]
            capa_num = CAPA_NUM[capa_txt]

            if bitrate_idx == 0:
                bitrate_texto = "libre (a definir en la trama)"
                bitrate_kbps = None
            else:
                tabla_bitrate = BITRATES_MPEG1 if version_mpeg == "MPEG-1" else BITRATES_MPEG2
                bitrate_kbps = tabla_bitrate[capa_num][bitrate_idx]
                bitrate_texto = f"{bitrate_kbps} kbps"

            if sr_idx == 3:
                frecuencia_texto = "reservado"
                frecuencia_hz = None
            else:
                frecuencia_hz = SR[version_mpeg][sr_idx]
                frecuencia_texto = f"{frecuencia_hz} Hz"

            modo_texto = MODOS[modo]
    except OSError as e:
        raise ErrorEntrada(f"No se pudo leer {ruta}: {e}") from e

    return {
        "ID3": id3,
        "ID3Version": id3_version,
        "ID3Tamano": id3_tamano,
        "AudioOffset": audio_offset,
        "SyncOffset": offset_sync,
        "SyncBytes": (datos[0], datos[1]),
        "VersionMPEG": version_mpeg,
        "Capa": capa_txt,
        "BitrateTexto": bitrate_texto,
        "BitrateKbps": bitrate_kbps,
        "FrecuenciaTexto": frecuencia_texto,
        "FrecuenciaHz": frecuencia_hz,
        "Modo": modo_texto,
    }


def tabla_cabecera_mp3(cab: dict) -> str:
    if cab["ID3"]:
        firma = (f"presente (versión {cab['ID3Version']}, etiqueta de {cab['ID3Tamano']} bytes, "
                 f"audio en offset {cab['AudioOffset']})")
    else:
        firma = "ausente"

    b0, b1 = cab["SyncBytes"]
    sync_txt = f"offset {cab['SyncOffset']} (0x{b0:02X} 0x{b1:02X})"

    lineas = [
        "---------------- CABECERA MP3 ----------------",
        f"Firma ID3v2      : {firma}",
        f"Sincronización   : {sync_txt}",
        f"Versión MPEG     : {cab['VersionMPEG']}",
        f"Capa (Layer)     : {cab['Capa']}",
        f"Bitrate          : {cab['BitrateTexto']}",
        f"Frecuencia       : {cab['FrecuenciaTexto']}",
        f"Modo de canal    : {cab['Modo']}",
    ]
    return "\n".join(lineas)


def resumen_validacion_mp3(cab: dict) -> str:
    return "ID3v2 + sincronización MPEG" if cab["ID3"] else "sincronización MPEG"


# --------------------------------------------------------------------------- #
# Paso 6 — Distribución de probabilidad
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
# Paso 7 — Entropía empírica de Shannon
# --------------------------------------------------------------------------- #
def entropia_shannon(prob: np.ndarray) -> float:
    # H(S) = -Σ p(i)·log2(p(i)); convención 0·log2(0) = 0
    p = prob[prob > 0]
    return float(-(p * np.log2(p)).sum())


def redundancia(h: float) -> float:
    return 1.0 - h / MAX_ENTROPIA


# --------------------------------------------------------------------------- #
# Paso 8 — Histogramas comparativos (matplotlib)
# --------------------------------------------------------------------------- #
def graficar_histogramas(prob_wav: np.ndarray, prob_mp3: np.ndarray,
                          ruta_wav: Path, ruta_mp3: Path,
                          h_wav: float, h_mp3: float) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, prob, etiqueta, ruta, h, color in (
            (axes[0], prob_wav, "WAV (PCM sin compresión)", ruta_wav, h_wav, "#2a6f97"),
            (axes[1], prob_mp3, "MP3 (con compresión)",      ruta_mp3, h_mp3, "#e07a5f")):
        ax.bar(np.arange(256), prob, width=1.0, color=color, edgecolor="none")
        ax.set_xlim(-0.5, 255.5)
        ax.set_ylabel("Frecuencia relativa $p_i$")
        ax.set_title(f"{etiqueta} — {ruta.name} — H = {h:.4f} bits/byte | R = {redundancia(h)*100:.2f} %",
                     fontsize=10)
    axes[1].set_xlabel("Valor del byte (0–255)")
    fig.suptitle("Histograma de frecuencias relativas por valor de byte — WAV vs MP3", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    fig.savefig(RUTA_PNG, dpi=110, facecolor="white")


# --------------------------------------------------------------------------- #
# Paso 9 — Resumen final: consola + salida/resumen.txt
# --------------------------------------------------------------------------- #
def formatear_duracion(segundos: float) -> str:
    total_ms = round(segundos * 1000)
    mm, resto_ms = divmod(total_ms, 60000)
    ss, ms = divmod(resto_ms, 1000)
    return f"{mm:02d}:{ss:02d}.{ms:03d}"


def top_bytes(conteos: np.ndarray, n: int = 5) -> list[tuple[int, int]]:
    valores = sorted(range(256), key=lambda v: (-int(conteos[v]), v))[:n]
    return [(v, int(conteos[v])) for v in valores]


def resumen(ruta_wav: Path, ruta_mp3: Path, cab_wav: dict, cab_mp3: dict,
            conteos_wav: np.ndarray, conteos_mp3: np.ndarray,
            h_wav: float, h_mp3: float) -> str:
    tam_wav = ruta_wav.stat().st_size
    tam_mp3 = ruta_mp3.stat().st_size

    duracion_wav = (formatear_duracion(cab_wav["Subchunk2Size"] / cab_wav["ByteRate"])
                     if cab_wav["ByteRate"] else "indeterminada")

    simb_wav = simbolos_distintos(conteos_wav)
    simb_mp3 = simbolos_distintos(conteos_mp3)
    r_wav = redundancia(h_wav)
    r_mp3 = redundancia(h_mp3)

    total_wav = int(conteos_wav.sum())
    total_mp3 = int(conteos_mp3.sum())
    top_wav_txt = ", ".join(f"0x{v:02X}: {(c / total_wav) * 100:.2f}%" for v, c in top_bytes(conteos_wav))
    top_mp3_txt = ", ".join(f"0x{v:02X}: {(c / total_mp3) * 100:.2f}%" for v, c in top_bytes(conteos_mp3))

    factor = tam_wav / tam_mp3
    razon = tam_mp3 / tam_wav

    return (
        "================ RESUMEN (Ejercicio 1) ================\n"
        f"WAV : {ruta_wav}\n"
        f"   tamaño            : {tam_wav} bytes ({tam_wav / 1048576:.2f} MiB)\n"
        f"   formato           : PCM {cab_wav['BitsPerSample']} bits/muestra, "
        f"{cab_wav['NumChannels']} canal(es), {cab_wav['SampleRate']} Hz\n"
        f"   duración          : {duracion_wav}\n"
        f"   símbolos distintos: {simb_wav}/256\n"
        f"   entropía empírica : {h_wav:.4f} bits/byte   (máximo teórico 8.0000)\n"
        f"   redundancia       : {r_wav * 100:.2f} %\n"
        f"MP3 : {ruta_mp3}\n"
        f"   tamaño            : {tam_mp3} bytes ({tam_mp3 / 1048576:.2f} MiB)\n"
        f"   formato           : {cab_mp3['VersionMPEG']} Layer {cab_mp3['Capa']}, "
        f"{cab_mp3['BitrateTexto']}, {cab_mp3['FrecuenciaTexto']}, {cab_mp3['Modo']}\n"
        f"   símbolos distintos: {simb_mp3}/256\n"
        f"   entropía empírica : {h_mp3:.4f} bits/byte   (máximo teórico 8.0000)\n"
        f"   redundancia       : {r_mp3 * 100:.2f} %\n"
        "COMPARACIÓN\n"
        f"   Δentropía (MP3 − WAV)      : {h_mp3 - h_wav:+.4f} bits/byte\n"
        f"   factor de tamaño (WAV/MP3) : {factor:.2f}x   (razón MP3/WAV = {razon:.4f})\n"
        f"   bytes más frecuentes WAV   : {top_wav_txt}\n"
        f"   bytes más frecuentes MP3   : {top_mp3_txt}\n"
        "=======================================================\n"
        f"Salida guardada: {RUTA_PNG}\n"
        f"                 {RUTA_RESUMEN}"
    )


if __name__ == "__main__":
    sys.exit(main())
