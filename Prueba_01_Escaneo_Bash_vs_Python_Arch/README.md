# Prueba 01 — Escaneo Bash vs Python en Arch

_Fecha: 2026-09-28 · Equipo: BlackArch (host `blackarch`), usuario normal `ecorp`_
_Origen: repetición en Arch del Tema 6 (Bash Scripting) del repo `estudio_Kali_linux`, hecho antes en Kali._

**Objetivo:** crear paso a paso dos scripts que revisan `127.0.0.1` (mi propio equipo), uno en **Bash**
(`ping` + `nmap`) y otro en **Python** (librería `socket`), y comparar los resultados con los de Kali.

| Archivo | Qué hace |
|---------|----------|
| [`escaneo.sh`](escaneo.sh) | Hace ping al objetivo; si responde, lo escanea con Nmap |
| [`escaneo.py`](escaneo.py) | Intenta una conexión TCP al puerto 631 y dice si está ABIERTO o CERRADO |

---

## Paso 0 — Arreglar la carpeta de trabajo (problema de permisos)

La carpeta `~/Desktop/scripts` se había creado **como root**, y `~/Desktop` también era de root:

```
drwxr-xr-x  root root  Desktop
drwxr-xr-x  root root  scripts
```

En una carpeta, `w` = crear/borrar archivos dentro. Para `ecorp` (otros) solo había `r-x`:
podía entrar y leer, pero **no crear** el script (`Permission denied`).

```bash
ls -ld ~/Desktop ~/Desktop/scripts                    # ver dueño y permisos de las carpetas
sudo chown ecorp:ecorp ~/Desktop ~/Desktop/scripts    # devolverme la propiedad
ls -ld ~/Desktop ~/Desktop/scripts                    # ahora: ecorp ecorp
```

- `chown` = *change owner*; `ecorp:ecorp` = usuario:grupo; `sudo` porque solo root puede quitarle archivos a root.
- `ls -l` = formato largo; `-d` = mostrar la carpeta misma, no su contenido.
- Se buscó con `find /home/ecorp -xdev ! -user ecorp` y solo esas 2 carpetas eran de root.

**Por qué no trabajar como root:** un error en un script como root puede dañar todo el sistema
(ej. `rm -rf "$carpeta"/*` con la variable vacía = `rm -rf /*`), todo lo creado queda a nombre de root,
y un script descargado malicioso tendría control total. → **Principio de mínimo privilegio:** trabajar
como usuario normal y usar `sudo` solo para el comando que lo necesite.

---

## Parte 1 — Script en Bash (`escaneo.sh`)

### Paso 1 — Crear el archivo con el shebang

```bash
cd ~/Desktop/scripts
nano escaneo.sh          # escribir: #!/bin/bash   → Ctrl+O, Enter, Ctrl+X
```

- **Shebang** `#!/bin/bash`: le dice al sistema con qué programa leer el archivo al ejecutarlo con `./`.
- En Arch `/bin` es un enlace a `/usr/bin`, igual que en Kali: funciona igual.

### Paso 2 — Escribir el script

```bash
#!/bin/bash

target="127.0.0.1"

echo "Voy a revisar si $target está encendida..."

if ping -c 1 "$target" &> /dev/null; then
    echo "[+] $target está viva. Procedo a escanear puertos..."
    nmap "$target"
else
    echo "[-] $target no responde. No tiene sentido escanear, me detengo aquí."
fi
```

| Línea | Qué hace |
|-------|----------|
| `target="127.0.0.1"` | Variable. Sin espacios alrededor del `=` (si no, bash cree que `target` es un comando) |
| `echo "... $target ..."` | Imprime texto; `$target` se reemplaza por su valor |
| `ping -c 1 "$target"` | Manda **1** ping ICMP (Echo Request, tipo 8) |
| `&> /dev/null` | Tira la salida del ping: solo interesa si funcionó o no |
| `if ...; then` / `else` / `fi` | Si el ping respondió → escanea con `nmap`; si no → se detiene. `fi` cierra el `if` |
| `[+]` / `[-]` | Convención de éxito / fallo en herramientas de hacking |

Corrección respecto a la versión del repo `estudio_Kali_linux`: allí el mensaje `"...me detengo aquí."`
quedó partido en dos líneas; aquí va en una sola.

