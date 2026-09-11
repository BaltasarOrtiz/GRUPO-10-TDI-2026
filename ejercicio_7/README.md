# Ejercicio 7 — Detección de Errores: Checksum CUIT/CUIL (Módulo 11)

## Requisitos

- Python 3.9+
- Solo librería estándar (`argparse`, `sys`).

## Instalación

No requiere instalación de paquetes.

## Uso

```bash
python3 ejercicio_7.py --cuit 20-17254359-7
```

O sin `--cuit`, para que el programa pida el número por teclado:

```bash
python3 ejercicio_7.py
```

## Qué hace el programa (puntos a–d)

- **a) Lógica matemática del dígito verificador.** Ver respuesta teórica a).
- **b) Pedir por teclado un CUIT/CUIL de 11 dígitos.** `limpiar_cuit`.
- **c) Separar los primeros 10 dígitos, calcular con Módulo 11 y comparar.** `calcular_digito_verificador` y `validar_cuit`.
- **d) Informar Válida/Inválida.** `imprimir_calculo` y el resultado final en `main`.

## Respuestas teóricas (a–d)

**a) Lógica matemática del dígito verificador.** Los primeros 10 dígitos se multiplican por el peso fijo `[5,4,3,2,7,6,5,4,3,2]`, se suman los productos, se toma el resto módulo 11, y el verificador es `11 - resto`. Casos especiales: `11 → 0`, `10 → 9` (convención usada en este programa; AFIP en el caso `resto=1` cambia el prefijo del CUIT en vez de usar un dígito fijo, pero eso aplica a la generación de un CUIT nuevo, no a la validación).

**b) Entrada por teclado.** Acepta formato con o sin guiones; valida que, tras quitar guiones/espacios, queden exactamente 11 dígitos numéricos.

**c) Separación y cálculo del dígito esperado.** `calcular_digito_verificador` toma `cuit_11[:10]`, aplica Módulo 11 y devuelve el dígito esperado. `validar_cuit` lo compara contra `int(cuit_11[10])`.

**d) Resultado y por qué es un código de detección de errores.** El programa informa VÁLIDA/INVÁLIDA e imprime el cálculo paso a paso. Es un código de detección sistemático porque el dígito de control es redundancia calculada a partir de los otros 10 dígitos: detecta siempre un error de un solo dígito, y la mayoría de las transposiciones adyacentes (no todas, por la repetición de pesos a partir de la posición 5).

## Resultados medidos (casos de prueba)

Corridas reales (`python3 ejercicio_7.py --cuit <valor>`):

| CUIT/CUIL ingresado | Dígito ingresado | Dígito esperado | Resultado |
|---|---|---|---|
| `20-17254359-7` | 7 | 7 | VÁLIDA |
| `20-17254359-0` | 0 | 7 | INVÁLIDA |
| `20-17254357-0` (caso especial resto=0, 11→0) | 0 | 0 | VÁLIDA |
| `20-17254352-9` (caso especial resto=1, 10→9) | 9 | 9 | VÁLIDA |

Salida completa del caso válido principal:

```
$ python3 ejercicio_7.py --cuit 20-17254359-7
[1/3] Validando formato de entrada...
      CUIT/CUIL ingresado: 20-17254359-7  (11 dígitos)
[2/3] Aplicando el algoritmo de Módulo 11 sobre los primeros 10 dígitos...
      Dígito     2   0   1   7   2   5   4   3   5   9
      Peso       5   4   3   2   7   6   5   4   3   2
      Producto  10   0   3  14  14  30  20  12  15  18
      Suma de productos: 136
      136 mod 11 = 4
      Dígito verificador esperado: 11 - 4 = 7
[3/3] Comparando con el dígito ingresado...
      Dígito ingresado: 7
      Dígito esperado : 7
      Resultado: VÁLIDA
```

Salida completa del caso inválido (mismo número, último dígito alterado):

```
$ python3 ejercicio_7.py --cuit 20-17254359-0
[1/3] Validando formato de entrada...
      CUIT/CUIL ingresado: 20-17254359-0  (11 dígitos)
[2/3] Aplicando el algoritmo de Módulo 11 sobre los primeros 10 dígitos...
      Dígito     2   0   1   7   2   5   4   3   5   9
      Peso       5   4   3   2   7   6   5   4   3   2
      Producto  10   0   3  14  14  30  20  12  15  18
      Suma de productos: 136
      136 mod 11 = 4
      Dígito verificador esperado: 11 - 4 = 7
[3/3] Comparando con el dígito ingresado...
      Dígito ingresado: 0
      Dígito esperado : 7
      Resultado: INVÁLIDA
```

Errores de formato (`ErrorEntrada`, exit 1):

```
$ python3 ejercicio_7.py --cuit 2017254359
ERROR: El CUIT/CUIL debe tener 11 dígitos, se recibieron 10: '2017254359'

$ python3 ejercicio_7.py --cuit "20-1725435X-7"
ERROR: El CUIT/CUIL debe contener solo dígitos (y opcionalmente guiones): '20-1725435X-7'
```
