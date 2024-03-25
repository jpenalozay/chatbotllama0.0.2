import json
import os
from datetime import datetime
import uuid

class SessionManager:
    # Inicializa el gestor de sesiones con el directorio especificado para almacenar los datos.
    print("Estamos en session manager")
    def __init__(self, session_data_dir="session_data", inactivity_time=0):
        self.inactivity_time=inactivity_time
        self.session_data_dir = session_data_dir
        if not os.path.exists(self.session_data_dir):
            os.makedirs(self.session_data_dir)
        print("Se ingreso a SessionManager init.")

    # Inicia una nueva sesión generando un ID único y guardando la estructura inicial de datos.
    def start_new_session(self):
        print("Se ingreso a SessionManager start new session.")
        session_id = str(uuid.uuid4())
        session_data = {
            "messages": [],  # Lista vacía de mensajes.
            "active": True,  # Estado activo de la sesión.
            "last_interaction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Momento de inicio.
        }
        self.save_session_data(session_id, session_data)
        return session_id

    # Guarda los datos de la sesión actual en un archivo JSON.
    def save_session_data(self, session_id, session_data):
        print("Estamos en la clase de sesiones en guardar la sesión.")
        session_file_path = os.path.join(self.session_data_dir, f"{session_id}.json")
        with open(session_file_path, 'w') as file:
            json.dump(session_data, file)

    # Carga los datos de la sesión desde un archivo JSON, o devuelve una estructura predeterminada.
    def load_session_data(self, session_id):
        print("Estamos en la clase de sesiones en la carga.")
        session_file_path = os.path.join(self.session_data_dir, f"{session_id}.json")
        if os.path.exists(session_file_path):
            print("Ingresamos para cargar los mensajes")
            with open(session_file_path, 'r') as file:
                return json.load(file)
        print("Ingresamos para cargar los mensajes en []")
        return {
            "messages": [],
            "active": False,
            "last_interaction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # Añade un nuevo mensaje a la sesión indicando el rol del emisor y actualiza el tiempo de interacción.
    def update_session(self, session_id, role, message_content):
        print("Estamos en la clase de sesiones en la actualización.")
        session_data = self.load_session_data(session_id)
        new_message = {
            "role": role,  # "user" o "assistant"
            "content": message_content,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        session_data["messages"].append(new_message)
        session_data["last_interaction_time"] = new_message["time"]
        print(f"Session Manager en Update Session,se agrego para {session_id},{role},{message_content}")
        self.save_session_data(session_id, session_data)
        
    # Finaliza una sesión cambiando su estado a inactivo y actualizando los datos.
    def end_session(self, session_id):
        print("Estamos en la clase de sesiones en la finalización.")
        session_data = self.load_session_data(session_id)
        session_data["active"] = False
        self.save_session_data(session_id, session_data)
        
    # Función para verificar la inactividad
    def check_inactivity(self,session_id, messages):
        if not messages:
            return True, None  # Asume que la sesión está activa si no hay mensajes.
        
        current_time = datetime.now()
        last_interaction = datetime.strptime(messages[-1]["time"], "%Y-%m-%d %H:%M:%S")
        elapsed_time = (current_time - last_interaction).total_seconds()

        if elapsed_time >= self.inactivity_time :
            return False, None  # Indica que la sesión debe finalizarse por inactividad.
        elif elapsed_time >= self.inactivity_time - WARNING_TIME:
            return True, self.inactivity_time - elapsed_time  # Muestra cuenta regresiva.

        return True, None  # La sesión sigue activa.
