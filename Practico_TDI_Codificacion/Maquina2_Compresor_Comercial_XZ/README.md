# Práctico de Máquina 2 — Compresor comercial: xz

Solución externa / de mercado asignada por sorteo (Sorteo B): **xz (XZ / LZMA2), nivel 6**.

**Estado:** pendiente de ejecutar y documentar.

No corresponde implementar nada acá: se usa la herramienta oficial (CLI `xz`) y se documenta la configuración empleada.

## Objetivos

- Correr `xz -6` sobre el corpus oficial compartido en [`../corpus_pruebas/`](../corpus_pruebas/), el mismo que usan la solución propia ([`../Maquina2_Compresor_Propio_RLE_Shannon/`](../Maquina2_Compresor_Propio_RLE_Shannon/)) y el baseline de la cátedra (`gzip -n -6`).
- Documentar la configuración exacta utilizada (versión de `xz`, flags, nivel de compresión).
- Registrar tamaño original/comprimido, ratio, ahorro, tiempo de compresión y descompresión, throughput.
- Calcular el Weissman Score de xz respecto de gzip-6 (tiempos en milisegundos, α = 1).

## Pruebas a correr (corpus común de la cátedra, en [`../corpus_pruebas/`](../corpus_pruebas/))

| Prueba | Archivo | Finalidad |
|---|---|---|
| Prueba 1 | `prueba_1_pequena.txt` (64 B) | Costo de cabecera; no entra en el ranking temporal |
| Prueba 2 | `prueba_2_texto_natural.txt` (100 KiB) | Texto natural en español, distribución lingüística real |
| Prueba 3 | `prueba_3_alta_repeticion.txt` (100 KiB) | Rachas largas y bloques repetidos |
| Prueba 4 | `prueba_4_baja_repeticion.txt` (100 KiB) | Pseudoaleatorio, distribución aprox. uniforme, semilla 2026 |

## Estructura prevista

| Elemento | Contenido |
|---|---|
| `README.md` | Configuración de xz utilizada, versión, comandos exactos |
| `results/` | CSV/JSON/tablas con resultados del benchmark sobre xz |

Ver el enunciado completo en [`../Practico_TDI_Codificacion.pdf`](../Practico_TDI_Codificacion.pdf) (sección "Sorteo B — Soluciones externas / de mercado").
