#!/bin/bash

target="127.0.0.1"

echo "Voy a revisar si $target está encendida..."

if ping -c 1 "$target" &> /dev/null; then
    echo "[+] $target está viva. Procedo a escanear puertos..."
    nmap "$target"
else
    echo "[-] $target no responde. No tiene sentido escanear, me detengo aquí."
fi
