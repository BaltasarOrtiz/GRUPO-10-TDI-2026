"""Núcleo del formato .tdi: RLE + Shannon canónico.

Este módulo concentra la lógica compartida entre ``compressor.py`` y
``decompressor.py`` (y reutilizada por ``benchmark.py``, un nivel arriba).
No implementa el algoritmo de compresión delegando en ninguna librería de
terceros: usa únicamente la biblioteca estándar de Python.

Pipeline de compresión:

    bytes originales -> RLE -> dos streams paralelos (symbols[], runs[])
                      -> tabla Shannon independiente por stream
                      -> bits intercalados por token (símbolo, run)
                      -> empaquetado en el archivo .tdi

Ver el README de esta carpeta para el detalle del formato de cabecera y
de la construcción "Shannon canónico" usada acá.
"""

from __future__ import annotations

import math
import struct
from collections import Counter, namedtuple

# --------------------------------------------------------------------------
# Errores propios (para que compressor.py / decompressor.py puedan dar
# mensajes claros y códigos de salida distintos de cero, sin tracebacks).
# --------------------------------------------------------------------------


class TDIError(Exception):
    """Error base del formato .tdi."""


class InvalidHeaderError(TDIError):
    """La cabecera del archivo .tdi es inválida o incompatible."""


class InsufficientDataError(TDIError):
    """El archivo .tdi no contiene suficientes datos para completar la decodificación."""


# --------------------------------------------------------------------------
# Formato de cabecera
# --------------------------------------------------------------------------

MAGIC = b"TDI1"

# '<' = little-endian, sin relleno de alineación.
#   magic                4s
#   original_size        Q  (uint64)
#   num_tokens           Q  (uint64)
#   sha256_original      32s
#   symbol_code_lengths  256s
#   run_code_lengths     256s
#   padding_bits         B  (uint8)
HEADER_FORMAT = "<4sQQ32s256s256sB"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
assert HEADER_SIZE == 4 + 8 + 8 + 32 + 256 + 256 + 1  # 565 bytes

Header = namedtuple(
    "Header",
    [
        "original_size",
        "num_tokens",
        "sha256_original",
        "symbol_lengths",
        "run_lengths",
        "padding_bits",
    ],
)


# --------------------------------------------------------------------------
# BitWriter / BitReader — empaquetado MSB-first
# --------------------------------------------------------------------------


class BitWriter:
    """Empaqueta bits en un buffer de bytes, MSB primero."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._current = 0
        self._nbits = 0

    def write_bits(self, value: int, length: int) -> None:
        if length <= 0:
            return
        for i in range(length - 1, -1, -1):
            bit = (value >> i) & 1
            self._current = (self._current << 1) | bit
            self._nbits += 1
            if self._nbits == 8:
                self._buffer.append(self._current)
                self._current = 0
                self._nbits = 0

    def getvalue(self) -> tuple[bytes, int]:
        """Devuelve (bytes_empaquetados, bits_de_relleno_en_el_ultimo_byte)."""
        padding = 0
        if self._nbits > 0:
            padding = 8 - self._nbits
            self._buffer.append(self._current << padding)
        return bytes(self._buffer), padding


class BitReader:
    """Lee bits de un buffer de bytes, MSB primero."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0  # posición en bits
        self._total_bits = len(data) * 8

    def read_bit(self) -> int:
        if self._pos >= self._total_bits:
            raise InsufficientDataError(
                "fin de datos inesperado dentro del bitstream durante la decodificación"
            )
        byte_index = self._pos >> 3
        bit_index = 7 - (self._pos & 7)
        bit = (self._data[byte_index] >> bit_index) & 1
        self._pos += 1
        return bit


# --------------------------------------------------------------------------
# RLE
# --------------------------------------------------------------------------


