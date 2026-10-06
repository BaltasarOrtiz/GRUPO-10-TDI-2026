# Resumen del benchmark extra — ¿dónde rinde mejor RLE + Shannon?

Corpus propio del grupo, generado con semillas fijas por `benchmark_extra.py` (ver [`../corpus_extra/README_extra.txt`](../corpus_extra/README_extra.txt)). **No forma parte del corpus oficial de la cátedra ni del ranking**: es una prueba adicional para identificar en qué tipo de datos se destaca el algoritmo propio. Mismas tres soluciones y misma medición que `benchmark.py`.

## Ratio de compresión R por archivo

| Tipo de dato | Ejemplo real | Propio | xz-6 | gzip-6 | Propio vs. resto |
|---|---|---:|---:|---:|---|
| Señal digital de 2 niveles | bits de un canal, línea B/N de un fax | 124.14 | 96.95 | 81.40 | gana a xz y a gzip |
| Archivo disperso (99,5 % ceros) | matriz dispersa, disco casi vacío | 64.86 | 55.70 | 49.53 | gana a xz y a gzip |
| Registro de estados (4 valores) | estado de una máquina muestreado | 24.18 | 20.06 | 18.14 | gana a xz y a gzip |
| Imagen B/N con manchas | máscara, plano escaneado | 90.85 | 99.14 | 63.48 | gana a gzip |
| Imagen B/N tipo logo | logo, ícono, dibujo simple | 236.57 | 632.32 | 121.47 | gana a gzip |
| Sensor que mantiene su valor | temperatura, nivel de un tanque | 20.22 | 24.25 | 16.98 | gana a gzip |
| Audio 8 bits con silencios | grabación de voz con pausas | 4.70 | 6.67 | 5.61 | pierde |
| Texto de ancho fijo con relleno | log o reporte tabulado | 8.12 | 20.32 | 11.59 | pierde |

Integridad SHA-256: OK en todas las filas (24 = 3 soluciones × 8 archivos). Detalle completo (tamaños, tiempos, throughput) en `benchmark_extra_resultados.csv`.

## Interpretación

El algoritmo propio supera a gzip-6 (y en algunos casos también a xz-6) cuando el archivo tiene **rachas largas de bytes idénticos cuyo largo y orden no siguen un patrón que se repita**. xz y gzip comprimen buscando secuencias que ya aparecieron antes en el archivo (diccionario LZ); si las rachas tienen largos aleatorios, casi nunca encuentran una copia exacta y cada racha les cuesta una referencia nueva. RLE, en cambio, no necesita que nada se repita: cada racha se guarda como (símbolo, largo) y Shannon asigna códigos cortos a los símbolos y largos más frecuentes.

Cuando los datos tienen poca racha y mucha repetición a distancia (audio con forma de onda, texto con columnas y palabras que se repiten), la ventaja vuelve a ser de xz y gzip, igual que en el corpus oficial. Es el mismo principio que usa el fax (RLE + código de longitud variable) para documentos en blanco y negro.
