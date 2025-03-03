import http.server
import socketserver
import xml.etree.ElementTree as ET
import xmlrpc.client
import re
import json

# Configuración del servidor SOAP
PORT = 8080
# Modifica la línea
RPC_SERVER = f"http://192.168.1.70:8000"

# Namespaces para SOAP y WSDL
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
WSDL_NS = "http://carpetaremota.example.com/wsdl"

# Cliente XML-RPC para comunicarse con el servidor RPC
rpc_client = xmlrpc.client.ServerProxy(RPC_SERVER)

class SOAPRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Maneja solicitudes GET para servir el WSDL"""
        if self.path == "/wsdl" or self.path == "/soap?wsdl":
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.end_headers()
            
            with open("carpeta_remota.wsdl", "r") as f:
                wsdl_content = f.read()
            
            self.wfile.write(wsdl_content.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def do_POST(self):
        """Maneja solicitudes POST para operaciones SOAP"""
        if self.path == "/soap":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Procesar la solicitud SOAP
                soap_response = self.process_soap_request(post_data)
                
                self.send_response(200)
                self.send_header("Content-type", "text/xml; charset=utf-8")
                self.end_headers()
                self.wfile.write(soap_response.encode())
            except Exception as e:
                # Enviar respuesta de error SOAP
                fault_response = self.create_soap_fault("Server", str(e))
                self.send_response(500)
                self.send_header("Content-type", "text/xml; charset=utf-8")
                self.end_headers()
                self.wfile.write(fault_response.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def process_soap_request(self, soap_data):
        """Procesa las solicitudes SOAP y las traduce a llamadas RPC"""
        
        # Analizar la solicitud SOAP
        root = ET.fromstring(soap_data)
        
        # Crear el namespace map para búsquedas XPath
        ns_map = {
            'soap': SOAP_NS,
            'wsdl': WSDL_NS
        }
        
        # Buscar el cuerpo SOAP
        body = root.find('.//soap:Body', ns_map)
        if body is None:
            return self.create_soap_fault("Client", "No se encontró el cuerpo SOAP")
        
        # Encontrar la operación solicitada
        operation = None
        params = {}
        
        # Buscar operación RegisterUser
        register_request = body.find('.//wsdl:RegisterUserRequest', ns_map)
        if register_request is not None:
            operation = "RegisterUser"
            username = register_request.find('.//wsdl:username', ns_map).text
            password = register_request.find('.//wsdl:password', ns_map).text
            params = {"username": username, "password": password}
        
        # Buscar operación ListDirectory
        list_request = body.find('.//wsdl:ListDirectoryRequest', ns_map)
        if list_request is not None:
            operation = "ListDirectory"
            username = list_request.find('.//wsdl:username', ns_map).text
            password = list_request.find('.//wsdl:password', ns_map).text
            path = list_request.find('.//wsdl:path', ns_map).text
            params = {"username": username, "password": password, "path": path}
        
        if operation is None:
            return self.create_soap_fault("Client", "Operación no soportada")
        
        # Ejecutar la operación RPC correspondiente
        result = None
        if operation == "RegisterUser":
            result = rpc_client.register_user(params["username"], params["password"])
        elif operation == "ListDirectory":
            result = rpc_client.list_directory(
                params["username"], 
                params["password"], 
                params["path"]
            )
        
        # Crear respuesta SOAP
        if operation == "RegisterUser":
            return self.create_register_response(result)
        else:  # ListDirectory
            return self.create_list_directory_response(result)
    
    def create_register_response(self, result):
        """Crea una respuesta SOAP para la operación RegisterUser"""
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:wsdl="{WSDL_NS}">
  <soap:Body>
    <wsdl:RegisterUserResponse>
      <wsdl:result>{result}</wsdl:result>
    </wsdl:RegisterUserResponse>
  </soap:Body>
</soap:Envelope>"""
        return soap_response
    
    def create_list_directory_response(self, result):
        """Crea una respuesta SOAP para la operación ListDirectory"""
        # Si el resultado es un diccionario, formatear correctamente
        if isinstance(result, dict):
            current_path = result.get("current_path", "")
            contents = result.get("contents", [])
            
            # Crear elementos para la lista de contenidos
            contents_xml = ""
            for item in contents:
                contents_xml += f"<wsdl:item>{item}</wsdl:item>"
            
            soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:wsdl="{WSDL_NS}">
  <soap:Body>
    <wsdl:ListDirectoryResponse>
      <wsdl:result>
        <wsdl:current_path>{current_path}</wsdl:current_path>
        <wsdl:contents>
          {contents_xml}
        </wsdl:contents>
      </wsdl:result>
    </wsdl:ListDirectoryResponse>
  </soap:Body>
</soap:Envelope>"""
        else:
            # Para mensajes de error o texto simple
            soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:wsdl="{WSDL_NS}">
  <soap:Body>
    <wsdl:ListDirectoryResponse>
      <wsdl:result>{result}</wsdl:result>
    </wsdl:ListDirectoryResponse>
  </soap:Body>
</soap:Envelope>"""
        
        return soap_response
    
    def create_soap_fault(self, code, message):
        """Crea un mensaje SOAP Fault para errores"""
        soap_fault = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_NS}">
  <soap:Body>
    <soap:Fault>
      <faultcode>soap:{code}</faultcode>
      <faultstring>{message}</faultstring>
    </soap:Fault>
  </soap:Body>
</soap:Envelope>"""
        return soap_fault

# Iniciar el servidor SOAP
def start_server():
    """Inicia el servidor SOAP"""
    server = socketserver.TCPServer(("", PORT), SOAPRequestHandler)
    print(f"Middleware SOAP iniciado en el puerto {PORT}")
    print(f"WSDL disponible en http://192.168.1.70:{PORT}/wsdl")
    server.serve_forever()

if __name__ == "__main__":
    try:
        # Verificar la conexión con el servidor RPC
        print(f"Intentando conectar con el servidor RPC en {RPC_SERVER}...")
        # Puede agregar una llamada simple aquí para verificar la conexión
        
        # Iniciar el servidor SOAP
        start_server()
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")