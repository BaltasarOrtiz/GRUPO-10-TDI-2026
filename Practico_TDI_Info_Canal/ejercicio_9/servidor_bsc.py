#!/usr/bin/env python3
# Código provisto por la cátedra, transcripción literal (sin modificaciones).
#
# servidor_bsc.py
#
# Servidor que simula un Canal Binario Simétrico (BSC) sin memoria.
# Utiliza Sockets TCP y un protocolo de enmarcado de longitud (4 bytes).
#
# Python 3.x

import socket
import random
import struct
import threading

# ============================================================
# CONFIGURACION GENERAL
# ============================================================
HOST = "0.0.0.0"
PUERTO = 5555

# Semilla maestra para generar la matriz del canal (fija la probabilidad)
SEMILLA_CANAL = 2026

# ============================================================
# GENERACION DEL CANAL (CAJA NEGRA)
# ============================================================
rng_canal = random.Random(SEMILLA_CANAL)
limite_a = rng_canal.random()
limite_b = rng_canal.random()
P_ERROR = min(limite_a, limite_b) * rng_canal.random()

# ============================================================
# PROTOCOLO DE COMUNICACION Y RED
# ============================================================
def recibir_exactamente(sock, cantidad):
    datos = bytearray()
    while len(datos) < cantidad:
        bloque = sock.recv(cantidad - len(datos))
        if not bloque:
            raise ConnectionError("Conexión cerrada por el cliente.")
        datos.extend(bloque)
    return bytes(datos)

def recibir_mensaje(sock):
    encabezado = recibir_exactamente(sock, 4)
    longitud = struct.unpack("!I", encabezado)[0]
    datos = recibir_exactamente(sock, longitud)
    return datos.decode("ascii")

def enviar_mensaje(sock, mensaje):
    datos = mensaje.encode("ascii")
    encabezado = struct.pack("!I", len(datos))
    sock.sendall(encabezado + datos)

# ============================================================
# ATENCION DEL CLIENTE Y RUIDO
# ============================================================
def atender_cliente(cliente, direccion):
    print(f"[+] Cliente conectado: {direccion[0]}:{direccion[1]}")

    # Instanciamos el generador de ruido POR CLIENTE.
    # Esto asegura que cada sesión nueva sea 100% determinista.
    rng_ruido = random.Random(SEMILLA_CANAL + 1)

    try:
        while True:
            mensaje = recibir_mensaje(cliente)

            if mensaje == "SALIR":
                break

            if not mensaje:
                enviar_mensaje(cliente, "ERROR: mensaje vacío")
                continue

            if any(bit not in "01" for bit in mensaje):
                enviar_mensaje(cliente, "ERROR: solo se permiten símbolos 0 y 1")
                continue

            # TRANSMISION A TRAVES DEL CANAL SIMETRICO
            salida = []
            for bit in mensaje:
                # Si el número aleatorio cae dentro de la probabilidad de error, invertimos el bit
                if rng_ruido.random() < P_ERROR:
                    salida.append("1" if bit == "0" else "0")
                else:
                    salida.append(bit)

            # Devolvemos la salida alterada
            enviar_mensaje(cliente, "".join(salida))

    except (ConnectionError, OSError):
        pass
    finally:
        cliente.close()
        print(f"[-] Cliente desconectado: {direccion[0]}:{direccion[1]}")

# ============================================================
# INICIO DEL SERVIDOR
# ============================================================
def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PUERTO))
    servidor.listen()

    print("=" * 55)
    print(" SERVIDOR - CANAL BINARIO SIMETRICO (BSC)")
    print("=" * 55)
    print(f"Escuchando en puerto {PUERTO}")
    print("La probabilidad de error (p) permanece oculta.")

    print("=" * 55)

    try:
        while True:
            cliente, direccion = servidor.accept()
            hilo = threading.Thread(
                target=atender_cliente,
                args=(cliente, direccion),
                daemon=True
            )
            hilo.start()
    except KeyboardInterrupt:
        print("\nServidor finalizado.")
    finally:
        servidor.close()

if __name__ == "__main__":
    iniciar_servidor()
