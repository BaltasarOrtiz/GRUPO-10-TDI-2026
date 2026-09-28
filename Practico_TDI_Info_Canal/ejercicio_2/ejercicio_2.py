#!/usr/bin/env python3
"""Ejercicio 2 — Análisis de Entropía, Histogramas y Estructura de Archivos (BMP vs JPG).

Dados un .bmp y un .jpg de la misma foto: valida formato, lee cabeceras,
calcula distribución de probabilidad y entropía de Shannon por byte, y
grafica los histogramas comparativos.

Uso:
    python3 ejercicio_2.py --bmp imagenes/foto.bmp --jpg imagenes/foto.jpg
    python3 ejercicio_2.py                      # pide las rutas por teclado
    python3 ejercicio_2.py --bmp ... --jpg ... --no-show   # sin ventana
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
FIRMA_BMP = b"BM"
MARCADOR_SOI = b"\xFF\xD8"
MARCADOR_EOI = b"\xFF\xD9"


class ErrorEntrada(Exception):
    """Entrada inválida del usuario (ruta, extensión o formato)."""


def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    try:
        # --- rutas + validación (paso 3) ---
        ruta_bmp = resolver_ruta(args.bmp, "BMP")
        ruta_jpg = resolver_ruta(args.jpg, "JPG")
        validar_extension(ruta_bmp, ".bmp")
        validar_extension(ruta_jpg, ".jpg")
        print("[1/6] Validando archivos...")
        print(f"      BMP: {ruta_bmp}  (extensión .bmp OK)")
        print(f"      JPG: {ruta_jpg}  (extensión .jpg OK)")

        # --- cabeceras (pasos 4 y 5) ---
        print("[2/6] Analizando cabecera BMP (BITMAPFILEHEADER + BITMAPINFOHEADER)...")
        cab_bmp = leer_cabecera_bmp(ruta_bmp)           # valida firma "BM"
        print(volcado_hex(ruta_bmp)); print(tabla_cabecera_bmp(cab_bmp))
        print(f"      {detalle_coherencia_bmp(cab_bmp)}")

        print("[3/6] Analizando cabecera JPG (JFIF/Exif, marcadores JPEG)...")
        cab_jpg = leer_cabecera_jpg(ruta_jpg)            # valida SOI 0xFFD8
        print(tabla_cabecera_jpg(cab_jpg))
        print(f"      JPG: {ruta_jpg}  ({resumen_validacion_jpg(cab_jpg)} OK)")

        # --- distribuciones y entropías (pasos 6 y 7) ---
        print("[4/6] Calculando distribuciones de probabilidad (256 símbolos)...")
        conteos_bmp = contar_bytes(ruta_bmp); conteos_jpg = contar_bytes(ruta_jpg)
        prob_bmp = a_probabilidades(conteos_bmp); prob_jpg = a_probabilidades(conteos_jpg)
        print(f"      BMP: {int(conteos_bmp.sum())} bytes leídos, "
              f"{simbolos_distintos(conteos_bmp)} símbolos distintos")
        print(f"      JPG: {int(conteos_jpg.sum())} bytes leídos, "
              f"{simbolos_distintos(conteos_jpg)} símbolos distintos")

        print("[5/6] Calculando entropía empírica H(S) = -Σ p(i)·log2(p(i))...")
        h_bmp = entropia_shannon(prob_bmp); h_jpg = entropia_shannon(prob_jpg)
        print(f"      BMP: H = {h_bmp:.4f} bits/byte (máximo {MAX_ENTROPIA:.4f}) "
              f"| redundancia {redundancia(h_bmp)*100:.2f} %")
        print(f"      JPG: H = {h_jpg:.4f} bits/byte (máximo {MAX_ENTROPIA:.4f}) "
              f"| redundancia {redundancia(h_jpg)*100:.2f} %")

        # --- gráfico (paso 8) ---
        print("[6/6] Generando histogramas comparativos...")
        graficar_histogramas(prob_bmp, prob_jpg, ruta_bmp, ruta_jpg, h_bmp, h_jpg)
        print(f"      Figura guardada: {RUTA_PNG}")
        if not args.no_show:
            print("      (cerrá la ventana de matplotlib para finalizar)")
            plt.show()
        else:
            plt.close("all")

        # --- resumen (paso 9) ---
        texto = resumen(ruta_bmp, ruta_jpg, cab_bmp, cab_jpg,
                        conteos_bmp, conteos_jpg, h_bmp, h_jpg)
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
        description="Ejercicio 2 — Análisis de información en imágenes "
                     "(BMP vs JPG): cabecera, distribución de probabilidad, "
                     "histogramas y entropía de Shannon.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--bmp", type=str, default=None,
        help="Ruta del archivo BMP (sin compresión). Si se omite, se solicita por teclado.",
    )
    parser.add_argument(
        "--jpg", type=str, default=None,
        help="Ruta del archivo JPG. Si se omite, se solicita por teclado.",
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
# Paso 4 — Cabecera BMP (BITMAPFILEHEADER + BITMAPINFOHEADER)
# --------------------------------------------------------------------------- #
BMP_COMPRESION = {0: "BI_RGB (sin compresión)", 1: "BI_RLE8", 2: "BI_RLE4",
                   3: "BI_BITFIELDS", 4: "BI_JPEG", 5: "BI_PNG", 6: "BI_ALPHABITFIELDS"}


def leer_cabecera_bmp(ruta: Path) -> dict:
    try:
        with open(ruta, "rb") as f:
            datos = f.read(54)
    except OSError as e:
        raise ErrorEntrada(f"No se pudo leer {ruta}: {e}") from e

    if datos[0:2] != FIRMA_BMP:
        raise ErrorEntrada(f"El archivo no es un BMP válido (firma 'BM' ausente): {ruta}")

    signature, file_size, reserved, data_offset = struct.unpack_from("<2sIII", datos, 0)
    (size, width, height, planes, bit_count, compression, image_size,
     x_ppm, y_ppm, colors_used, colors_important) = struct.unpack_from("<IiiHHIIiiII", datos, 14)

    if size != 40:
        raise ErrorEntrada(
            f"Variante de cabecera BMP no soportada (BITMAPINFOHEADER de {size} bytes, se espera 40): {ruta}"
        )

    tam_archivo = ruta.stat().st_size

    return {
        "Signature": signature.decode("latin-1"),
        "FileSize": file_size,
        "Reserved": reserved,
        "DataOffset": data_offset,
        "Size": size,
        "Width": width,
        "Height": height,
        "Planes": planes,
        "BitCount": bit_count,
        "Compression": compression,
        "ImageSize": image_size,
        "XPixelsPerM": x_ppm,
        "YPixelsPerM": y_ppm,
        "ColorsUsed": colors_used,
        "ColorsImportant": colors_important,
        "TamanoArchivo": tam_archivo,
    }


def volcado_hex(ruta: Path, limite: int = 54) -> str:
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


def tabla_cabecera_bmp(cab: dict) -> str:
    compresion_txt = BMP_COMPRESION.get(cab["Compression"], f"{cab['Compression']} (desconocido)")
    orientacion = "bottom-up" if cab["Height"] > 0 else "top-down"

    filas = [
        ("0", "Signature", "2", cab["Signature"]),
        ("2", "FileSize", "4", f'{cab["FileSize"]}   (tamaño declarado del archivo)'),
        ("6", "Reserved", "4", str(cab["Reserved"])),
        ("10", "DataOffset", "4", f'{cab["DataOffset"]}   (inicio de los píxeles)'),
        ("14", "Size", "4", f'{cab["Size"]}   (tamaño de BITMAPINFOHEADER)'),
        ("18", "Width", "4", f'{cab["Width"]} px'),
        ("22", "Height", "4", f'{cab["Height"]} px  (positivo = bottom-up, negativo = top-down; {orientacion})'),
        ("26", "Planes", "2", str(cab["Planes"])),
        ("28", "BitCount", "2", f'{cab["BitCount"]} bits/píxel'),
        ("30", "Compression", "4", f'{cab["Compression"]} ({compresion_txt})'),
        ("34", "ImageSize", "4", f'{cab["ImageSize"]} bytes'),
        ("38", "XPixelsPerM", "4", f'{cab["XPixelsPerM"]} px/m'),
        ("42", "YPixelsPerM", "4", f'{cab["YPixelsPerM"]} px/m'),
        ("46", "ColorsUsed", "4", str(cab["ColorsUsed"])),
        ("50", "ColorsImportant", "4", str(cab["ColorsImportant"])),
        ("54", "Data", "*", "inicio de los datos de píxeles"),
    ]

    lineas = [
        "---------------- CABECERA BMP (BITMAPFILEHEADER + BITMAPINFOHEADER) ----------------",
        f"{'Offset':<8}{'Campo':<17}{'Size':<6}{'Valor'}",
    ]
    for offset, campo, size, valor in filas:
        lineas.append(f"{offset:<8}{campo:<17}{size:<6}{valor}")
    return "\n".join(lineas)


def detalle_coherencia_bmp(cab: dict) -> str:
    if cab["FileSize"] == cab["TamanoArchivo"]:
        l1 = "Coherencia: FileSize coincide con el tamaño del archivo"
    else:
        l1 = (f"Coherencia: INCOHERENTE (FileSize={cab['FileSize']} "
              f"vs tamaño real={cab['TamanoArchivo']})")

    tamano_paleta = (cab["ColorsUsed"] if cab["ColorsUsed"] else
                      (2 ** cab["BitCount"] if cab["BitCount"] <= 8 else 0)) * 4
    data_offset_esperado = 14 + cab["Size"] + tamano_paleta
    if cab["DataOffset"] == data_offset_esperado:
        n_colores = tamano_paleta // 4
        l2 = f"      Coherencia: DataOffset coincide con 54 + paleta ({n_colores} colores)"
    else:
        l2 = (f"      Coherencia: INCOHERENTE DataOffset={cab['DataOffset']} "
              f"(esperado {data_offset_esperado})")

    if cab["BitCount"] in (1, 4, 8, 16, 24, 32):
        l3 = "      Coherencia: BitCount estándar"
    else:
        l3 = f"      Coherencia: BitCount no estándar (valor {cab['BitCount']}), se continúa igual"

    ancho = cab["Width"]
    alto = abs(cab["Height"])
    orientacion = "bottom-up" if cab["Height"] > 0 else "top-down"
    l4 = f"      Dimensiones: {ancho} x {alto} px ({ancho * alto} píxeles), orientación {orientacion}"

    return f"{l1}\n{l2}\n{l3}\n{l4}\n"


# --------------------------------------------------------------------------- #
# Paso 5 — Cabecera JPG (recorrido de marcadores con seek)
# --------------------------------------------------------------------------- #
MARCADORES_SOF = {0xC0: "Baseline DCT", 0xC1: "Extended Sequential DCT",
                   0xC2: "Progressive DCT", 0xC3: "Lossless (secuencial)"}


def _recorrer_marcadores_jpg(f, ruta: Path) -> dict:
    info = {"ContenedorTipo": "ninguno", "ContenedorVersion": None,
            "TipoSOF": None, "Precision": None, "Ancho": None, "Alto": None,
            "NumComponentes": None, "Marcadores": []}
    while True:
        b = f.read(1)
        if not b:
            raise ErrorEntrada(f"JPG truncado: no se encontró SOS/EOI antes del fin del archivo: {ruta}")
        if b != b"\xFF":
            continue                                 # byte de relleno entre marcadores
        marcador = f.read(1)
        if marcador in (b"", b"\x00", b"\xFF"):
            continue                                 # 0xFF de relleno o byte stuffing (no aplica antes de SOS)
        codigo = marcador[0]
        offset = f.tell() - 2
        if codigo == 0xD9:                            # EOI directo, sin SOS (imagen sin datos)
            info["EOI"] = True
            break
        if codigo in (0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0x01):
            continue                                  # RSTn / TEM: sin campo de longitud
        longitud = struct.unpack(">H", f.read(2))[0]  # incluye los 2 bytes de longitud
        info["Marcadores"].append((f"0xFF{codigo:02X}", offset, longitud))
        if 0xE0 <= codigo <= 0xEF:                     # APPn: detectar JFIF / Exif
            payload = f.read(min(longitud - 2, 16))
            if codigo == 0xE0 and payload[:5] == b"JFIF\x00":
                info["ContenedorTipo"] = "JFIF"
                info["ContenedorVersion"] = f"{payload[5]}.{payload[6]:02d}"
            elif codigo == 0xE1 and payload[:5] == b"Exif\x00":
                info["ContenedorTipo"] = "Exif"
            f.seek(offset + 2 + longitud, 0)
        elif 0xC0 <= codigo <= 0xCF and codigo not in (0xC4, 0xC8, 0xCC):  # SOFn (baseline/progresivo/...)
            payload = f.read(6)
            info["Precision"] = payload[0]
            info["Alto"] = struct.unpack(">H", payload[1:3])[0]
            info["Ancho"] = struct.unpack(">H", payload[3:5])[0]
            info["NumComponentes"] = payload[5]
            info["TipoSOF"] = MARCADORES_SOF.get(codigo, f"SOF{codigo - 0xC0}")
            f.seek(offset + 2 + longitud, 0)
        elif codigo == 0xDA:                          # SOS: acá empiezan los datos comprimidos, no seguir
            info["SOS_offset"] = offset
            break
        else:
            f.seek(offset + 2 + longitud, 0)           # DQT, DHT, COM, DRI, etc.: se saltea el payload
    return info


def leer_cabecera_jpg(ruta: Path) -> dict:
    try:
        with open(ruta, "rb") as f:
            inicio = f.read(2)
            if inicio != MARCADOR_SOI:
                raise ErrorEntrada(f"El archivo no parece ser un JPG válido (falta el marcador SOI 0xFFD8): {ruta}")

            info = _recorrer_marcadores_jpg(f, ruta)

            f.seek(-2, os.SEEK_END)
            info["EOI"] = f.read(2) == MARCADOR_EOI
    except OSError as e:
        raise ErrorEntrada(f"No se pudo leer {ruta}: {e}") from e

    if info["TipoSOF"] is None:
        raise ErrorEntrada(f"El archivo JPG no contiene un marcador SOF reconocible: {ruta}")

    info["TamanoArchivo"] = ruta.stat().st_size
    return info


def tabla_cabecera_jpg(cab: dict) -> str:
    if cab["ContenedorTipo"] == "JFIF":
        contenedor_txt = f"JFIF {cab['ContenedorVersion']}"
    elif cab["ContenedorTipo"] == "Exif":
        contenedor_txt = "Exif"
    else:
        contenedor_txt = "ninguno (solo SOI/EOI)"

    n = cab["NumComponentes"]
    componentes_txt = {1: "escala de grises", 3: "YCbCr, color", 4: "CMYK"}.get(n, f"{n} componentes")

    eoi_txt = "presente (0xFFD9, últimos 2 bytes del archivo)" if cab["EOI"] else "AUSENTE"

    lineas = [
        "---------------- CABECERA JPG (JFIF/Exif) ----------------",
        "Marcador SOI     : 0xFFD8 (offset 0)",
        f"Contenedor       : {contenedor_txt}",
        f"Tipo de trama    : {cab['TipoSOF']}",
        f"Dimensiones      : {cab['Ancho']} x {cab['Alto']} px ({cab['Ancho'] * cab['Alto']} píxeles)",
        f"Componentes      : {n} ({componentes_txt})",
        f"Precisión        : {cab['Precision']} bits/componente",
        f"Marcador EOI     : {eoi_txt}",
    ]
    return "\n".join(lineas)


def resumen_validacion_jpg(cab: dict) -> str:
    if cab["ContenedorTipo"] == "JFIF":
        return "JFIF"
    if cab["ContenedorTipo"] == "Exif":
        return "Exif"
    return "sin contenedor identificado (solo SOI/EOI)"


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
def graficar_histogramas(prob_bmp: np.ndarray, prob_jpg: np.ndarray,
                          ruta_bmp: Path, ruta_jpg: Path,
                          h_bmp: float, h_jpg: float) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, prob, etiqueta, ruta, h, color in (
            (axes[0], prob_bmp, "BMP (sin compresión)", ruta_bmp, h_bmp, "#2a6f97"),
            (axes[1], prob_jpg, "JPG (con compresión)",  ruta_jpg, h_jpg, "#e07a5f")):
        ax.bar(np.arange(256), prob, width=1.0, color=color, edgecolor="none")
        ax.set_xlim(-0.5, 255.5)
        ax.set_ylabel("Frecuencia relativa $p_i$")
        ax.set_title(f"{etiqueta} — {ruta.name} — H = {h:.4f} bits/byte | R = {redundancia(h)*100:.2f} %",
                     fontsize=10)
    axes[1].set_xlabel("Valor del byte (0–255)")
    fig.suptitle("Histograma de frecuencias relativas por valor de byte — BMP vs JPG", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    fig.savefig(RUTA_PNG, dpi=110, facecolor="white")


# --------------------------------------------------------------------------- #
# Paso 9 — Resumen final: consola + salida/resumen.txt
# --------------------------------------------------------------------------- #
def top_bytes(conteos: np.ndarray, n: int = 5) -> list[tuple[int, int]]:
    valores = sorted(range(256), key=lambda v: (-int(conteos[v]), v))[:n]
    return [(v, int(conteos[v])) for v in valores]


def resumen(ruta_bmp: Path, ruta_jpg: Path, cab_bmp: dict, cab_jpg: dict,
            conteos_bmp: np.ndarray, conteos_jpg: np.ndarray,
            h_bmp: float, h_jpg: float) -> str:
    tam_bmp = ruta_bmp.stat().st_size
    tam_jpg = ruta_jpg.stat().st_size

    compresion_txt = BMP_COMPRESION.get(cab_bmp["Compression"], f"{cab_bmp['Compression']} (desconocido)")

    simb_bmp = simbolos_distintos(conteos_bmp)
    simb_jpg = simbolos_distintos(conteos_jpg)
    r_bmp = redundancia(h_bmp)
    r_jpg = redundancia(h_jpg)

    total_bmp = int(conteos_bmp.sum())
    total_jpg = int(conteos_jpg.sum())
    top_bmp_txt = ", ".join(f"0x{v:02X}: {(c / total_bmp) * 100:.2f}%" for v, c in top_bytes(conteos_bmp))
    top_jpg_txt = ", ".join(f"0x{v:02X}: {(c / total_jpg) * 100:.2f}%" for v, c in top_bytes(conteos_jpg))

    factor = tam_bmp / tam_jpg
    razon = tam_jpg / tam_bmp

    return (
        "================ RESUMEN (Ejercicio 2) ================\n"
        f"BMP : {ruta_bmp}\n"
        f"   tamaño            : {tam_bmp} bytes ({tam_bmp / 1048576:.2f} MiB)\n"
        f"   formato           : {cab_bmp['BitCount']} bits/píxel, "
        f"{cab_bmp['Width']}x{abs(cab_bmp['Height'])} px, compresión {compresion_txt}\n"
        f"   símbolos distintos: {simb_bmp}/256\n"
        f"   entropía empírica : {h_bmp:.4f} bits/byte   (máximo teórico 8.0000)\n"
        f"   redundancia       : {r_bmp * 100:.2f} %\n"
        f"JPG : {ruta_jpg}\n"
        f"   tamaño            : {tam_jpg} bytes ({tam_jpg / 1048576:.2f} MiB)\n"
        f"   formato           : {cab_jpg['TipoSOF']}, "
        f"{cab_jpg['Ancho']}x{cab_jpg['Alto']} px, {cab_jpg['NumComponentes']} componente(s), "
        f"{cab_jpg['Precision']} bits\n"
        f"   símbolos distintos: {simb_jpg}/256\n"
        f"   entropía empírica : {h_jpg:.4f} bits/byte   (máximo teórico 8.0000)\n"
        f"   redundancia       : {r_jpg * 100:.2f} %\n"
        "COMPARACIÓN\n"
        f"   Δentropía (JPG − BMP)      : {h_jpg - h_bmp:+.4f} bits/byte\n"
        f"   factor de tamaño (BMP/JPG) : {factor:.2f}x   (razón JPG/BMP = {razon:.4f})\n"
        f"   bytes más frecuentes BMP   : {top_bmp_txt}\n"
        f"   bytes más frecuentes JPG   : {top_jpg_txt}\n"
        "=======================================================\n"
        f"Salida guardada: {RUTA_PNG}\n"
        f"                 {RUTA_RESUMEN}"
    )


if __name__ == "__main__":
    sys.exit(main())
