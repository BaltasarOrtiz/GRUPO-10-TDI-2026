# Ejercicio 4 — Índice de Coincidencia (IC)

## Requisitos

- Python 3.9+
- `numpy`

## Instalación

```bash
pip install numpy
```

## Estructura de carpetas

```
ejercicio_4/
  ejercicio_4.py     # programa (CLI + análisis + resumen)
  README.md
  salida/            # la crea el programa en tiempo de ejecución
    resumen_corpus.txt.txt
    resumen_corpus.txt.zip.txt
```

Reutiliza `ejercicio_3/archivos/corpus.txt` y `corpus.txt.zip` (el
enunciado pide calcular el IC sobre los mismos archivos del punto
anterior); no se copian ni se regeneran acá.

## Uso

```bash
python3 ejercicio_4.py --archivo ../ejercicio_3/archivos/corpus.txt
python3 ejercicio_4.py --archivo ../ejercicio_3/archivos/corpus.txt.zip
```

Modo interactivo (sin `--archivo`, pide la ruta por teclado):

```bash
python3 ejercicio_4.py
```

## Qué hace el programa (puntos a–c)

- **a)** `calcular_ic` implementa el IC genérico, válido para cualquier
  alfabeto.
- **b)** Se ejecuta sobre los mismos archivos de `ejercicio_3`, en el
  alfabeto de 256 bytes y en el de 27 letras españolas.
- **c)** Imprime y guarda, por archivo, `H` e IC en ambos alfabetos.

## Respuestas teóricas (a–c)

**a)** `IC = Σf_i(f_i−1) / (N(N−1))`, con `f_i` la frecuencia de cada
símbolo y `N` el total. `calcular_ic` se implementa una sola vez y se
reutiliza sobre dos alfabetos: 256 valores de byte y las 27 letras del
español (a–z, ñ), extraídas normalizando acentos.

**b)** Se ejecuta sobre `ejercicio_3/archivos/corpus.txt` y
`corpus.txt.zip`, los mismos archivos del Ejercicio 3.

**c)** `H` e IC están inversamente relacionados: `H` es máxima e IC es
mínima (`1/k`) cuando la distribución es uniforme. En `corpus.txt` (texto
real, distribución desigual) `H` es baja e IC alta; en `corpus.txt.zip`
(casi uniforme tras DEFLATE) `H` es casi máxima e IC casi mínima.

## Resultados medidos

Corrida real contra los archivos de `ejercicio_3/archivos/` (evidencia en
`salida/resumen_corpus.txt.txt` y `salida/resumen_corpus.txt.zip.txt`):

| Métrica | corpus.txt | corpus.txt.zip |
|---|---|---|
| tamaño | 36147 bytes (0.03 MiB) | 12540 bytes (0.01 MiB) |
| H (bytes, k=256) | 4.4433 bits/símbolo | 7.9795 bits/símbolo |
| IC (bytes, k=256) | 0.064745 | 0.003938 |
| letras encontradas | 28736/36147 (79.50 %) | 5174/12540 (41.26 %) |
| codificación usada | UTF-8 | Latin-1 (fallback: no era UTF-8 válido) |
| H (letras, k=27) | 4.0290 bits/símbolo | 4.2701 bits/símbolo |
| IC (letras, k=27) | 0.073137 | 0.069335 |

Se cumple `IC_bytes(corpus.txt) = 0.064745 > IC_bytes(corpus.txt.zip) =
0.003938` e `IC_letras(corpus.txt) = 0.073137 > IC_letras(corpus.txt.zip)
= 0.069335`. `IC_bytes(zip) ≈ 0.003938` queda pegado al mínimo teórico
`1/256 ≈ 0.003906`, y `H_bytes(zip) = 7.9795` a solo 0.02 bits del máximo.

El IC de letras de `corpus.txt` (0.073137) coincide con la referencia de
español real (0.074). El de `corpus.txt.zip` (0.069335) no se acerca al
valor de referencia aleatorio (~0.038): al decodificarlo como Latin-1
(no es UTF-8 válido) y normalizar con NFD, varios bytes altos
(0xC0–0xFF) pliegan a vocales (12 bytes distintos pliegan a "a", pocos a
consonantes), sesgando la muestra de letras extraídas y elevando su IC.

## Archivos críticos

- `ejercicio_4/ejercicio_4.py` — programa único.
- No se crean archivos de entrada nuevos: se leen (sin modificar)
  `ejercicio_3/archivos/corpus.txt` y `ejercicio_3/archivos/corpus.txt.zip`.
