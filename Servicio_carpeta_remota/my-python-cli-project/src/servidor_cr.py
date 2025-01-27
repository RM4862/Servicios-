from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from socketserver import ThreadingMixIn
import socket
import os
import logging

# Configurar el registro
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

# Carpeta base permitida
BASE_DIR =  # Reemplaza con la ruta de la carpeta permitida

# Historial de rutas
path_history = [BASE_DIR]

# Usuarios registrados
users = {}

def register_user(username, password):
    """Registra un nuevo usuario."""
    if username in users:
        return f"Error: El usuario '{username}' ya existe."
    users[username] = password
    return f"Usuario '{username}' registrado exitosamente."

def authenticate_user(username, password):
    """Autentica un usuario."""
    if username not in users or users[username] != password:
        return False
    return True

def list_directory(username, password, path):
    """Lista el contenido de una carpeta."""
    if not authenticate_user(username, password):
        return "Error: Autenticación fallida."

    global path_history

    # Comandos especiales
    if path == "..":
        if len(path_history) > 1:
            path_history.pop()
        abs_path = path_history[-1]
    elif path == "/":
        path_history = [BASE_DIR]
        abs_path = BASE_DIR
    else:
        abs_path = os.path.abspath(os.path.join(path_history[-1], path))
        if not abs_path.startswith(os.path.abspath(BASE_DIR)):
            return f"Error: Acceso denegado a la ruta '{path}'."

        # Verificar si la carpeta existe antes de actualizar el historial de rutas
        if not os.path.exists(abs_path):
            return f"Error: La carpeta '{abs_path}' no existe. Ruta actual: {path_history[-1]}"

        path_history.append(abs_path)

    try:
        contents = os.listdir(abs_path)
        if not contents:
            return f"La carpeta '{abs_path}' está vacía. Ruta actual: {abs_path}"
        return {"current_path": abs_path, "contents": contents}
    except FileNotFoundError:
        return f"Error: La carpeta '{abs_path}' no existe. Ruta actual: {path_history[-1]}"
    except PermissionError:
        return f"Error: Sin permisos para acceder a '{abs_path}'. Ruta actual: {path_history[-1]}"

def list_base_directory():
    """Lista el contenido de la carpeta base."""
    try:
        contents = os.listdir(BASE_DIR)
        if not contents:
            print(f"La carpeta base '{BASE_DIR}' está vacía.")
        else:
            print(f"Contenido de la carpeta base '{BASE_DIR}':")
            for item in contents:
                print(f"- {item}")
    except FileNotFoundError:
        print(f"Error: La carpeta base '{BASE_DIR}' no existe.")
    except PermissionError:
        print(f"Error: Sin permisos para acceder a la carpeta base '{BASE_DIR}'.")

def get_local_ip():
    """Obtiene la dirección IP local de la máquina."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No se envía ningún dato, solo se conecta a una dirección remota para obtener la IP local
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

class MiddlewareXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    def do_POST(self):
        logging.info(f"Request from {self.client_address}")
        super().do_POST()

# Crear el servidor RPC multihilo
server = ThreadedXMLRPCServer(("0.0.0.0", 8000), requestHandler=MiddlewareXMLRPCRequestHandler)  # Escuchar en todas las interfaces de red
local_ip = get_local_ip()
print(f"Servidor escuchando en el puerto 8000 en la IP {local_ip}...")

# Listar el contenido de la carpeta base al iniciar el servidor
list_base_directory()

# Registrar las funciones
server.register_function(register_user, "register_user")
server.register_function(list_directory, "list_directory")

# Mantener el servidor corriendo
server.serve_forever()