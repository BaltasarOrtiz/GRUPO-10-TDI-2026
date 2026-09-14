# Ejercicio 9 — Canal Binario Simétrico (BSC) por Sockets TCP

## Requisitos

Python 3.9+ y únicamente la biblioteca estándar (`socket`, `struct`, `threading`, `random`, `argparse`, `math`).

## Instalación

No aplica: no hay paquetes de terceros.

## Uso (cómo levantar el servidor y correr el cliente)

**Hay que levantar el servidor primero.** `servidor_bsc.py` es el código provisto por la cátedra, sin modificaciones.

En una terminal:

```bash
python3 servidor_bsc.py
```

Queda escuchando en el puerto `5555` (`Ctrl+C` para detenerlo).

En otra terminal:

```bash
python3 cliente_bsc.py
```

Opciones:

- `--host` (default `127.0.0.1`).
- `--puerto` (default `5555`).
- `--semilla-cliente` (default: no determinista): fija la semilla de las tramas aleatorias del cliente, para reproducibilidad.

## Qué hace el programa (Fase 1 y Fase 2)

**Fase 1 — Transmisión y BER empírico** (`conectar`, `medir_ber`, `generar_trama_aleatoria`, `contar_errores`, `texto_a_binario`, `binario_a_texto`):

1. El cliente se conecta al servidor por sockets TCP.
2. Corre 3 pruebas con tramas de `100`, `10.000` y `1.000.000` de bits.
3. Cada trama se envía y se recibe la versión afectada por el ruido del canal.
4. Se comparan bit a bit, se cuentan errores y se calcula el BER empírico.
5. Se convierte una frase a binario, se pasa por el canal, y se reconvierte a texto.

**Fase 2 — Modelado matemático y Capacidad del Canal** (`matriz_bsc`, `probabilidades_entrada`, `informacion_mutua`, `capacidad_bsc`, `entropia`):

1. Matriz del canal `P(Y|X)`, usando como `p` el BER empírico de la prueba de `1.000.000` de bits.
2. `P(X=0)`/`P(X=1)` de esa trama.
3. Información Mutua `I(X;Y)`.
4. Capacidad `C = 1 - H(p)`.
5. Compara `I(X;Y)` contra `C` (margen 5-10 %).

## Respuestas teóricas

**Convergencia del BER (Ley de los Grandes Números).** El BER empírico de `N` bits es el promedio de `N` Bernoulli(p), así que converge a `p` cuando `N → ∞`; la varianza del estimador decrece como `p(1-p)/N`. Por eso se usa la corrida de `N=1.000.000` como mejor estimación de `p`.

**Por qué el mensaje de texto se ve "roto".** Cada carácter son 8 bits; la probabilidad de que al menos uno se invierta es `1-(1-p)^8`, mayor que `p`, y un solo bit invertido ya cambia el carácter completo.

**Comparación `I(X;Y)` vs. `C`.** En un BSC, `H(Y|X) = H(p)` sin importar `P(X)`, así que `I(X;Y)` se maximiza cuando `P(X)` es uniforme (`0.5/0.5`). Una trama aleatoria equiprobable tiene `P(X=0)` cercano a `0.5` para `N` grande, así que `I(X;Y)` se acerca a `C`. En la corrida registrada, con `p = 0.060868` y `P(X=0) = 0.500236`, `I(X;Y) = C = 0.669119` bits/símbolo (diferencia relativa `0.00 %`, dentro del margen). Sí se maximizó la capacidad del canal.

## Resultados medidos (corrida real, servidor + cliente)

Ejecución real: servidor levantado con `python3 servidor_bsc.py`, cliente ejecutado con `python3 cliente_bsc.py --semilla-cliente 2026` contra `127.0.0.1:5555`. Salida completa, tal cual la imprime el programa:

```
=== Fase 1: Transmisión y BER empírico ===

Prueba 1/3: trama de 100 bits
   Errores: 6/100   BER empírico: 0.060000
Prueba 2/3: trama de 10.000 bits
   Errores: 604/10000   BER empírico: 0.060400
Prueba 3/3: trama de 1.000.000 bits
   Errores: 60868/1000000   BER empírico: 0.060868

Convergencia (Ley de los Grandes Números): a medida que crece N, el BER empírico se estabiliza cada vez más cerca de la probabilidad de error real del canal (la varianza del estimador decrece como 1/N); compárense los tres valores de arriba: deberían acercarse entre sí a medida que N crece.

Mensaje de texto a través del canal (frase: 'Teoria de la Informacion')...
   Original : 'Teoria de la Informacion'
   Recibido : 'teOrka de\x00lk Infosmacío.'
   Caracteres distintos: 8/24

=== Fase 2: Modelado matemático y Capacidad del Canal ===

Usando p = 0.060868 (BER empírico de la prueba de 1,000,000 bits, la mejor estimación disponible por Ley de los Grandes Números) como probabilidad de error teórica del BSC.

1. Matriz del canal P(Y|X):
      Fila X=0: [0.939132, 0.060868]
      Fila X=1: [0.060868, 0.939132]

2. Probabilidades de entrada (trama de 1,000,000 bits enviada):
      P(X=0) = 0.500236
      P(X=1) = 0.499764

3. Información mutua de esta transmisión: I(X;Y) = 0.669119 bits/símbolo
      (H(Y) = 1.000000, H(Y|X) = 0.330881)

4. Capacidad del canal: C = 1 - H(p) = 0.669119 bits/símbolo

5. Comparación: I(X;Y) = 0.669119, C = 0.669119, diferencia relativa = 0.00 %
      Dentro del margen de 5-10 % del enunciado.
```

El BER converge de forma estable alrededor de `0.06` a medida que crece `N` (`0.060000` → `0.060400` → `0.060868`). El mensaje de texto salió alterado en 8 de 24 caracteres, incluyendo un byte de control no imprimible (`\x00`). `I(X;Y)` y `C` coincidieron prácticamente de forma exacta.

## Archivos

- `ejercicio_9/servidor_bsc.py` — código provisto por la cátedra, transcripción literal, sin cambios de lógica.
- `ejercicio_9/cliente_bsc.py` — el entregable real. Protocolo de red (`recibir_exactamente`, `recibir_mensaje`, `enviar_mensaje`, `conectar`), Fase 1 (`generar_trama_aleatoria`, `contar_errores`, `medir_ber`, `texto_a_binario`, `binario_a_texto`), Fase 2 (`entropia`, `matriz_bsc`, `probabilidad_salida`, `entropia_condicional`, `informacion_mutua`, `capacidad_bsc`, `probabilidades_entrada`), orquestación en `main`, argumentos en `parsear_argumentos`.
