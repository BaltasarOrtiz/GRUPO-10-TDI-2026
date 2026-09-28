"""Tests unitarios para tdi_format.py (RLE + Shannon canónico).

Correr con:
    python3 -m unittest discover Practico_TDI_Codificacion/Maquina2_Compresor_Propio_RLE_Shannon/tests
"""

from __future__ import annotations

import hashlib
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tdi_format  # noqa: E402

CORPUS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "corpus_pruebas",
)


class BitWriterReaderTest(unittest.TestCase):
    def test_roundtrip_arbitrary_bit_sequences(self):
        rng = random.Random(2026)
        for _ in range(50):
            fields = [(rng.getrandbits(l) if l > 0 else 0, l) for l in (rng.randint(1, 12) for _ in range(rng.randint(1, 20)))]
            writer = tdi_format.BitWriter()
            for value, length in fields:
                writer.write_bits(value, length)
            packed, padding = writer.getvalue()
            self.assertGreaterEqual(padding, 0)
            self.assertLess(padding, 8)

            reader = tdi_format.BitReader(packed)
            for value, length in fields:
                got = 0
                for _ in range(length):
                    got = (got << 1) | reader.read_bit()
                self.assertEqual(got, value)

    def test_empty_writer_produces_empty_output(self):
        writer = tdi_format.BitWriter()
        packed, padding = writer.getvalue()
        self.assertEqual(packed, b"")
        self.assertEqual(padding, 0)

    def test_reader_raises_on_exhausted_data(self):
        writer = tdi_format.BitWriter()
        writer.write_bits(0b101, 3)
        packed, _ = writer.getvalue()
        reader = tdi_format.BitReader(packed)
        with self.assertRaises(tdi_format.InsufficientDataError):
            for _ in range(9):
                reader.read_bit()


class RLETest(unittest.TestCase):
    def test_empty(self):
        symbols, runs = tdi_format.rle_encode(b"")
        self.assertEqual(symbols, b"")
        self.assertEqual(runs, b"")
        self.assertEqual(tdi_format.rle_decode(symbols, runs), b"")

    def test_single_byte(self):
        symbols, runs = tdi_format.rle_encode(b"x")
        self.assertEqual(symbols, b"x")
        self.assertEqual(runs, bytes([0]))
        self.assertEqual(tdi_format.rle_decode(symbols, runs), b"x")

    def test_long_run_splits_into_multiple_tokens(self):
        data = b"a" * 300
        symbols, runs = tdi_format.rle_encode(data)
        # 300 = 256 + 44 -> dos tokens
        self.assertEqual(symbols, b"aa")
        self.assertEqual(list(runs), [255, 43])
        self.assertEqual(tdi_format.rle_decode(symbols, runs), data)

    def test_exact_multiple_of_256(self):
        data = b"b" * 512
        symbols, runs = tdi_format.rle_encode(data)
        self.assertEqual(symbols, b"bb")
        self.assertEqual(list(runs), [255, 255])
        self.assertEqual(tdi_format.rle_decode(symbols, runs), data)

    def test_no_repetition(self):
        data = bytes(range(256))
        symbols, runs = tdi_format.rle_encode(data)
        self.assertEqual(symbols, data)
        self.assertEqual(runs, bytes([0]) * 256)
        self.assertEqual(tdi_format.rle_decode(symbols, runs), data)

    def test_mixed(self):
        data = b"aaabccccccddddddddddddddddddddddddddddddddddddddddddddddddddddddz"
        symbols, runs = tdi_format.rle_encode(data)
        self.assertEqual(tdi_format.rle_decode(symbols, runs), data)

    def test_random_roundtrip(self):
        rng = random.Random(7)
        data = bytes(rng.randint(0, 5) for _ in range(5000))  # alfabeto chico -> rachas
        symbols, runs = tdi_format.rle_encode(data)
        self.assertEqual(tdi_format.rle_decode(symbols, runs), data)


