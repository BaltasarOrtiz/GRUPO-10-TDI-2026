# Resumen del benchmark — Práctico de Máquina 2

Corpus usado para el ranking temporal / Weissman Score global: prueba_2_texto_natural.txt, prueba_3_alta_repeticion.txt, prueba_4_baja_repeticion.txt (Prueba 1 queda excluida, según el enunciado).

## Weissman Score global (referencia = gzip -n -6)

- gzip-6 (referencia): W = 1.0000 (por definición)
- propio (RLE + Shannon): W = 0.0760  (R_global=1.3731, T_global=57.849 ms)
- xz-6: W = 0.4189  (R_global=3.5146, T_global=6.579 ms)
- gzip-6: R_global=3.4883, T_global=2.189 ms

## Resultados por archivo

| Archivo | Algoritmo | Original (B) | Comprimido (B) | R | A (%) | Integridad |
|---|---|---:|---:|---:|---:|---|
| prueba_1_pequena.txt | propio | 64 | 603 | 0.1061 | -842.19 | OK |
| prueba_1_pequena.txt | xz-6 | 64 | 112 | 0.5714 | -75.00 | OK |
| prueba_1_pequena.txt | gzip-6 | 64 | 59 | 1.0847 | 7.81 | OK |
| prueba_2_texto_natural.txt | propio | 102400 | 73465 | 1.3939 | 28.26 | OK |
| prueba_2_texto_natural.txt | xz-6 | 102400 | 1332 | 76.8769 | 98.70 | OK |
| prueba_2_texto_natural.txt | gzip-6 | 102400 | 1919 | 53.3611 | 98.13 | OK |
| prueba_3_alta_repeticion.txt | propio | 102400 | 47563 | 2.1529 | 53.55 | OK |
| prueba_3_alta_repeticion.txt | xz-6 | 102400 | 208 | 492.3077 | 99.80 | OK |
| prueba_3_alta_repeticion.txt | gzip-6 | 102400 | 914 | 112.0350 | 99.11 | OK |
| prueba_4_baja_repeticion.txt | propio | 102400 | 102703 | 0.9970 | -0.30 | OK |
| prueba_4_baja_repeticion.txt | xz-6 | 102400 | 85868 | 1.1925 | 16.14 | OK |
| prueba_4_baja_repeticion.txt | gzip-6 | 102400 | 85234 | 1.2014 | 16.76 | OK |

## Interpretación

En texto natural (Prueba 2), xz-6 alcanza R=76.88 y gzip-6 R=53.36, muy por encima de la solución propia (R=1.39): LZMA2/DEFLATE explotan repeticiones de largo alcance (frases y estructuras repetidas) que RLE, al operar solo sobre rachas de bytes consecutivos idénticos, no puede capturar.
En alta repetición (Prueba 3), la brecha se achica: propio logra R=2.15 aprovechando las rachas largas directamente, aunque xz-6 (R=492.31) sigue ganando por combinar coincidencias de largo alcance con Huffman/entropía sobre los literales.
En baja repetición / pseudoaleatorio (Prueba 4), la solución propia con R=1.00 no logra comprimir (R<1, el .tdi resulta más grande que el original), lo cual es esperable: sin rachas que explotar y con una distribución casi uniforme, ni RLE ni un codificador de entropía por símbolo pueden ganar espacio; xz-6 (R=1.19) tampoco gana mucho, por la misma razón de fondo (entropía cercana al máximo).