Comprobación (error cometido y aprendido: `%%` no existe; el correcto es `&&` = "ejecuta el segundo
solo si el primero funcionó"):

```bash
cat escaneo.sh && ls -l escaneo.sh
# -rw-r--r-- 1 ecorp ecorp 300 ... escaneo.sh     ← sin x: no se puede ejecutar con ./
```

### Paso 3 — Dar permiso de ejecución

```bash
chmod +x escaneo.sh
ls -l escaneo.sh
# -rwxr-xr-x 1 ecorp ecorp 300 ... escaneo.sh     ← ahora con x
```

- `chmod` = *change mode*; `+x` = añadir permiso de ejecución. Los archivos nuevos nacen sin `x` por seguridad.
- Si no muestra nada → funcionó.

### Paso 4 — Ejecutar

```bash
./escaneo.sh
```

`./` = "el archivo de ESTA carpeta". Sin él, bash lo busca solo en las carpetas de programas
(`/usr/bin`...) → `command not found`. Es por seguridad (evita ejecutar un programa falso de la carpeta actual).

**Resultado:**

```
Voy a revisar si 127.0.0.1 está encendida...
[+] 127.0.0.1 está viva. Procedo a escanear puertos...
Starting Nmap 7.991 ( https://nmap.org ) at 2026-09-28 16:45 -0500
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000029s latency).
All 1000 scanned ports on localhost (127.0.0.1) are in ignored states.
Not shown: 1000 closed tcp ports (conn-refused)
```

- El ping respondió → entró en el `if` → lanzó Nmap.
- Sin `-p`, Nmap escanea los **1000 puertos más comunes**. `ignored states` = no los lista porque todos están closed.
- **`conn-refused`**: como se ejecutó como usuario normal, Nmap usó **TCP Connect (`-sT`)** (handshake completo,
  el sistema responde RST). Como root usaría **SYN scan (`-sS`)** y la razón sería `reset`.

---

## Parte 2 — Script en Python (`escaneo.py`)

### Paso 5 — Crear el archivo

```python
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
```

| Línea | Qué hace |
|-------|----------|
| `#!/usr/bin/env python3` | Shebang: `env` busca dónde está `python3` (en Arch `/usr/bin/python3`) |
| `import socket` | Librería estándar de Python (viene incluida, no requiere `pip`) |
| `print(f"...{puerto}...")` | La `f` permite meter variables entre `{}` |
| `socket.socket(AF_INET, SOCK_STREAM)` | Crea un socket: `AF_INET` = IPv4, `SOCK_STREAM` = **TCP** |
| `settimeout(1)` | Si nadie responde en 1 s, se rinde |
| `connect_ex((target, puerto))` | Intenta la conexión TCP (SYN → SYN-ACK → ACK). Devuelve **0 si conectó**, otro número si no |
| `if resultado == 0` | 0 → ABIERTO, otro → CERRADO |
| `sock.close()` | Cierra el socket |

¿Por qué el puerto 631? Porque en Kali el `escaneo.sh` encontró `631/tcp open ipp` (CUPS, servicio de
impresión), y la versión Python se hizo para comprobar ese mismo puerto.

### Paso 6 — Errores con el shebang (y cómo se resolvieron)

**Error 1 — el shebang no se copió al pegar.** El archivo empezaba en `import socket`.

**Error 2 — un espacio antes del `#!`:**

```
 #!/usr/bin/env python3        ← espacio al principio
```

```
./escaneo.py: line 2: import: command not found
./escaneo.py: line 4: target: command not found
./escaneo.py: line 7: syntax error near unexpected token `f"Voy a revisar si el puerto ..."'
```

- El shebang solo funciona si `#!` son **exactamente los 2 primeros caracteres** del archivo.
  Con cualquier cosa antes (incluso un espacio), Linux lo lee con **bash** → bash intenta ejecutar
  `import` como comando. Los errores son de bash, no de Python.
- `sudo pacman -S python3` no hacía falta: Python ya estaba instalado (pacman solo lo reinstaló).
  `command not found` dentro de un script casi siempre es un error **del script**, no un programa faltante.
- Cómo ver caracteres invisibles:

```bash
head -1 escaneo.py | cat -A
# #!/usr/bin/env python3$      ← correcto ($ = fin de línea, sin espacio delante)
```

### Paso 7 — Ejecutar

```bash
chmod +x escaneo.py
./escaneo.py
```

**Resultado:**

```
Voy a revisar si el puerto 631 está abierto en 127.0.0.1...
[-] El puerto 631 está CERRADO
```

`connect_ex` recibió un RST (conexión rechazada) → devolvió error ≠ 0 → CERRADO.
Coincide con Nmap (1000 puertos closed).

---

## Comparación de resultados

| | Kali (Tema 6 original) | Arch (esta prueba) |
|---|---|---|
| `escaneo.sh` | `631/tcp open ipp` | 1000 puertos closed (`conn-refused`) |
| `escaneo.py` (631) | ABIERTO | CERRADO |
| Motivo | Kali tenía CUPS encendido | Arch no enciende servicios por defecto (`ss -tulnp` vacío) |

| | Bash (`escaneo.sh`) | Python (`escaneo.py`) |
|---|---|---|
| Pregunta | ¿El host está vivo? → escanea | ¿El puerto 631 está abierto? |
| Quién hace el trabajo | Programas externos (`ping`, `nmap`) | Python mismo (`socket`) |
| Cierre de bloques | `fi` | Indentación |
| Variables | `$target` | `target` / `{target}` en f-strings |

## Diferencias Kali ↔ Arch relevantes para scripts

- El lenguaje es el mismo (GNU Bash; en Arch 5.3).
- Shell de la terminal: Kali usa **zsh**, Arch **bash** (config en `.zshrc` vs `.bashrc`).
- `/bin/sh`: en Kali es **dash**, en Arch es **bash**. Con `sh escaneo.sh` en Kali, `&>` no funciona
  (dash lo lee como `&` + `>`) y el `if` saldría siempre verdadero. → Ejecutar con `./script.sh` o `bash script.sh`, nunca `sh`.
- Instalar: `apt` en Kali, `pacman` en Arch. Librerías Python: `pacman -S python-<nombre>` o un entorno virtual.

## Conclusiones

1. Crear, dar `chmod +x` y ejecutar con `./` es igual en Kali y en Arch.
2. El mismo script da resultados distintos porque **el equipo es distinto**, no porque el script esté mal.
3. El shebang debe ser literalmente lo primero del archivo; si no, se ejecuta con bash.
4. Trabajar como usuario normal; si una carpeta se crea como root, se arregla con `chown`.
5. Python con `socket` hace lo mismo que `nmap -sT` para un puerto, sin depender de Nmap.

## Pendiente (siguiente paso)

Ver un **ABIERTO** en Arch: cambiar `puerto = 631` por `puerto = 4444`, abrir el puerto en otra
terminal con `nc -lvnp 4444` y ejecutar `./escaneo.py`.
