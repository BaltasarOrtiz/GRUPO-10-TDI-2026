# Documento funcional — Solución de mercado: xz (XZ / LZMA2)

Práctico de Máquina 2 — Teoría de la Información, Grupo 10, 2026.

El presente documento complementa el [`README.md`](README.md) de esta carpeta, que especifica la configuración exacta y los comandos empleados, con la fundamentación técnica del algoritmo y el análisis comparativo requeridos por el enunciado para la solución de mercado asignada por sorteo.

## 1. Rol de la solución dentro del práctico

Conforme al escenario planteado por la cátedra, el grupo actúa como proveedor de dos soluciones de compresión (ver [`../README.md`](../README.md)):

- **Solución de autoría propia**: RLE + Shannon, implementada según lo asignado por Sorteo A ([`../Maquina2_Compresor_Propio_RLE_Shannon/`](../Maquina2_Compresor_Propio_RLE_Shannon/)).
- **Solución tercerizada / de mercado**: `xz`, asignada por Sorteo B. En este caso no corresponde implementación alguna: se utiliza la herramienta oficial disponible en el mercado y se documenta su configuración, su fundamento algorítmico y su desempeño frente al resto de las soluciones evaluadas.

Ambas soluciones se comparan entre sí y contra el compresor de referencia común de la cátedra, `gzip -n -6`.

## 2. Fundamento algorítmico de xz

