# Ejercicio 1 — Análisis de Información en Señales de Audio (WAV)

## Requisitos

- Python 3.9 o superior.
- matplotlib (arrastra numpy como dependencia).

```
pip install matplotlib
```

En Debian/Ubuntu: `sudo apt install python3-matplotlib`.

Sin salida gráfica (`DISPLAY` ausente), usar `--no-show`: genera igual el PNG sin abrir la ventana.

El programa **no decodifica** el MP3: el análisis es estadístico sobre los bytes del archivo. La comparación entre WAV y MP3 solo vale si ambos contienen la misma pista.

## Estructura de carpetas

```
ejercicio_1/
  ejercicio_1.py     # programa (CLI + análisis + gráfico + resumen)
  README.md
  audio/
    sample-15s.wav
    sample-15s.mp3
  salida/             # la crea el programa
    histogramas.png
    resumen.txt
```

## Uso

```
python3 ejercicio_1.py --wav audio/pista.wav --mp3 audio/pista.mp3
```

Sin `--wav`/`--mp3` el programa pide las rutas por teclado. `--no-show` no abre la ventana de matplotlib.

Ejemplo usado en este repositorio:

```
python3 ejercicio_1.py --wav audio/sample-15s.wav --mp3 audio/sample-15s.mp3
```

El programa imprime 6 fases (`[1/6]`–`[6/6]`): validación, cabecera WAV, cabecera MP3, distribuciones de probabilidad, entropía y generación de histogramas. Genera `salida/histogramas.png` y `salida/resumen.txt`.

## Qué hace el programa (puntos a–f)

- **a)** Valida extensión y firma de contenido (`validar_extension`, `leer_cabecera_wav`, `leer_cabecera_mp3`).
- **b)** `leer_cabecera_wav` recorre los chunks RIFF con `seek`; `volcado_hex`/`tabla_cabecera_wav` muestran cabecera y coherencias.
- **c)** `contar_bytes` cuenta apariciones de cada byte; `a_probabilidades` normaliza a p(i) = c_i/N.
- **d)** `graficar_histogramas` dibuja los dos paneles (WAV/MP3).
- **e)** `entropia_shannon` calcula H(S) = -Σ p(i)·log2(p(i)).
- **f)** `resumen` compara entropías, redundancias y tamaños.

## Respuestas teóricas (a–f)

**a) Validación.** Extensión (`.wav`/`.mp3`) + firma de contenido: WAV exige `RIFF` en bytes 0–3 y `WAVE` en 8–11; MP3 exige ID3v2 o sincronización de trama MPEG (11 bits en 1). La extensión sola no alcanza: un archivo renombrado la pasaría igual sin tener el contenido correcto.

**b) Cabecera WAV.** Se recorren los chunks RIFF con `seek`, sin cargar el archivo completo, hasta ubicar `fmt ` y `data`. Coherencias verificadas: `ChunkSize+8 == tamaño del archivo`, `BlockAlign == NumChannels·BitsPerSample/8`, `ByteRate == SampleRate·BlockAlign`. Duración = `Subchunk2Size / ByteRate`.

**c) Distribución de probabilidad.** Se recorre el archivo completo (bloques de 1 MiB) contando apariciones `c_i` de cada valor de byte `i ∈ [0,255]`; `p(i) = c_i/N`, con `Σp(i) = 1`.

**d) Histogramas.** Dos paneles (WAV arriba, MP3 abajo), eje x = valor de byte (0–255), eje y = frecuencia relativa; título con H y redundancia de cada uno. Se guarda en `salida/histogramas.png`.

**e) Entropía empírica.** `H(S) = −Σ_{i=0}^{255} p(i)·log₂p(i)` bits/byte, convención `0·log₂0=0`. Se cumple `0 ≤ H ≤ 8`; el máximo solo si los 256 valores son equiprobables. Redundancia `R = 1 − H/8`.

**f) Por qué difieren.** El WAV es PCM sin comprimir: las muestras tienen fuerte correlación temporal y amplitud concentrada, lo que da un histograma con picos y `H` bien por debajo de 8. El MP3 termina en codificación Huffman, que elimina la redundancia estadística: histograma casi plano y `H ≈ 8`. Mayor entropía en el MP3 no significa más información útil, sino que su codificación ya está cerca del límite de incompresibilidad de Shannon.

## Resultados medidos

| Métrica | WAV | MP3 |
|---|---|---|
| tamaño | 3382316 bytes (3.23 MiB) | 381645 bytes (0.36 MiB) |
| formato | PCM 16 bits/muestra, 2 canal(es), 44100 Hz | MPEG-1 Layer III, 64 kbps, 44100 Hz, Estéreo |
| duración | 00:19.174 | no calculada (el programa no decodifica el MP3) |
| símbolos distintos | 256/256 | 256/256 |
| entropía empírica (bits/byte) | 7.3228 | 7.9124 |
| redundancia (%) | 8.47 % | 1.10 % |
| Δentropía (MP3 − WAV) | +0.5896 bits/byte | |
| factor de tamaño (WAV/MP3) | 8.86x (razón MP3/WAV = 0.1128) | |

Valores tomados de `salida/resumen.txt`, generado ejecutando:

```
python3 ejercicio_1.py --wav audio/sample-15s.wav --mp3 audio/sample-15s.mp3 --no-show
```

con los archivos de audio reales provistos en `ejercicio_1/audio/`.