def rle_encode(data: bytes) -> tuple[bytes, bytes]:
    """Codifica ``data`` como dos streams paralelos (symbols, runs).

    ``runs[i]`` almacena ``run_length - 1`` (0..255), de forma que cada
    token representa una racha de 1 a 256 repeticiones de ``symbols[i]``.
    Rachas más largas que 256 se parten en tokens consecutivos del mismo
    símbolo.
    """
    symbols = bytearray()
    runs = bytearray()
    n = len(data)
    i = 0
    while i < n:
        b = data[i]
        j = i + 1
        limit = i + 256
        while j < n and data[j] == b and j < limit:
            j += 1
        run_length = j - i
        symbols.append(b)
        runs.append(run_length - 1)
        i = j
    return bytes(symbols), bytes(runs)


def rle_decode(symbols: bytes, runs: bytes) -> bytes:
    """Reconstruye los bytes originales a partir de los streams (symbols, runs)."""
    out = bytearray()
    for s, r in zip(symbols, runs):
        out.extend(bytes((s,)) * (r + 1))
    return bytes(out)


# --------------------------------------------------------------------------
# Shannon canónico
# --------------------------------------------------------------------------


def compute_shannon_lengths(data: bytes) -> bytes:
    """Calcula, para cada valor de byte 0..255, la longitud de su codeword Shannon.

    l = ceil(-log2(p)), con p = f/N. Caso degenerado: si un único valor
    cubre todo el stream (p=1), se fuerza l=1 (todo codeword necesita al
    menos 1 bit). Devuelve un objeto bytes de 256 posiciones (0 = el valor
    no aparece en ``data``).
    """
    lengths = [0] * 256
    n = len(data)
    if n == 0:
        return bytes(lengths)

    freq = Counter(data)
    for value, f in freq.items():
        if f == n:
            length = 1
        else:
            p = f / n
            raw = -math.log2(p)
            # Guarda contra ruido de punto flotante que empuje un entero
            # exacto (p. ej. p potencia de 2) un paso más arriba de lo debido.
            length = math.ceil(raw - 1e-9)
            length = max(length, 1)
        lengths[value] = length
    return bytes(lengths)


def canonical_codes_from_lengths(lengths: bytes) -> dict[int, tuple[int, int]]:
    """Construye codewords canónicos a partir de las longitudes por símbolo.

    Numeración canónica (misma técnica que Huffman canónico): se ordenan
    los valores usados por (longitud ascendente, valor ascendente); el
    primer codeword es 0, y cada codeword siguiente es el anterior + 1,
    desplazado a la izquierda cuando aumenta la longitud.

    Devuelve {valor: (longitud, codeword_entero)}.
    """
    used = sorted(
        (value for value in range(256) if lengths[value] > 0),
        key=lambda v: (lengths[v], v),
    )
    codes: dict[int, tuple[int, int]] = {}
    code = 0
    prev_length = 0
    for value in used:
        length = lengths[value]
        code <<= length - prev_length
        codes[value] = (length, code)
        code += 1
        prev_length = length
    return codes


def _build_decode_table(
    codes: dict[int, tuple[int, int]]
) -> tuple[dict[tuple[int, int], int], int]:
    table = {(length, code): value for value, (length, code) in codes.items()}
    max_length = max((length for length, _ in codes.values()), default=0)
    return table, max_length


def _decode_one_symbol(
    reader: BitReader, table: dict[tuple[int, int], int], max_length: int
) -> int:
    code = 0
    for length in range(1, max_length + 1):
        code = (code << 1) | reader.read_bit()
        value = table.get((length, code))
        if value is not None:
            return value
    raise InvalidHeaderError(
        "no se encontró un codeword válido en la tabla Shannon (datos corruptos)"
    )


# --------------------------------------------------------------------------
# Verificación de Kraft / prefijo (usada también por los tests)
# --------------------------------------------------------------------------


def kraft_sum(codes: dict[int, tuple[int, int]]) -> float:
    return sum(2.0 ** -length for length, _ in codes.values())


