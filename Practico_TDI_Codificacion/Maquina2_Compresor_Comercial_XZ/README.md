# Práctico de Máquina 2 — Compresor comercial: xz

Solución externa / de mercado asignada por sorteo (Sorteo B): **xz (XZ / LZMA2), nivel 6**.

**Estado:** ejecutado y documentado (ver [`../results/`](../results/) para los resultados numéricos y [`Documento_Funcional_XZ.md`](Documento_Funcional_XZ.md) para la explicación técnica del algoritmo y el análisis comparativo completo).

No corresponde implementar nada acá: se usa la herramienta oficial (CLI `xz`) y se documenta la configuración empleada.

## Objetivos

- Correr `xz -6` sobre el corpus oficial compartido en [`../corpus_pruebas/`](../corpus_pruebas/), el mismo que usan la solución propia ([`../Maquina2_Compresor_Propio_RLE_Shannon/`](../Maquina2_Compresor_Propio_RLE_Shannon/)) y el baseline de la cátedra (`gzip -n -6`).
- Documentar la configuración exacta utilizada (versión de `xz`, flags, nivel de compresión).
- Registrar tamaño original/comprimido, ratio, ahorro, tiempo de compresión y descompresión, throughput.
- Calcular el Weissman Score de xz respecto de gzip-6 (tiempos en milisegundos, α = 1).

## Configuración exacta utilizada

- Binario: `/opt/homebrew/bin/xz`, versión **5.8.4** (`liblzma 5.8.4`) — confirmado con `xz --version`, coincide con la última versión oficial publicada en [tukaani-project/xz](https://github.com/tukaani-project/xz).
- Compresión: `xz -6 -k -c entrada > salida.xz` (nivel 6, conserva el archivo original con `-k`, escribe a stdout con `-c`).
- Descompresión: `xz -d -c salida.xz > reconstruido`.
- Invocación real usada por [`../benchmark.py`](../benchmark.py): `subprocess.run(["xz", "-6", "-k", "-c"], input=data, stdout=subprocess.PIPE)` para compresión, y `["xz", "-d", "-c"]` para descompresión, cronometrando solo la llamada al proceso con `time.perf_counter()`.

## Ejemplo real

```
$ xz -6 -k -c ../corpus_pruebas/prueba_2_texto_natural.txt | wc -c
1332
```

102400 bytes → 1332 bytes (R ≈ 76.88, A ≈ 98.70%) sobre el texto natural de la Prueba 2. Ver [`../results/benchmark_resultados.csv`](../results/benchmark_resultados.csv) y [`../results/benchmark_resumen.md`](../results/benchmark_resumen.md) para el detalle completo (las 4 pruebas, throughput, Weissman Score global) generado por [`../benchmark.py`](../benchmark.py).

## Pruebas a correr (corpus común de la cátedra, en [`../corpus_pruebas/`](../corpus_pruebas/))

| Prueba | Archivo | Finalidad |
|---|---|---|
| Prueba 1 | `prueba_1_pequena.txt` (64 B) | Costo de cabecera; no entra en el ranking temporal |
| Prueba 2 | `prueba_2_texto_natural.txt` (100 KiB) | Texto natural en español, distribución lingüística real |
| Prueba 3 | `prueba_3_alta_repeticion.txt` (100 KiB) | Rachas largas y bloques repetidos |
| Prueba 4 | `prueba_4_baja_repeticion.txt` (100 KiB) | Pseudoaleatorio, distribución aprox. uniforme, semilla 2026 |

## Estructura

| Elemento | Contenido |
|---|---|
| `README.md` | Configuración de xz utilizada, versión, comandos exactos (este archivo) |
| `Documento_Funcional_XZ.md` | Explicación técnica de LZMA2, análisis comparativo completo (propio vs. xz vs. gzip-6) e interpretación del Weissman Score, para la entrega y la presentación |

Esta carpeta no tiene una subcarpeta `results/` propia: al comparar tres soluciones sobre el mismo corpus, los resultados del benchmark (CSV y resumen) se generan una sola vez, un nivel arriba, en [`../results/`](../results/), a partir de [`../benchmark.py`](../benchmark.py).

Ver el enunciado completo en [`../Practico_TDI_Codificacion.pdf`](../Practico_TDI_Codificacion.pdf) (sección "Sorteo B — Soluciones externas / de mercado").
