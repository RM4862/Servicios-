import argparse
import xmlrpc.client
 
def main():
    print("Cliente para interactuar con el servidor XML-RPC.")
    print("Comandos disponibles:")
    print("  - '..' para regresar a la carpeta anterior")
    print("  - '/' para regresar al inicio")
    print("  - 'cancel' para terminar la sesión")
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description="Cliente para interactuar con el servidor XML-RPC.")
    parser.add_argument("action", type=str, choices=["register", "list"], help="Acción a realizar: 'register' para registrar un nuevo usuario, 'list' para listar el contenido de una carpeta.")
    parser.add_argument("username", type=str, help="Nombre de usuario.")
    parser.add_argument("password", type=str, help="Contraseña.")
    parser.add_argument("path", type=str, nargs='?', default='/', help="Ruta de la carpeta remota que se desea listar (solo para 'list').")
    # Parsear los argumentos
    args = parser.parse_args()
    # Dirección IP del servidor (modificar según sea necesario)
    server_ip = ""  # Reemplaza con la IP del servidor obtenida del servidor_cr.py
    # Conectar al servidor
    server = xmlrpc.client.ServerProxy(f"http://{server_ip}:8000/")
    if args.action == "register":
        # Registrar el usuario
        response = server.register_user(args.username, args.password)
        print(response)
    elif args.action == "list":
        current_path = args.path
        while True:
            # Solicitar el contenido de la carpeta remota
            response = server.list_directory(args.username, args.password, current_path)
            if isinstance(response, dict):
                print(f"Ruta actual: {response['current_path']}")
                print("Contenido de la carpeta:")
                for item in response['contents']:
                    print(f"- {item}")
            else:
                print(response)
                break
            # Solicitar la siguiente ruta o comando al usuario
            next_path = input("Ingrese la siguiente ruta o 'cancel' para terminar: ")
            if next_path.lower() == "cancel":
                print("Sesión terminada.")
                break
            current_path = next_path
 
if __name__ == "__main__":
    main()