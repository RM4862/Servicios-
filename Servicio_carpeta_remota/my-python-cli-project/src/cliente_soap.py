import requests
import xml.etree.ElementTree as ET
import sys

# Configuración del cliente
SOAP_URL = "http://192.168.1.70:8080/soap"
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
WSDL_NS = "http://carpetaremota.example.com/wsdl"

# Configuración de namespaces para análisis XML
namespaces = {
    'soap': SOAP_NS,
    'wsdl': WSDL_NS
}

class SOAPClient:
    def __init__(self, url=SOAP_URL):
        self.url = url
        self.username = None
        self.password = None
    
    def login(self, username, password):
        """Guarda las credenciales para futuras operaciones"""
        self.username = username
        self.password = password
    
    def register_user(self, username, password):
        """Registra un nuevo usuario en el sistema"""
        # Construir solicitud SOAP
        soap_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:wsdl="{WSDL_NS}">
  <soap:Body>
    <wsdl:RegisterUserRequest>
      <wsdl:username>{username}</wsdl:username>
      <wsdl:password>{password}</wsdl:password>
    </wsdl:RegisterUserRequest>
  </soap:Body>
</soap:Envelope>"""
        
        # Enviar solicitud
        headers = {'Content-Type': 'text/xml; charset=utf-8'}
        response = requests.post(self.url, data=soap_request, headers=headers)
        
        # Procesar respuesta
        if response.status_code == 200:
            return self._parse_register_response(response.text)
        else:
            return self._parse_fault(response.text)
    
    def list_directory(self, path):
        """Lista el contenido de un directorio"""
        if not self.username or not self.password:
            return "Error: Debe iniciar sesión primero"
        
        # Construir solicitud SOAP
        soap_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:wsdl="{WSDL_NS}">
  <soap:Body>
    <wsdl:ListDirectoryRequest>
      <wsdl:username>{self.username}</wsdl:username>
      <wsdl:password>{self.password}</wsdl:password>
      <wsdl:path>{path}</wsdl:path>
    </wsdl:ListDirectoryRequest>
  </soap:Body>
</soap:Envelope>"""
        
        # Enviar solicitud
        headers = {'Content-Type': 'text/xml; charset=utf-8'}
        response = requests.post(self.url, data=soap_request, headers=headers)
        
        # Procesar respuesta
        if response.status_code == 200:
            return self._parse_list_response(response.text)
        else:
            return self._parse_fault(response.text)
    
    def _parse_register_response(self, xml_response):
        """Analiza la respuesta XML de register_user"""
        try:
            root = ET.fromstring(xml_response)
            result_elem = root.find('.//wsdl:result', namespaces)
            if result_elem is not None:
                return result_elem.text
            return "Error: Respuesta inválida del servidor"
        except Exception as e:
            return f"Error al analizar la respuesta: {e}"
    
    def _parse_list_response(self, xml_response):
        """Analiza la respuesta XML de list_directory"""
        try:
            root = ET.fromstring(xml_response)
            
            # Buscar el elemento principal de resultado
            result_elem = root.find('.//wsdl:result', namespaces)
            
            # Si el resultado es un string simple (error o mensaje)
            if result_elem is not None and len(result_elem) == 0:
                return result_elem.text
            
            # Si es un objeto de directorio
            current_path_elem = root.find('.//wsdl:current_path', namespaces)
            contents_elem = root.find('.//wsdl:contents', namespaces)
            
            if current_path_elem is not None and contents_elem is not None:
                current_path = current_path_elem.text
                contents = [item.text for item in contents_elem.findall('.//wsdl:item', namespaces)]
                
                # Formatear la salida
                result = f"Ubicación actual: {current_path}\n"
                result += "Contenido:\n"
                for item in contents:
                    result += f"- {item}\n"
                return result
            
            return "Error: Respuesta inválida del servidor"
        except Exception as e:
            return f"Error al analizar la respuesta: {e}"
    
    def _parse_fault(self, xml_response):
        """Analiza un mensaje de error SOAP (Fault)"""
        try:
            root = ET.fromstring(xml_response)
            fault_string = root.find('.//faultstring')
            if fault_string is not None:
                return f"Error SOAP: {fault_string.text}"
            return "Error desconocido en la respuesta SOAP"
        except Exception as e:
            return f"Error al analizar el mensaje de error: {e}"

def print_help():
    """Muestra la ayuda del cliente"""
    print("\nComandos disponibles:")
    print("  register <usuario> <contraseña> - Registrar un nuevo usuario")
    print("  login <usuario> <contraseña> - Iniciar sesión")
    print("  ls [ruta] - Listar contenido (por defecto usa la ruta actual)")
    print("  cd <ruta> - Cambiar de directorio")
    print("  up - Subir un nivel (..)") 
    print("  root - Ir a la carpeta raíz (/)")
    print("  exit - Salir del programa")
    print("  help - Mostrar esta ayuda")

def main():
    client = SOAPClient()
    print("Cliente SOAP para Carpeta Remota")
    print("Escriba 'help' para ver los comandos disponibles.")
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command == "exit":
                break
                
            elif command == "help":
                print_help()
                
            elif command.startswith("register "):
                parts = command.split(" ", 2)
                if len(parts) != 3:
                    print("Uso: register <usuario> <contraseña>")
                else:
                    result = client.register_user(parts[1], parts[2])
                    print(result)
                    
            elif command.startswith("login "):
                parts = command.split(" ", 2)
                if len(parts) != 3:
                    print("Uso: login <usuario> <contraseña>")
                else:
                    client.login(parts[1], parts[2])
                    print(f"Sesión iniciada como {parts[1]}")
                    
            elif command.startswith("ls"):
                parts = command.split(" ", 1)
                path = parts[1] if len(parts) > 1 else "."
                result = client.list_directory(path)
                print(result)
                
            elif command.startswith("cd "):
                path = command.split(" ", 1)[1]
                result = client.list_directory(path)
                print(result)
                
            elif command == "up":
                result = client.list_directory("..")
                print(result)
                
            elif command == "root":
                result = client.list_directory("/")
                print(result)
                
            else:
                print("Comando no reconocido. Escriba 'help' para ver los comandos disponibles.")
                
        except KeyboardInterrupt:
            print("\nSaliendo del programa...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()