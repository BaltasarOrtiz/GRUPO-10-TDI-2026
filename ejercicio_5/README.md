# Ejercicio 5 — Eficiencia de Almacenamiento y Empaquetado a Nivel de Bits (Bitwise)

## Requisitos

- Python 3.9+
- Solo librería estándar (`csv`, `struct`, `argparse`, `pathlib`)

## Instalación

Nada que instalar: solo un intérprete de Python 3.

## Estructura de carpetas

```
ejercicio_5/
  ejercicio_5.py     # programa (subcomandos "generar" y "leer")
  README.md
  salida/            # la crea "generar" en tiempo de ejecución
    personas_variable.csv   # longitud variable (paso a)
    personas_fijo.bin       # longitud fija, bitwise (paso b)
    resumen.txt              # comparación de tamaños (paso c)
```

## Uso

```bash
python3 ejercicio_5.py generar
python3 ejercicio_5.py leer --formato texto
python3 ejercicio_5.py leer --formato binario
```

`generar` crea `salida/`, escribe el CSV y el binario a partir de
`PERSONAS` (20 personas ficticias) y guarda la comparación de tamaños en
`salida/resumen.txt`. `leer --formato texto|binario` muestra las 20
personas en pantalla.

## Qué hace el programa (puntos a–d)

- **a)** `escribir_csv` guarda las personas en CSV; `leer_csv` las relee
  con `csv.DictReader`.
- **b)** `escribir_binario` guarda registros de tamaño fijo;
  `empaquetar_booleanos` comprime los 8 booleanos en 1 byte con
  operadores bitwise.
- **c)** `comparar_tamanos` calcula tamaños, ahorro y proyección a
  escala.
- **d)** `leer_binario` valida el tamaño del archivo y usa
  `desempaquetar_booleanos` para recuperar los 8 booleanos.

## Respuestas teóricas (a–d)

**a)** El CSV tiene una fila por persona; cada fila ocupa un tamaño
distinto porque nombre, dirección y booleanos como texto (`"True"` /
`"False"`) tienen longitud variable.

**b)** El binario usa registros de tamaño fijo (95 bytes: 40 nombre + 50
dirección + 4 DNI + 1 booleanos), lo que permite acceso directo al
registro `i` con `seek(i * 95)`. Los 8 booleanos se empaquetan en 1 byte:
`byte |= (1 << i)` para escribir, `byte & (1 << i)` para leer. Es la
representación mínima: un booleano tiene como máximo 1 bit de
información (`log₂2 = 1`), así que 8 booleanos caben exactos en 1 byte.

**c)** CSV: 2422 bytes (121.10 bytes/persona). Binario: 1900 bytes (95
bytes/persona, fijo). Ahorro: 522 bytes (21.55 %). El campo de 8
booleanos usa hasta 47 bytes en texto contra 1 byte en binario (~46x).
Proyectado a escala: 24.9 MiB de diferencia en 1.000.000 de personas,
248.9 MiB en 10.000.000.

**d)** `leer_csv` reconstruye los booleanos comparando contra `"True"`.
`leer_binario` valida que el tamaño del archivo sea múltiplo del tamaño
de registro y usa `struct.unpack` + `desempaquetar_booleanos` para
recuperar los 8 booleanos originales. Ambos caminos devuelven los mismos
datos que `PERSONAS`.

## Resultados medidos

Valores tomados de `salida/resumen.txt` de la corrida real (20 personas):

| Métrica                              | CSV (variable) | Binario (fijo) |
|---------------------------------------|----------------|-----------------|
| Tamaño total                          | 2422 bytes     | 1900 bytes      |
| Bytes/persona (promedio / fijo)       | 121.10         | 95              |
| Ahorro absoluto del binario           | 522 bytes                        |
| Ahorro porcentual del binario         | 21.55 %                          |
| Proyección a 1.000.000 de personas    | 24.9 MiB de diferencia           |
| Proyección a 10.000.000 de personas   | 248.9 MiB de diferencia          |

## Archivos críticos

- `ejercicio_5/ejercicio_5.py` — archivo único.
- Enunciado: páginas 10–11 de `Practico_TDI_Info_Canal (2) (1).pdf`.