def is_prefix_free(codes: dict[int, tuple[int, int]]) -> bool:
    bitstrings = [format(code, f"0{length}b") for length, code in codes.values()]
    for i, a in enumerate(bitstrings):
        for j, b in enumerate(bitstrings):
            if i != j and b.startswith(a):
                return False
    return True


# --------------------------------------------------------------------------
# Encode / decode de alto nivel (formato .tdi completo)
# --------------------------------------------------------------------------


def encode(data: bytes) -> bytes:
    """Comprime ``data`` (bytes originales) y devuelve el contenido completo del .tdi."""
    import hashlib

    symbols, runs = rle_encode(data)
    num_tokens = len(symbols)

    symbol_lengths = compute_shannon_lengths(symbols)
    run_lengths = compute_shannon_lengths(runs)

    symbol_codes = canonical_codes_from_lengths(symbol_lengths)
    run_codes = canonical_codes_from_lengths(run_lengths)

    writer = BitWriter()
    for i in range(num_tokens):
        s_len, s_code = symbol_codes[symbols[i]]
        writer.write_bits(s_code, s_len)
        r_len, r_code = run_codes[runs[i]]
        writer.write_bits(r_code, r_len)
    bitstream, padding_bits = writer.getvalue()

    sha256_original = hashlib.sha256(data).digest()

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        len(data),
        num_tokens,
        sha256_original,
        symbol_lengths,
        run_lengths,
        padding_bits,
    )
    return header + bitstream


def parse_header(tdi_bytes: bytes) -> Header:
    if len(tdi_bytes) < HEADER_SIZE:
        raise InsufficientDataError(
            f"el archivo tiene {len(tdi_bytes)} bytes, menos que la cabecera "
            f"mínima esperada de {HEADER_SIZE} bytes"
        )
    (
        magic,
        original_size,
        num_tokens,
        sha256_original,
        symbol_lengths,
        run_lengths,
        padding_bits,
    ) = struct.unpack(HEADER_FORMAT, tdi_bytes[:HEADER_SIZE])

    if magic != MAGIC:
        raise InvalidHeaderError(
            f"magic bytes inválidos: se esperaba {MAGIC!r}, se encontró {magic!r} "
            "(¿el archivo no es un .tdi o está corrupto?)"
        )
    if padding_bits > 7:
        raise InvalidHeaderError(
            f"padding_bits fuera de rango (0-7): {padding_bits}"
        )
    if num_tokens > 0:
        if not any(symbol_lengths) or not any(run_lengths):
            raise InvalidHeaderError(
                "la cabecera declara tokens pero la tabla de longitudes Shannon está vacía"
            )

    return Header(
        original_size,
        num_tokens,
        sha256_original,
        symbol_lengths,
        run_lengths,
        padding_bits,
    )


def decode(tdi_bytes: bytes) -> tuple[bytes, Header]:
    """Descomprime el contenido completo de un .tdi y devuelve (bytes_originales, Header).

    Levanta ``InvalidHeaderError`` si la cabecera es inválida/incompatible, o
    ``InsufficientDataError`` si el archivo está truncado y no alcanza para
    completar la decodificación de los ``num_tokens`` declarados.
    """
    header = parse_header(tdi_bytes)
    bitstream = tdi_bytes[HEADER_SIZE:]

    if header.num_tokens == 0:
        return b"", header

    symbol_codes = canonical_codes_from_lengths(header.symbol_lengths)
    run_codes = canonical_codes_from_lengths(header.run_lengths)
    symbol_table, symbol_max_len = _build_decode_table(symbol_codes)
    run_table, run_max_len = _build_decode_table(run_codes)

    reader = BitReader(bitstream)
    symbols = bytearray(header.num_tokens)
    runs = bytearray(header.num_tokens)
    for i in range(header.num_tokens):
        symbols[i] = _decode_one_symbol(reader, symbol_table, symbol_max_len)
        runs[i] = _decode_one_symbol(reader, run_table, run_max_len)

    data = rle_decode(bytes(symbols), bytes(runs))
    return data, header
