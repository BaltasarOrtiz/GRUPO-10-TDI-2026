# Ejercicio 6 — Medición de Distancia entre Cadenas (Hamming / Levenshtein)

## Requisitos

- Python 3.9+
- Solo librería estándar (`argparse`, `unicodedata`, `sys`).

## Instalación

No requiere instalar nada además del intérprete de Python.

## Uso

```bash
python3 ejercicio_6.py
```

Sin argumentos, corre la demo con los 3 casos del enunciado.

```bash
python3 ejercicio_6.py --a "cadena1" --b "cadena2"
```

Compara dos cadenas propias: Hamming (si las longitudes coinciden), Levenshtein, similitud porcentual, clasificación, y comparación normalizada.

## Qué hace el programa (puntos a–d)

- **a) Distancia de Hamming** — `distancia_hamming(a, b)`.
- **b) Distancia de Levenshtein** — `distancia_levenshtein(a, b)`.
- **c) Prueba con nombre mal tipeado** — `ejecutar_demo()`, Caso 3.
- **d) Heurística de comparación de texto** — `similitud()`, `clasificar_similitud()`, `normalizar()`.

## Respuestas teóricas (a–d)

**a) Distancia de Hamming.** Cuenta las posiciones en que dos cadenas de **igual longitud** difieren, `O(n)`. No está definida si las longitudes son distintas. Tampoco detecta bien un desfase (letra insertada/eliminada o transposición): cuenta varias posiciones distintas por un solo error real de tipeo.

**b) Distancia de Levenshtein.** Mínimo número de inserciones, eliminaciones y sustituciones para transformar una cadena en la otra. Programación dinámica, matriz `(n+1)×(m+1)`, `O(n·m)`. A diferencia de Hamming, admite cadenas de distinta longitud.

**c) Prueba con nombres mal tipeados.** `"Horacio Lopez"` vs `"Oracio Lopez"`: Levenshtein da **2**, no 1, porque la comparación es sensible a mayúsculas/minúsculas (al sacar la `H` queda `"oracio"` minúscula vs `"Oracio"` mayúscula). Tras normalizar (punto d) da 1.

**d) Propuesta de heurística para comparación de texto.** Pipeline de 3 pasos: (1) normalizar (minúsculas, sin acentos); (2) medir distancia de Levenshtein sobre el texto normalizado; (3) convertir a porcentaje de similitud (`1 - distancia / largo_máximo`) y clasificar con umbrales (`≥85 %` probable error de tipeo, `≥50 %` parcialmente similar, si no distintas).

## Resultados medidos (salida de la demo)

Salida real de `python3 ejercicio_6.py`:

```
=== Ejercicio 6: Distancia entre cadenas ===

[Caso 1] Distancia de Hamming -- mismo largo, transposicion de dos letras
  A: "Juan Perez"  (10 caracteres)
  B: "Jaun Perez"  (10 caracteres)
  Distancia de Hamming: 2
  (difieren en los indices 1 y 2: 'u' vs 'a', 'a' vs 'u' -- un solo error de tipeo humano, el intercambio de dos letras adyacentes, ya se cuenta como 2 posiciones distintas)

[Caso 2] Distancia de Hamming -- cadenas de distinta longitud (desfase real)
  A: "Juan Perez"  (10 caracteres)
  B: "Juann Perez"  (11 caracteres)
  Distancia de Hamming: ERROR -- Distancia de Hamming no aplicable: las cadenas tienen longitudes distintas (10 y 11). Un desfase (una letra de mas o de menos) desalinea todos los caracteres siguientes; Hamming compara posicion a posicion y no tiene forma de 'correr' el desfase, por eso ni siquiera esta definida en este caso.
  Distancia de Levenshtein: 1 (una sola insercion: la 'n' extra de 'Juann')
  Esto es lo que el enunciado pide demostrar: frente a un desfase de longitud, Hamming ni siquiera puede calcularse, mientras que Levenshtein sigue dando el resultado intuitivamente correcto.

[Caso 3] Distancia de Levenshtein -- nombre mal tipeado
  A: "Horacio Lopez"  (13 caracteres)
  B: "Oracio Lopez"  (12 caracteres)
  Distancia de Levenshtein: 2 (no es una sola eliminacion: al sacar la 'H' de 'Horacio' queda 'oracio' en minuscula, pero el destino tiene 'Oracio' con mayuscula inicial -- son 2 operaciones: 1 eliminacion + 1 sustitucion de mayuscula/minuscula)
  Similitud normalizada: 84.62 %  -> Parcialmente similares
  Tras normalizar (minusculas): distancia = 1 (ahi si es 1 sola eliminacion; ver punto d) -- muestra por que normalizar antes de medir es util)
```

## Archivos críticos y anclas

- `ejercicio_6/ejercicio_6.py` — archivo único. Anclas: `parsear_argumentos`, `distancia_hamming`, `distancia_levenshtein`, `similitud`/`clasificar_similitud`/`normalizar`, `ejecutar_demo`/`_mostrar_par`, `ejecutar_comparacion`, `main`.
- Enunciado: página 11 de `Practico_TDI_Info_Canal (2) (1).pdf` ("6. Medición de Distancia entre Cadenas").
