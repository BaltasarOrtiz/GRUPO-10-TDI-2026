# Ejercicio 8 — Capacidad de Canal por Búsqueda Exhaustiva (Binario a Cuaternario)

## Requisitos

- Python 3.9+.
- Solo librería estándar (`argparse`, `math`, `sys`).

## Instalación

No hay dependencias que instalar.

## Uso

Con la matriz pasada por línea de comandos (8 valores `P(Y=j|X=i)`, separados por coma, fila por fila):

```bash
python3 ejercicio_8.py --matriz "0.7,0.1,0.1,0.1,0.1,0.7,0.1,0.1"
```

Con la traza completa de las 101 iteraciones de la búsqueda exhaustiva:

```bash
python3 ejercicio_8.py --matriz "0.7,0.1,0.1,0.1,0.1,0.7,0.1,0.1" --verbose
```

Sin `--matriz`, el programa pide los 8 valores uno por uno por teclado:

```bash
python3 ejercicio_8.py
```

## Qué hace el programa (puntos a–e)

- **a) Carga y validación de la matriz `P(Y|X)` (2×4).** `pedir_matriz_interactiva`/`parsear_matriz_cli` y `validar_matriz`.
- **b) Búsqueda exhaustiva.** `buscar_capacidad`, 101 pasos de `P(X=0)` entre `0.00` y `1.00`.
- **c) Cálculo dinámico de `P(Y)`, `H(Y)`, `H(Y|X)`, `I(X;Y)`.** `probabilidad_salida`, `entropia`, `entropia_condicional`, `informacion_mutua`.
- **d) Maximización.** Comparación `i_xy > mejor["i_xy"]` dentro de `buscar_capacidad`.
- **e) Reporte de la Capacidad.** Bloque `[4/4]` de `main()`.

## Respuestas teóricas (a–e)

**a) Matriz del canal.** `P(Y|X)` es `2×4`: cada fila es la distribución de salida dado el símbolo transmitido, y debe sumar 1 (tolerancia `1e-6` por punto flotante). `H(Y|X)` depende solo de esta matriz, no de `P(X)`.

**b) Búsqueda exhaustiva.** Con entrada binaria, `P(X)` queda determinada por `p₀ = P(X=0)`, así que barrer todas las distribuciones se reduce a un `for` de 101 valores (`0.00` a `1.00`, paso `0.01`). Es fuerza bruta sobre una grilla, no el óptimo analítico exacto.

**c) Información mutua por iteración.** `P(Y=j) = Σ_i P(X=i)·P(Y=j|X=i)` (Probabilidad Total); `H(Y)` es entropía de Shannon sobre `P(Y)`; `H(Y|X)` es el promedio ponderado de la entropía de cada fila; `I(X;Y) = H(Y) - H(Y|X)`.

**d) Maximización.** El bucle guarda el mejor `I(X;Y)` visto y lo reemplaza solo si aparece un valor estrictamente mayor.

**e) Capacidad de canal.** `C = max_{P(X)} I(X;Y)`. El mayor `I(X;Y)` de la búsqueda es la aproximación de `C` (limitada al paso de grilla `0.01`), y la `P(X)` que lo logra es la distribución óptima. Cota: como `H(X) ≤ 1` bit (entrada binaria), `C` nunca puede superar 1 bit/símbolo.

## Resultados medidos (casos de prueba)

Corridas reales de `python3 ejercicio_8.py --matriz "..."`:

| Matriz `P(Y|X)` | Tipo | `C` (bits/símbolo) | `P(X=0)` óptimo |
|---|---|---|---|
| `[[1,0,0,0],[0,1,0,0]]` | Determinista / sin ruido | 1.0000 | 0.50 |
| `[[0.7,0.1,0.1,0.1],[0.1,0.7,0.1,0.1]]` | Simétrico ("uniforme") | 0.3651 | 0.50 |
| `[[0.7,0.2,0.05,0.05],[0.1,0.1,0.3,0.5]]` | Asimétrico ("no uniforme") | 0.4206 | 0.51 |

Los dos primeros casos coinciden con lo esperado: canal determinista → `C = 1.0000` en `p₀ = 0.50`; canal simétrico → óptimo exactamente en `p₀ = 0.50`. El tercer caso confirma `0 ≤ C ≤ 1` y muestra que el óptimo se desplaza de `0.50` cuando la matriz no es simétrica.

## Archivos críticos y anclas

- `ejercicio_8/ejercicio_8.py` — archivo único. `parsear_argumentos`, `parsear_matriz_cli`/`pedir_matriz_interactiva`/`validar_matriz`, `entropia`/`probabilidad_salida`/`entropia_condicional`/`informacion_mutua`, `buscar_capacidad`, `main`.
- Enunciado: páginas 11–12 de `Practico_TDI_Info_Canal (2) (1).pdf` ("8. Cálculo de Capacidad de Canal por Búsqueda Exhaustiva").
