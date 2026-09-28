# Práctico de Máquina 2 — Compresor propio: RLE + Shannon

Algoritmo asignado por sorteo (Sorteo A, alternativa 2): **Repeticiones + estadística**. Representar rachas mediante RLE y codificar la salida utilizando Shannon, con reconstrucción completa.

**Estado:** pendiente de implementar.

## Objetivos

- Implementar en Python un compresor y un descompresor propios, sin delegar el núcleo del algoritmo a una librería de compresión.
- Definir qué información adicional necesita el método para descomprimir (cabecera, tabla de códigos, parámetros).
- Demostrar recuperación exacta del archivo original byte a byte (validación SHA-256).
- Medir y comparar contra la solución de mercado asignada ([`../Maquina2_Compresor_Comercial_XZ/`](../Maquina2_Compresor_Comercial_XZ/)) y contra el baseline de la cátedra (`gzip -n -6`), corriendo sobre el corpus oficial compartido en [`../corpus_pruebas/`](../corpus_pruebas/).

## Estructura de proyecto prevista

| Elemento | Contenido mínimo |
|---|---|
| `compressor.py` | Implementación de la compresión propia (RLE + Shannon) |
| `decompressor.py` | Implementación de la descompresión propia |
| `benchmark.py` | Automatiza mediciones y genera resultados reproducibles |
| `README.md` | Algoritmo, instalación, uso, dependencias, formato `.tdi`, cabecera, baseline y ejemplos |
| `tests/` | Archivos de prueba, casos límite y resultados representativos |
| `results/` | CSV/JSON/tablas con resultados del benchmark del grupo |
| `requirements.txt` | Solo si hay dependencias externas de Python |

## Formato comprimido propio

A definir: extensión `.tdi`, cabecera mínima documentada (magic bytes, tamaño original, parámetros del algoritmo, tabla/modelo de códigos Shannon, bits significativos del último byte).

## Interfaz sugerida

```
python compressor.py entrada.txt salida_grupo.tdi
python decompressor.py salida_grupo.tdi reconstruido.txt
```

Salida mínima: archivo de entrada/salida, tamaño original y comprimido, ratio y ahorro, tiempo de compresión/descompresión, estado de integridad, parámetros relevantes del algoritmo.

Ver el enunciado completo en [`../Practico_TDI_Codificacion.pdf`](../Practico_TDI_Codificacion.pdf) (sección "Práctico de Máquina 2").
