# Práctico TDI — Codificación (Práctico de Máquina 2)

Licenciatura en Ciencias de la Computación, 2026.

Enunciado: [`Practico_TDI_Codificacion.pdf`](Practico_TDI_Codificacion.pdf).

## Contenido

| Carpeta | Tema |
|---|---------|
| [`Ejercicios_Practicos/`](Ejercicios_Practicos/) | Ejercicios de lápiz y papel de los Prácticos 3 y 4: códigos, Kraft, Shannon/Fano/Huffman, LZ/LZW, codificación aritmética, fuentes de Markov, pipeline BWT→RLE→Huffman |
| [`Maquina2_Compresor_Propio_RLE_Shannon/`](Maquina2_Compresor_Propio_RLE_Shannon/) | Práctico de Máquina 2, apartado 1 — algoritmo propio asignado por sorteo: RLE + Shannon |
| [`Maquina2_Compresor_Comercial_XZ/`](Maquina2_Compresor_Comercial_XZ/) | Práctico de Máquina 2, apartado 2 — solución de mercado asignada por sorteo: xz (XZ/LZMA2) |
| [`corpus_pruebas/`](corpus_pruebas/) | Corpus oficial de la cátedra (4 pruebas), compartido por las tres soluciones comparadas |

## Práctico de Máquina 2 en resumen

El grupo actúa como "proveedor" y ofrece dos soluciones de compresión evaluadas sobre el mismo corpus, más un baseline común de la cátedra:

1. **Solución propia** (RLE + Shannon): compresor/descompresor en Python implementados por el grupo, sin delegar el núcleo del algoritmo a una librería.
2. **Solución de mercado asignada** (xz): no se implementa, se usa la herramienta oficial documentando su configuración (nivel 6).
3. **Baseline de la cátedra**: `gzip -n -6`, igual para todos los grupos, usado como referencia para el Weissman Score.

Ambas soluciones (propia y xz) se comparan entre sí y contra el baseline sobre las 4 pruebas de [`corpus_pruebas/`](corpus_pruebas/) (archivo chico, texto natural, alta repetición, baja repetición), con validación de integridad SHA-256 byte a byte contra los hashes de [`corpus_pruebas/README_pruebas.txt`](corpus_pruebas/README_pruebas.txt). Los resultados alimentan una tabla comparativa y una presentación grupal.

**Importante:** los archivos de `corpus_pruebas/` son los oficiales de la cátedra y no deben modificarse; todos los grupos deben evaluar exactamente los mismos bytes.

**Fecha de entrega:** martes 6 de octubre de 2026.
