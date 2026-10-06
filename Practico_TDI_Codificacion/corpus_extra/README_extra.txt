CORPUS EXTRA - TEORIA DE LA INFORMACION (Grupo 10)
==================================================

Objetivo
--------
Corpus adicional del grupo, NO oficial. Sirve para explorar en que tipo de
datos se destaca el algoritmo propio (RLE + Shannon) frente a xz -6 y
gzip -n -6. No forma parte del ranking ni de la planilla de la catedra.

Todos los archivos se generan de forma deterministica (semillas fijas) con:

    python3 Practico_TDI_Codificacion/benchmark_extra.py

que ademas corre las tres soluciones y escribe los resultados en
results/benchmark_extra_resultados.csv y results/benchmark_extra_resumen.md.

Archivos
--------
1) extra_1_senal_digital.bin
   Rachas de 0x00 / 0xFF con largo aleatorio (1-200). Semilla 7.
   Ejemplo real: bits de un canal digital, linea blanco/negro de un fax.

2) extra_2_disperso.bin
   99,5 % de bytes en cero y bytes al azar en posiciones al azar. Semilla 4.
   Ejemplo real: matriz dispersa, imagen de disco casi vacia.

3) extra_3_estados.txt
   Rachas de los caracteres A/B/C/D con largo aleatorio (1-40). Semilla 6.
   Ejemplo real: estado de una maquina muestreado periodicamente.

4) extra_4_mascara_bn.bmp
   Imagen BMP 1024x1024, 8 bits, fondo negro con 60 elipses blancas al azar. Semilla 8.
   Ejemplo real: mascara de segmentacion, plano escaneado.

5) extra_5_logo_bn.bmp
   Imagen BMP 1024x1024, 8 bits, logo simple en blanco y negro (circulo, cuadrado, barra).
   Ejemplo real: logo, icono, dibujo simple.

6) extra_6_sensor.bin
   Valor de 1 byte que se mantiene 5-60 muestras y cambia de a +-3. Semilla 3.
   Ejemplo real: temperatura, nivel de un tanque.

7) extra_7_audio_silencios.raw
   PCM 8 bits sin signo: silencios (128) alternados con una senoidal con ruido. Semilla 5.
   Ejemplo real: grabacion de voz con pausas.

8) extra_8_texto_relleno.txt
   Lineas de ancho fijo (80) con numero, espacios de relleno y OK/ERROR/WARN. Semilla 9.
   Ejemplo real: log o reporte tabulado.

Tamanos y SHA-256
-----------------
extra_1_senal_digital.bin     1048576  9a7a5cc5ce55a192785a02f637b74ebc2daa24b7c0caef07f5f1f99ea29285d5
extra_2_disperso.bin          1048576  8c0dd3b6e7f636a79ad2854230edadc6d0c915dbd36a7f5bf8c875d7b90cd999
extra_3_estados.txt           1048576  9396d3b13bf4436a7abde1865c3b08a9ae3ab0af54ff9a701b8e81f4349af387
extra_4_mascara_bn.bmp        1049654  6e2abad9822ed53c34d1d7b61950c00801b87bc357ca139e7029740401aa7787
extra_5_logo_bn.bmp           1049654  a9609bc467366dba743d832f488a06dac585ee45d6869a387d980e46457a0dc6
extra_6_sensor.bin            1048576  675aba50802caf248cb59d2df4aacaf329c651073a7d485005df06bc58c62584
extra_7_audio_silencios.raw   1048576  9c0ee8a694be96f1f5a3a65efa3a945102cb2b5c412faddd9b903771a8bcc685
extra_8_texto_relleno.txt     1048576  b604eacc0d89e12150288bd86c08ae76bd388e686e735cda918d68a060c6c1a2
