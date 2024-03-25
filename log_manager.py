import os
import json
from datetime import datetime

class LogManager:
    print("Estamos en el Log Manager")
    def __init__(self, log_dir):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        print("Estamos en el Log Manager en el procesos de init")

    # Añade un resumen de la Sesion al log diario
    def append_to_daily_log(self, session_summary):
        print("Estamos en el Log Manager en el procesos de agregar log diario")
        log_file_path = os.path.join(self.log_dir, f"{session_summary['date']}.log")
        with open(log_file_path, 'a') as log_file:
            log_entries = [
                f"Dia: {session_summary['date']}, Sesion Id: {session_summary['session_id']}",
                f"Comienzo: {session_summary['start_time']}, Fin: {session_summary['end_time']}",
                f"Tiempo Total (segundo): {session_summary['total_session_time_seconds']}, Total Preguntas: {session_summary['total_user_questions']}"
            ]
            log_file.write('\n'.join(log_entries) + '\n')
            for interaction in session_summary["interactions"]:
                log_file.write(f"Fecha_Hora: {interaction['time']}, Rol: {interaction['role'].title()}, Contenido: {interaction['content']}\n")
            log_file.write("\n")

    # Actualiza o crea un resumen diario de las sesiones
    def update_active_session_log(self, session_id, messages):
        print("Estamos en el Log Manager en el procesos de actualizar el log de sesiones activas")
        active_sessions_file = os.path.join(self.log_dir, "active_sessions.json")
        print(f"Se ingreso al proceso de actualización del log de sesiones activas y se agrego a {session_id}")
        # Verifica si el archivo existe y contiene datos.
        if os.path.exists(active_sessions_file) and os.stat(active_sessions_file).st_size != 0:
            with open(active_sessions_file, 'r') as file:
                active_sessions = json.load(file)
        else:
            active_sessions = {}

        # Para calcular correctamente los segundos activos, ambos tiempos deben ser datetime objects.
        if messages:
            start_time = datetime.strptime(messages[0]["time"], "%Y-%m-%d %H:%M:%S")
        else:
            start_time = datetime.now()
        active_sessions[session_id] = {
            "Dia": datetime.now().strftime('%Y-%m-%d'),
            # Aquí deberías asegurarte de calcular correctamente el tiempo activo.
            "Tiempo Actividad (segundos)": (datetime.now() - start_time).total_seconds(),
            "Numero Preguntas": len([m for m in messages if m["role"] == "user"])
        }

        # Escribe la información actualizada de nuevo en el archivo.
        with open(active_sessions_file, 'w') as file:
            json.dump(active_sessions, file)

    # Actualiza un resumen diario existente
    def update_existing_summary(self, summary_log_path, session_summary):
        print("Estamos en el Log Manager en el procesos de actualizar el sumario")
        hoy=datetime.now().strftime('%Y-%m-%d')
        summary_file_path  = os.path.join(summary_log_path, f"resumen_{hoy}")
            
        if os.path.exists(summary_file_path ) and os.path.getsize(summary_file_path ) > 0:
            with open(summary_file_path , 'r') as file:
                lines = file.readlines()
        else:
            lines = []
            
        # Extrae los totales del archivo si tiene las líneas necesarias, de lo contrario inicializa los contadores.
        if len(lines) >= 4:
            total_sessions = int(lines[1].split(": ")[1].strip()) + 1
            total_time = int(lines[2].split(": ")[1].strip()) + session_summary['total_session_time_seconds']
            total_responses = int(lines[3].split(": ")[1].strip()) + len([i for i in session_summary['interactions'] if i['role'] == 'assistant'])
        else:
            # Inicializa los totales si el archivo de resumen es nuevo o está mal formado.
            total_sessions = 1
            total_time = session_summary['total_session_time_seconds']
            total_responses = len([i for i in session_summary['interactions'] if i['role'] == 'assistant'])
        
        # Escribe el contenido actualizado en el archivo de resumen.
        with open(summary_file_path, 'w') as file:
            file.write(f"Dia: {hoy}\n")
            file.write(f"Total Sesiones: {total_sessions}\n")
            file.write(f"Tiempo Total Sesiones (segundos): {total_time}\n")
            file.write(f"Total Asistente Respuestas: {total_responses}\n")
        return {
            'day': hoy,
            'total_sessions': total_sessions,
            'total_time': total_time,
            'total_responses': total_responses
        }

    # Elimina las sesiones inactivas o cerradas del registro de sesiones activas
    def clear_inactive_sessions(self,path_name, session_id):
        self.session_id = session_id        
        print("Estamos en el Log Manager en el procesos de limpiar log de sesiones activas")
        active_sessions_file = os.path.join(path_name, "active_sessions.json")
        if os.path.exists(active_sessions_file) and os.path.getsize(active_sessions_file) > 0:
            print("Encontro el archivo")
            with open(active_sessions_file, 'r') as file:
                active_sessions = json.load(file)

            if self.session_id and self.session_id in active_sessions:
                del active_sessions[self.session_id]

            with open(active_sessions_file, 'w') as file:
                json.dump(active_sessions, file)
        else:
            print("No encontro el archivo")
