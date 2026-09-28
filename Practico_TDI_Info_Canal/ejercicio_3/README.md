# Ejercicio 3 — Entropía Empírica en Archivos (Texto vs. Comprimidos)

Programa Python que lee un archivo arbitrario byte por byte en tiempo O(N)
y calcula su entropía empírica de Shannon y su redundancia.

## Requisitos

- Python 3.9+
- numpy

## Instalación

```bash
pip install numpy
# o, en Debian/Ubuntu:
sudo apt install python3-numpy
```

## Estructura de carpetas

```
ejercicio_3/
  ejercicio_3.py     # programa (CLI + análisis + resumen)
  README.md
  archivos/
    LEEME.txt
    corpus.txt       # texto en español (~30-50 KB)
    corpus.txt.zip   # el mismo corpus.txt comprimido (ZIP_DEFLATED)
  salida/            # la crea el programa en tiempo de ejecución
    resumen_corpus.txt.txt
    resumen_corpus.txt.zip.txt
```

## Uso

```bash
python3 ejercicio_3.py --archivo archivos/corpus.txt
python3 ejercicio_3.py --archivo archivos/corpus.txt.zip
```

Modo interactivo (pide la ruta por teclado si se omite `--archivo`):

```bash
python3 ejercicio_3.py
```

## Qué hace el programa (puntos a–c)

- **a)** `contar_bytes` lee el archivo en bloques de 1 MiB y calcula la
  frecuencia relativa `p(i)` de cada uno de los 256 valores de byte y la
  entropía empírica de Shannon.
- **b)** Se ejecuta una vez con `archivos/corpus.txt` y otra con
  `archivos/corpus.txt.zip`.
- **c)** Ver "Respuestas teóricas".

## Respuestas teóricas (a–c)

**a)** El programa recorre el archivo en bloques de 1 MiB, cuenta las
apariciones `c_i` de cada uno de los 256 valores de byte y calcula
`p(i) = c_i/N`. La entropía empírica es `H(S) = −Σ p(i)·log₂p(i)`
(bits/byte), con `0 ≤ H ≤ log₂256 = 8`. Redundancia: `R = 1 − H/8`.
Complejidad: O(N) en tiempo, O(1) en memoria.

**b)** Se ejecuta el programa dos veces, una por archivo. Resultados en la
tabla de abajo.

**c)** El texto plano usa pocos símbolos con frecuencias muy desiguales
(espacio, "e", "a" dominan), por lo que `H` queda lejos de 8 bits/byte.
DEFLATE (LZ77 + Huffman) elimina esa redundancia: Huffman asigna códigos
de salida casi equiprobables, así que el `.zip` queda con `H` muy cercana
al máximo teórico.

## Resultados medidos

Corrida real sobre los archivos de `archivos/` (evidencia guardada en
`salida/resumen_corpus.txt.txt` y `salida/resumen_corpus.txt.zip.txt`):

| Métrica              | corpus.txt              | corpus.txt.zip           |
|-----------------------|--------------------------|---------------------------|
| Tamaño                | 36147 bytes (0.03 MiB)  | 12540 bytes (0.01 MiB)   |
| Símbolos distintos    | 90/256                   | 256/256                   |
| Entropía empírica H   | 4.4433 bits/byte         | 7.9795 bits/byte          |
| Redundancia           | 44.46 %                  | 0.26 %                    |
| Tiempo de lectura     | ≈ 0.0002 s               | ≈ 0.0001 s                |

Razón de tamaños: `corpus.txt.zip` pesa el 34.69 % de `corpus.txt`
(factor de compresión ≈ 2.88x).

`H(zip) = 7.9795 > H(txt) = 4.4433`, confirmando que DEFLATE elimina casi
toda la redundancia estadística del texto original.

## Archivos críticos

- `ejercicio_3/ejercicio_3.py` — programa completo.
- `ejercicio_3/archivos/` — archivos de entrada.
