#!/usr/bin/env python3
import socket

target = "127.0.0.1"
puerto = 631

print(f"Voy a revisar si el puerto {puerto} está abierto en {target}...")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(1)

resultado = sock.connect_ex((target, puerto))

if resultado == 0:
    print(f"[+] El puerto {puerto} está ABIERTO")
else:
    print(f"[-] El puerto {puerto} está CERRADO")

sock.close()
