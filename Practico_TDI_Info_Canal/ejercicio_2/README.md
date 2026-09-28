# Ejercicio 2 — Análisis de Entropía, Histogramas y Estructura de Archivos (BMP vs JPG)

## Requisitos

- Python 3.9 o superior.
- matplotlib (arrastra numpy como dependencia).

```
pip install matplotlib
```
## Estructura de carpetas

```
ejercicio_2/
  ejercicio_2.py     # programa (CLI + análisis + gráfico + resumen)
  README.md
  imagenes/
    LEEME.txt
  salida/             # la crea el programa
    histogramas.png
    resumen.txt
```

## Uso

```
python3 ejercicio_2.py --bmp imagenes/foto.bmp --jpg imagenes/foto.jpg
```

Sin `--bmp`/`--jpg` el programa pide las rutas por teclado. `--no-show` no abre la ventana de matplotlib.

El programa imprime 6 fases (`[1/6]`–`[6/6]`): validación, cabecera BMP, cabecera JPG, distribuciones de probabilidad, entropía y generación de histogramas. Genera `salida/histogramas.png` y `salida/resumen.txt`.

## Qué hace el programa (puntos a–f)

- **a)** Valida extensión y firma de contenido: `leer_cabecera_bmp` exige `"BM"`; `leer_cabecera_jpg` exige SOI, un `SOFn` y EOI.
- **b)** `leer_cabecera_bmp` lee los 54 bytes fijos con `struct.unpack_from`; `leer_cabecera_jpg` recorre los marcadores JPEG con `seek`, sin decodificar el flujo Huffman.
- **c)** `contar_bytes` cuenta apariciones de cada byte; `a_probabilidades` normaliza a p(i) = c_i/N.
- **d)** `graficar_histogramas` dibuja los dos paneles (BMP/JPG).
- **e)** `entropia_shannon` calcula H(S) = -Σ p(i)·log2(p(i)).
- **f)** `resumen` compara entropías, redundancias y tamaños.

## Respuestas teóricas (a–f)

**a) Validación.** Extensión (`.bmp`/`.jpg`) + firma de contenido: BMP exige `0x42 0x4D` ("BM") en offset 0; JPG exige SOI `0xFFD8` en offset 0, un marcador `SOF` reconocible y EOI `0xFFD9` al final. La extensión sola no alcanza: un archivo renombrado la pasaría igual sin tener el contenido correcto.

**b) Cabecera BMP.** Cabecera fija de 54 bytes: BITMAPFILEHEADER (14 bytes) + BITMAPINFOHEADER (40 bytes), leída con `struct.unpack`. Coherencias verificadas: `FileSize` contra el tamaño real, `DataOffset` contra `54 + tamaño de paleta`, `BitCount` estándar.

**c) Distribución de probabilidad.** Se recorre el archivo completo (bloques de 1 MiB) contando apariciones `c_i` de cada valor de byte, `p(i) = c_i/N`. Se cuenta el archivo completo (cabecera + paleta + píxeles en BMP; todos los marcadores y el flujo Huffman en JPG), no solo los datos de imagen.

**d) Histogramas.** Dos paneles (BMP arriba, JPG abajo), eje x = valor de byte (0–255), eje y = frecuencia relativa; título con H y redundancia de cada uno. Se guarda en `salida/histogramas.png`.

**e) Entropía empírica.** `H(S) = −Σ_{i=0}^{255} p(i)·log₂p(i)` bits/byte, convención `0·log₂0=0`. Se cumple `0 ≤ H ≤ 8`. Redundancia `R = 1 − H/8`.

**f) Por qué difieren.** El BMP es un mapa de bits sin comprimir: una fotografía real tiene fuerte redundancia espacial (píxeles vecinos parecidos), lo que da un histograma con picos y `H` bien por debajo de 8. El JPG aplica DCT, cuantización con pérdida y, al final, codificación Huffman, que elimina la redundancia estadística: histograma casi plano y `H ≈ 8`. Mayor entropía en el JPG no significa más información útil, sino que su codificación ya está cerca del límite de incompresibilidad de Shannon.

## Resultados medidos

| Métrica | BMP | JPG |
|---|---|---|
| tamaño | 786488 bytes (0.75 MiB) | 50964 bytes (0.05 MiB) |
| formato | 24 bits/píxel, 512x512 px, compresión BI_RGB (sin compresión) | Baseline DCT, 512x512 px, 3 componente(s), 8 bits |
| símbolos distintos | 256/256 | 256/256 |
| entropía empírica (bits/byte) | 6.4148 | 7.9529 |
| redundancia (%) | 19.82 % | 0.59 % |
| Δentropía (JPG − BMP) | +1.5381 bits/byte | |
| factor de tamaño (BMP/JPG) | 15.43x (razón JPG/BMP = 0.0648) | |

Valores tomados de `salida/resumen.txt`, generado ejecutando:

```
python3 ejercicio_2.py --bmp imagenes/blue.bmp --jpg imagenes/blue.jpg --no-show
```

`imagenes/blue.jpg` se generó a partir de `blue.bmp` con Pillow (`Image.open(...).save(..., "JPEG", quality=85)`). Bytes más frecuentes: BMP `0xFF` con 15.05 % (imagen predominantemente clara/azul); JPG máximo 1.40 % por byte, reflejando el aplanado por codificación Huffman.
