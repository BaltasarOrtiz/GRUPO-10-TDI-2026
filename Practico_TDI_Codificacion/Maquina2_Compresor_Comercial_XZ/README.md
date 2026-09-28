# Práctico de Máquina 2 — Compresor comercial: xz

Solución externa / de mercado asignada por sorteo (Sorteo B): **xz (XZ / LZMA2), nivel 6**.

**Estado:** pendiente de ejecutar y documentar.

No corresponde implementar nada acá: se usa la herramienta oficial (CLI `xz`) y se documenta la configuración empleada.

## Objetivos

- Correr `xz -6` sobre el mismo corpus de pruebas que la solución propia ([`../Maquina2_Compresor_Propio_RLE_Shannon/`](../Maquina2_Compresor_Propio_RLE_Shannon/)) y que el baseline de la cátedra (`gzip -n -6`).
- Documentar la configuración exacta utilizada (versión de `xz`, flags, nivel de compresión).
- Registrar tamaño original/comprimido, ratio, ahorro, tiempo de compresión y descompresión, throughput.
- Calcular el Weissman Score de xz respecto de gzip-6 (tiempos en milisegundos, α = 1).

## Pruebas a correr (corpus común de la cátedra)

| Prueba | Tipo | Finalidad |
|---|---|---|
| Prueba 1 | Archivo muy pequeño | Costo de cabecera; no entra en el ranking temporal |
| Prueba 2 | Texto natural | ≥ 1 MiB, distribución lingüística real |
| Prueba 3 | Alta repetición | ≥ 1 MiB con patrones y rachas repetidas |
| Prueba 4 | Baja repetición | ≥ 1 MiB, símbolos aproximadamente equiprobables |

## Estructura prevista

| Elemento | Contenido |
|---|---|
| `README.md` | Configuración de xz utilizada, versión, comandos exactos |
| `results/` | CSV/JSON/tablas con resultados del benchmark sobre xz |

Ver el enunciado completo en [`../Practico_TDI_Codificacion.pdf`](../Practico_TDI_Codificacion.pdf) (sección "Sorteo B — Soluciones externas / de mercado").
