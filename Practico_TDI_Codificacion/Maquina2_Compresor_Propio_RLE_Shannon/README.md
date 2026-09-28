# Práctico de Máquina 2 — Compresor propio: RLE + Shannon

Algoritmo asignado por sorteo (Sorteo A, alternativa 2): **Repeticiones + estadística**. Representar rachas mediante RLE y codificar la salida utilizando Shannon, con reconstrucción completa.

**Estado:** implementado y verificado (tests unitarios y roundtrip completo sobre el corpus oficial).

## Objetivos

- Implementar en Python un compresor y un descompresor propios, sin delegar el núcleo del algoritmo a una librería de compresión.
- Definir qué información adicional necesita el método para descomprimir (cabecera, tabla de códigos, parámetros).
- Demostrar recuperación exacta del archivo original byte a byte (validación SHA-256).
- Medir y comparar contra la solución de mercado asignada ([`../Maquina2_Compresor_Comercial_XZ/`](../Maquina2_Compresor_Comercial_XZ/)) y contra el baseline de la cátedra (`gzip -n -6`), corriendo sobre el corpus oficial compartido en [`../corpus_pruebas/`](../corpus_pruebas/).

## Estructura del proyecto

| Elemento | Contenido |
|---|---|
| `tdi_format.py` | Núcleo del algoritmo: `BitWriter`/`BitReader`, RLE, construcción de tablas Shannon canónicas, empaquetado/lectura del formato `.tdi`. Reutilizado (importado en proceso) por `compressor.py`, `decompressor.py` y por `../benchmark.py` |
| `compressor.py` | CLI de compresión propia (RLE + Shannon), solo I/O, manejo de errores y mensajes de salida |
| `decompressor.py` | CLI de descompresión propia, solo I/O, manejo de errores y validación de integridad |
| `tests/test_tdi_format.py` | Suite `unittest`: BitWriter/BitReader, RLE (casos límite incluida racha > 256), tablas Shannon (Kraft, prefijo, caso degenerado), roundtrip completo (incluye las 4 pruebas de `../corpus_pruebas/`) |
| `README.md` | Este archivo |

No hay `requirements.txt`: todo el código usa exclusivamente la biblioteca estándar de Python (probado con Python 3.14).

Los resultados del benchmark comparativo (propio vs. xz vs. gzip-6) ya **no** viven en una carpeta `results/` local: se generan un nivel arriba, en [`../results/`](../results/), junto con el resto de las soluciones comparadas (ver [`../benchmark.py`](../benchmark.py) y [`../README.md`](../README.md)).

## Diseño del algoritmo

Pipeline: bytes originales → RLE → dos streams paralelos `symbols[]`/`runs[]` → tabla Shannon **independiente** por stream → bits intercalados por token (símbolo, luego racha) → empaquetado en `.tdi`.

### RLE

Cada token representa una racha de 1 a 256 repeticiones de un mismo byte: `symbols[i]` es el byte repetido y `runs[i] = longitud_de_racha - 1` (0-255). Rachas de más de 256 bytes se parten en tokens consecutivos del mismo símbolo (p. ej. una racha de 300 bytes idénticos se codifica como un token de racha 256 seguido de un token de racha 44).

### Shannon canónico

Para cada stream (`symbols[]` y `runs[]`, por separado) se calcula, para cada valor de byte que aparece, la longitud de codeword `l = ceil(-log2(p))` con `p = frecuencia/N` (caso degenerado de un único símbolo: se fuerza `l = 1`).

