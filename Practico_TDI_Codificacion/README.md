# Práctico TDI — Codificación (Práctico de Máquina 2)

Licenciatura en Ciencias de la Computación, 2026.

Enunciado: [`Practico_TDI_Codificacion.pdf`](Practico_TDI_Codificacion.pdf).

## Contenido

| Carpeta / archivo | Tema |
|---|---------|
| [`Ejercicios_Practicos/`](Ejercicios_Practicos/) | Ejercicios de lápiz y papel de los Prácticos 3 y 4: códigos, Kraft, Shannon/Fano/Huffman, LZ/LZW, codificación aritmética, fuentes de Markov, pipeline BWT→RLE→Huffman |
| [`Maquina2_Compresor_Propio_RLE_Shannon/`](Maquina2_Compresor_Propio_RLE_Shannon/) | Práctico de Máquina 2, apartado 1 — algoritmo propio asignado por sorteo: RLE + Shannon (`compressor.py`/`decompressor.py`, formato `.tdi`, tests) |
| [`Maquina2_Compresor_Comercial_XZ/`](Maquina2_Compresor_Comercial_XZ/) | Práctico de Máquina 2, apartado 2 — solución de mercado asignada por sorteo: xz (XZ/LZMA2), nivel 6 |
| [`corpus_pruebas/`](corpus_pruebas/) | Corpus oficial de la cátedra (4 pruebas), compartido por las tres soluciones comparadas |
| [`benchmark.py`](benchmark.py) | Corre las tres soluciones (propio, xz-6, gzip-6) sobre las 4 pruebas del corpus y escribe los resultados en [`results/`](results/) |
| [`results/`](results/) | `benchmark_resultados.csv` y `benchmark_resumen.md` generados por `benchmark.py`; resultados compartidos por las tres soluciones (no hay una carpeta `results/` separada dentro de cada solución) |

## Práctico de Máquina 2 en resumen

El grupo actúa como "proveedor" y ofrece dos soluciones de compresión evaluadas sobre el mismo corpus, más un baseline común de la cátedra:

1. **Solución propia** (RLE + Shannon): compresor/descompresor en Python implementados por el grupo, sin delegar el núcleo del algoritmo a una librería.
2. **Solución de mercado asignada** (xz): no se implementa, se usa la herramienta oficial documentando su configuración (nivel 6).
3. **Baseline de la cátedra**: `gzip -n -6`, igual para todos los grupos, usado como referencia para el Weissman Score.

Ambas soluciones (propia y xz) se comparan entre sí y contra el baseline sobre las 4 pruebas de [`corpus_pruebas/`](corpus_pruebas/) (archivo chico, texto natural, alta repetición, baja repetición), con validación de integridad SHA-256 byte a byte contra los hashes de [`corpus_pruebas/README_pruebas.txt`](corpus_pruebas/README_pruebas.txt). Los resultados alimentan una tabla comparativa y una presentación grupal.

**Importante:** los archivos de `corpus_pruebas/` son los oficiales de la cátedra y no deben modificarse; todos los grupos deben evaluar exactamente los mismos bytes.

## Resultado del benchmark (resumen)

Corriendo `python3 benchmark.py` (ver [`results/benchmark_resumen.md`](results/benchmark_resumen.md) para el detalle completo): sobre las Pruebas 2, 3 y 4 (Prueba 1 excluida del ranking temporal, según enunciado), xz-6 obtiene el mejor Weissman Score global (≈0.49 respecto de gzip-6=1.0), seguido por la solución propia RLE + Shannon (≈0.08). La solución propia comprime razonablemente cuando hay rachas explotables (R≈2.15 en alta repetición, R≈1.39 en texto natural gracias a las rachas cortas típicas del español), pero no logra competir con LZMA2/DEFLATE en texto natural o alta repetición porque el RLE solo ve repeticiones consecutivas y no coincidencias de largo alcance; en el archivo pseudoaleatorio de baja repetición ninguna de las tres soluciones gana espacio de forma significativa (R cercano a 1), como es esperable cuando la entropía de la fuente es casi máxima.

**Fecha de entrega:** martes 6 de octubre de 2026.