`xz` es el formato de contenedor y la herramienta de línea de comandos del proyecto **XZ Utils** ([tukaani-project/xz](https://github.com/tukaani-project/xz)), que implementa el algoritmo **LZMA2**. La versión utilizada en el presente benchmark es la **5.8.4**, la cual coincide con el último release estable publicado en el repositorio oficial (`v5.8.4`), verificado mediante la API pública de GitHub al momento de redactar este documento.

LZMA2 combina dos técnicas de compresión estudiadas por separado en la cátedra:

1. **Compresión por diccionario (familia LZ77)**: un buscador de coincidencias recorre una ventana deslizante de gran tamaño — con el preset 6 empleado en este trabajo, el diccionario tiene **8 MiB** (dato verificado mediante `xz -vv`, filtro `lzma2=dict=8MiB,lc=3,lp=0,pb=2,mode=normal,nice=64,mf=bt4`) — y reemplaza secuencias de bytes previamente vistas dentro de esa ventana por referencias del tipo `(distancia, longitud)`. A diferencia de RLE, que únicamente detecta repeticiones de bytes consecutivos, este mecanismo permite localizar coincidencias en cualquier posición dentro de los 8 MiB precedentes del archivo.
2. **Codificación de entropía adaptativa (range coding)**: los literales y las referencias producidas por el paso anterior se codifican mediante un codificador de rango — una variante de codificación aritmética — cuyos modelos de probabilidad se actualizan de forma continua durante el procesamiento del archivo, en lugar de emplear una tabla estática calculada en una única pasada, como ocurre con el código Shannon canónico de la solución propia. Esta adaptabilidad permite ajustar la codificación a variaciones locales en la estadística de los datos.

La combinación de una ventana de búsqueda extensa con modelos de entropía adaptativos constituye el fundamento por el cual xz alcanza tasas de compresión sensiblemente superiores a las de un esquema RLE + Shannon estático.

## 3. Configuración utilizada

- Binario: `/opt/homebrew/bin/xz`, versión **5.8.4** (`liblzma 5.8.4`).
- Preset: **nivel 6** (`xz -6`), configuración por defecto de la herramienta y establecida como referencia por la cátedra.
- Compresión: `xz -6 -k -c entrada > salida.xz`.
- Descompresión: `xz -d -c salida.xz > reconstruido`.
- Invocación empleada en [`../benchmark.py`](../benchmark.py): `subprocess.run(["xz", "-6", "-k", "-c"], ...)`, cronometrando exclusivamente la llamada al proceso.

Detalle completo del filtro, obtenido mediante `xz -6 -vv`: `dict=8MiB, lc=3, lp=0, pb=2, mode=normal, nice=64, mf=bt4, depth=0`. No se aplicó la opción `--extreme` ni se modificó manualmente el filtro: se utilizó el preset 6 estándar, sin alteraciones, conforme a lo indicado por la cátedra.

## 4. Resultados sobre el corpus oficial

Datos extraídos de [`../results/benchmark_resultados.csv`](../results/benchmark_resultados.csv) (ver también [`../results/benchmark_resumen.md`](../results/benchmark_resumen.md)).

| Archivo | Original | Comprimido (xz) | R | Ahorro | T. compresión | T. descompresión | Throughput compresión |
|---|---:|---:|---:|---:|---:|---:|---:|
| Prueba 1 (64 B) | 64 B | 112 B | 0,5714 | −75,00 % | 5,107 ms | 2,879 ms | 0,01 MB/s |
| Prueba 2 (texto natural) | 100 KiB | 1 332 B | 76,877 | 98,70 % | 6,579 ms | 2,974 ms | 14,84 MB/s |
| Prueba 3 (alta repetición) | 100 KiB | 208 B | 492,308 | 99,80 % | 4,930 ms | 2,739 ms | 19,81 MB/s |
| Prueba 4 (baja repetición) | 100 KiB | 85 868 B | 1,193 | 16,14 % | 12,901 ms | 5,484 ms | 7,57 MB/s |

La verificación SHA-256(original) = SHA-256(reconstruido) resultó exitosa en las cuatro pruebas.

Respecto de la Prueba 1: al tratarse de un archivo de 64 bytes, el contenedor `.xz` (cabecera y pie de formato, aproximadamente 60 bytes fijos) supera en tamaño al contenido comprimido — el resultado obtenido (R < 1) es el esperado y, conforme indica el enunciado, no debe incluirse en el ranking temporal; su función es evidenciar el costo fijo del formato, no comparar velocidad.

## 5. Análisis comparativo (xz, solución propia y gzip-6)

| | R global (Pruebas 2-4) | T global (mediana, ms) | Weissman W (ref. gzip-6) |
|---|---:|---:|---:|
| gzip-6 (referencia) | 3,4883 | 2,398 | 1,0000 (por definición) |
| **xz-6** | **3,5146** | 5,932 | **0,4949** |
| Solución propia (RLE + Shannon) | 1,3731 | 65,030 | 0,0825 |

**Texto natural (Prueba 2):** xz obtiene R = 76,88, frente a R = 1,39 de la solución propia. La diferencia responde a una causa estructural: el archivo de prueba presenta redundancia a distancia (estructuras y secciones que se repiten a lo largo del texto), fenómeno que únicamente un compresor con diccionario de largo alcance, como LZMA2, puede aprovechar. RLE, al operar exclusivamente sobre bytes idénticos consecutivos, no detecta este tipo de redundancia, dado que el idioma español rara vez presenta caracteres repetidos en forma contigua.

**Alta repetición (Prueba 3):** la brecha relativa se reduce, aunque persiste en términos absolutos: la solución propia alcanza R = 2,15, dado que en este caso existen rachas extensas que RLE puede capturar directamente. No obstante, xz (R = 492,31) continúa siendo superior, dado que además de las coincidencias por diccionario aplica range coding adaptativo sobre los literales restantes, resultando en una codificación de entropía más precisa que la de una tabla Shannon estática.

**Baja repetición (Prueba 4):** con datos pseudoaleatorios de distribución aproximadamente uniforme, ninguna de las soluciones evaluadas logra una reducción significativa de tamaño (xz: R = 1,19; gzip: R = 1,20; solución propia: R ≈ 0,997). Este resultado es consistente con lo previsto por la teoría de la información: cuando la entropía de la fuente se aproxima al máximo teórico, no existe redundancia — ni por repetición ni estadística — susceptible de ser explotada por ningún algoritmo de compresión sin pérdida.

**Tiempos y throughput:** xz presenta tiempos de ejecución consistentemente menores que la solución propia sobre este corpus (T global de 5,9 ms frente a 65,0 ms), y resulta comparable a gzip pese a realizar un procesamiento considerablemente más complejo por byte (búsqueda de coincidencias en una ventana de 8 MiB junto con codificación de rango adaptativa). Corresponde señalar que xz es una implementación en lenguaje C, altamente optimizada, mientras que la solución propia es una implementación de referencia en Python sin optimizaciones de bajo nivel; en consecuencia, la comparación de throughput refleja en parte una diferencia de lenguaje e implementación, y no exclusivamente una diferencia algorítmica.

## 6. Interpretación del Weissman Score

Tomando gzip-6 como referencia (W = 1 por definición), xz obtiene un valor de **W ≈ 0,49**, inferior a la unidad pese a comprimir mejor que gzip en términos de ratio. Esto se explica porque la fórmula de Weissman pondera también el tiempo de ejecución, y en el presente corpus xz presenta un tiempo relativo mayor al de gzip (5,9 ms frente a 2,4 ms de mediana), aun siendo considerablemente más veloz que la solución propia. Esta última obtiene **W ≈ 0,08**, lo que refleja una desventaja simultánea en ratio y en tiempo respecto del baseline. Cabe remarcar que el Weissman Score constituye un indicador complementario, y no la única medida de calidad: debe interpretarse junto con el ratio, los tiempos y el throughput considerados de manera independiente, tal como señala el propio enunciado, dado que, tomado de forma aislada, podría sugerir erróneamente que gzip supera a xz cuando, en términos de compresión, la relación es la inversa.

## 7. Conclusiones

- xz (LZMA2) supera en ratio de compresión a la solución propia en las cuatro pruebas, y presenta tiempos de ejecución menores en las cuatro pruebas.
- La ventaja de xz resulta más pronunciada cuanto mayor es la redundancia de largo alcance presente en el archivo (texto natural, alta repetición), contexto en el cual el diccionario de 8 MiB y la codificación de entropía adaptativa determinan una diferencia sustancial frente a un esquema RLE + Shannon estático, limitado a rachas consecutivas.
- En archivos con entropía cercana al máximo teórico (Prueba 4), la ventaja de xz se reduce de manera considerable: ningún algoritmo de compresión sin pérdida puede reducir significativamente el tamaño de una fuente sin redundancia explotable, resultado que corrobora empíricamente lo previsto por la teoría de la información.
- El Weissman Score matiza esta lectura al ponderar el tiempo de ejecución, favoreciendo a gzip por sobre xz en el presente corpus aun cuando xz obtiene mejores tasas de compresión; dicha aparente contradicción debe explicitarse al momento de interpretar el indicador.

Para la fundamentación completa del enunciado, ver [`../Practico_TDI_Codificacion.pdf`](../Practico_TDI_Codificacion.pdf) (sección "Práctico de Máquina 2"). Para la configuración técnica y los comandos exactos, ver el [`README.md`](README.md) de esta carpeta.