En vez de construir el codeword literalmente a partir de la expansión binaria de la probabilidad acumulada, los **bits concretos** se asignan con numeración canónica (la misma técnica que Huffman canónico): se ordenan los símbolos usados por `(longitud ascendente, valor ascendente)`, el primer codeword es `0`, y cada codeword siguiente es el anterior + 1, desplazado a la izquierda cuando aumenta la longitud. Esto sigue cumpliendo la desigualdad de Kraft (las longitudes son las mismas que las que exige Shannon) y produce un código libre de prefijos válido, pero simplifica muchísimo la reconstrucción del lado del decodificador: alcanza con guardar las 256 longitudes por stream en la cabecera, porque el decodificador reconstruye exactamente la misma tabla de codewords aplicando la misma numeración canónica. Esta simplificación ("Shannon canónico") está documentada acá porque es la única desviación consciente respecto de construir literalmente los bits vía la expansión binaria de la probabilidad acumulada — el resultado es equivalente en tasa de compresión (mismas longitudes) y mucho más simple y robusto de implementar/verificar (ver `tests/test_tdi_format.py::ShannonCanonicalTest`, que verifica Kraft y prefijo-libre para varias distribuciones, incluida la degenerada).

### Formato `.tdi`

Cabecera fija de 565 bytes (`4+8+8+32+256+256+1`), seguida del bitstream empaquetado:

| Campo | Tamaño | Contenido |
|---|---|---|
| `magic` | 4 B | `b"TDI1"` |
| `original_size` | 8 B | uint64 little-endian |
| `num_tokens` | 8 B | uint64 little-endian |
| `sha256_original` | 32 B | SHA-256 del archivo original, para la verificación de integridad |
| `symbol_code_lengths` | 256 B | longitud del codeword Shannon de cada valor de byte 0-255 en `symbols[]` (0 = no aparece) |
| `run_code_lengths` | 256 B | ídem para `runs[]` |
| `padding_bits` | 1 B | bits de relleno (0) agregados al final del bitstream para completar el último byte |
| bitstream | resto del archivo | codewords intercalados símbolo/racha por token, empaquetados MSB-first |

El `.tdi` es completamente autocontenido: `decompressor.py` no necesita el archivo original ni ningún estado externo.

## Uso

```
python3 compressor.py entrada.txt salida.tdi
python3 decompressor.py salida.tdi reconstruido.txt
```

Ejemplo real, corriendo sobre `../corpus_pruebas/prueba_2_texto_natural.txt` (100 KiB de texto natural en español):

```
$ python3 compressor.py ../corpus_pruebas/prueba_2_texto_natural.txt /tmp/p2.tdi
Entrada:  ../corpus_pruebas/prueba_2_texto_natural.txt
Salida:   /tmp/p2.tdi
Tamaño original:   102400 bytes
Tamaño comprimido: 73465 bytes
Ratio de compresión (R = original/comprimido): 1.3939
Espacio ahorrado (A): 28.26%
Tiempo de compresión: 65.030 ms

$ python3 decompressor.py /tmp/p2.tdi /tmp/p2_out.txt
Entrada:  /tmp/p2.tdi
Salida:   /tmp/p2_out.txt
Tamaño reconstruido: 102400 bytes
Tiempo de descompresión: 111.657 ms
Integridad: OK
```

Manejo de errores (sin tracebacks, códigos de salida distintos de cero): archivo de entrada inexistente, cabecera `.tdi` inválida o incompatible (magic bytes incorrectos), y archivo `.tdi` truncado/con datos insuficientes para completar la decodificación de los tokens declarados. Al finalizar la descompresión se imprime siempre el estado de integridad (`OK`/`FALLÓ`) según la comparación SHA-256(original) == SHA-256(reconstruido).

## Tests

```
python3 -m unittest discover Maquina2_Compresor_Propio_RLE_Shannon/tests
```

24 tests, cubren BitWriter/BitReader, RLE (vacío, un byte, racha > 256, sin repetición, mixto), construcción Shannon (Kraft, prefijo-libre, caso degenerado de un solo símbolo) y roundtrip completo compresor→descompresor (archivo vacío, casos armados a mano, y las 4 pruebas de `../corpus_pruebas/`).

Ver el enunciado completo en [`../Practico_TDI_Codificacion.pdf`](../Practico_TDI_Codificacion.pdf) (sección "Práctico de Máquina 2").