class ShannonCanonicalTest(unittest.TestCase):
    def _check_valid_code(self, data: bytes):
        lengths = tdi_format.compute_shannon_lengths(data)
        codes = tdi_format.canonical_codes_from_lengths(lengths)
        if data:
            self.assertGreater(len(codes), 0)
            for value, (length, _code) in codes.items():
                self.assertGreaterEqual(length, 1)
            kraft = tdi_format.kraft_sum(codes)
            self.assertLessEqual(kraft, 1.0 + 1e-9)
            self.assertTrue(tdi_format.is_prefix_free(codes))
        return codes

    def test_constant_array_gets_length_one(self):
        data = b"z" * 1000
        codes = self._check_valid_code(data)
        self.assertEqual(codes[ord("z")][0], 1)

    def test_uniform_distribution(self):
        data = bytes(range(256)) * 10
        self._check_valid_code(data)

    def test_skewed_distribution(self):
        data = b"a" * 900 + b"b" * 90 + b"c" * 9 + b"d"
        self._check_valid_code(data)

    def test_two_symbols(self):
        data = b"a" * 5 + b"b" * 3
        codes = self._check_valid_code(data)
        self.assertEqual(len(codes), 2)

    def test_random_frequencies(self):
        rng = random.Random(42)
        data = bytes(rng.randint(0, 255) for _ in range(20000))
        self._check_valid_code(data)

    def test_empty_data_has_no_codes(self):
        codes = self._check_valid_code(b"")
        self.assertEqual(codes, {})


class FullRoundtripTest(unittest.TestCase):
    def _assert_roundtrip(self, data: bytes):
        tdi_bytes = tdi_format.encode(data)
        reconstructed, header = tdi_format.decode(tdi_bytes)
        self.assertEqual(reconstructed, data)
        self.assertEqual(header.original_size, len(data))
        self.assertEqual(header.sha256_original, hashlib.sha256(data).digest())
        self.assertEqual(hashlib.sha256(reconstructed).digest(), header.sha256_original)

    def test_empty_file(self):
        self._assert_roundtrip(b"")

    def test_small_handcrafted_file(self):
        self._assert_roundtrip(b"El veloz murcielago hindu comia feliz cardillo y kiwi. AAAAAAAAAA!!")

    def test_single_byte(self):
        self._assert_roundtrip(b"\x00")

    def test_all_byte_values(self):
        self._assert_roundtrip(bytes(range(256)))

    def test_header_invalid_magic_raises(self):
        tdi_bytes = tdi_format.encode(b"hola mundo")
        corrupted = b"XXXX" + tdi_bytes[4:]
        with self.assertRaises(tdi_format.InvalidHeaderError):
            tdi_format.decode(corrupted)

    def test_truncated_file_raises_insufficient_data(self):
        tdi_bytes = tdi_format.encode(b"a" * 5000 + b"b" * 5000 + bytes(range(256)) * 20)
        truncated = tdi_bytes[: tdi_format.HEADER_SIZE + 3]
        with self.assertRaises(tdi_format.InsufficientDataError):
            tdi_format.decode(truncated)

    def test_file_shorter_than_header_raises_insufficient_data(self):
        with self.assertRaises(tdi_format.InsufficientDataError):
            tdi_format.decode(b"TDI1short")

    def test_corpus_files(self):
        if not os.path.isdir(CORPUS_DIR):
            self.skipTest(f"corpus_pruebas no encontrado en {CORPUS_DIR}")
        filenames = [
            "prueba_1_pequena.txt",
            "prueba_2_texto_natural.txt",
            "prueba_3_alta_repeticion.txt",
            "prueba_4_baja_repeticion.txt",
        ]
        for filename in filenames:
            path = os.path.join(CORPUS_DIR, filename)
            with self.subTest(filename=filename):
                with open(path, "rb") as f:
                    data = f.read()
                self._assert_roundtrip(data)


if __name__ == "__main__":
    unittest.main()
