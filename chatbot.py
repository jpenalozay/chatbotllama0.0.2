import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
import uuid
import json
from datetime import datetime
import os

# Configuración del prompt que guiará las respuestas del asistente
PROMPT_GENERAL = (
    "Soy un asistente virtual comprometido con responder de manera respetuosa y ética, "
    "siempre en español. Me esfuerzo por comprender y responder a todas las preguntas con claridad. "
    "Si una pregunta no está clara o está mal formulada, solicitaré una aclaración para asegurar "
    "que puedo proporcionar la información más precisa y útil posible."
)
PROMPT_ESPECIFICO = (
    "Estoy especializado en gestión de proyectos según el PMBOK. Tengo conocimientos en las áreas de "
    "iniciación, planificación, ejecución, monitoreo y control, y cierre de proyectos. "
    "Estoy aquí para responder tus preguntas específicas sobre estos temas, proporcionando "
    "asesoramiento detallado y ejemplos prácticos para ayudarte a entender y aplicar los principios del PMBOK."
)

# Configuración general del modelo y el entorno
PROMPT =  PROMPT_GENERAL + " " + PROMPT_ESPECIFICO
PERSIST_DIR = "storage"
TEMPERATURE = 0.5
MODEL = "gpt-4"
SESSION_DATA_DIR = "session_data"
LOG_DIR = "log_data"
ACTIVE_SESSIONS_FILE = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_active_sessions.json")
# Variables configurables para tiempos de inactividad (en segundos)
INACTIVITY_TIMEOUT = 300  # 5 minutos para finalización de sesión
WARNING_TIME = 60  # 1 minutos para comenzar la cuenta regresiva

# Variables de sesion
#cuestion = ""
contador = 0

# Creación de directorios necesarios si no existen
os.makedirs(SESSION_DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Definición de funciones para manejo de sesiones y logs
# Función para verificar la inactividad
def check_inactivity(session_id, messages):
    if not messages:
        return True, None  # Asume que la sesión está activa si no hay mensajes.
    
    current_time = datetime.now()
    last_interaction = datetime.strptime(messages[-1]["time"], "%Y-%m-%d %H:%M:%S")
    elapsed_time = (current_time - last_interaction).total_seconds()

    if elapsed_time >= INACTIVITY_TIMEOUT:
        return False, None  # Indica que la sesión debe finalizarse por inactividad.
    elif elapsed_time >= INACTIVITY_TIMEOUT - WARNING_TIME:
        return True, INACTIVITY_TIMEOUT - elapsed_time  # Muestra cuenta regresiva.

    return True, None  # La sesión sigue activa.

def display_inactivity_warning(session_id, messages):
    if messages:
        last_interaction = datetime.strptime(messages[-1]["time"], "%Y-%m-%d %H:%M:%S")
        elapsed_time = (datetime.now() - last_interaction).total_seconds()
        
        if INACTIVITY_TIMEOUT - WARNING_TIME <= elapsed_time < INACTIVITY_TIMEOUT:
            remaining_time = INACTIVITY_TIMEOUT - elapsed_time
            st.warning(f"Tu sesión está a punto de finalizar por inactividad. Tiempo restante: {int(remaining_time)} segundos.")

# Funciones de utilidad para manejo de sesiones y almacenamiento de datos
def save_session_data(session_id, messages):
    # Almacena los mensajes de la sesión en un archivo JSON
    session_file_path = os.path.join(SESSION_DATA_DIR, f"{session_id}.json")
    with open(session_file_path, 'w') as f:
        json.dump(messages, f)

def load_session_data(session_id):
    # Carga mensajes previos de la sesión desde un archivo JSON
    session_file_path = os.path.join(SESSION_DATA_DIR, f"{session_id}.json")
    if os.path.exists(session_file_path):
        with open(session_file_path, 'r') as f:
            return json.load(f)
    return [{"role": "assistant", "content": "Hola, ¿cómo puedo ayudarte?", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]

# Funciones para el log
def append_to_daily_log(session_summary, log_dir):
    log_file_path = os.path.join(log_dir, f"{session_summary['date']}.log")
    with open(log_file_path, 'a') as log_file:
        # Formateo y escritura del resumen de la sesión individual en el log
        log_entries = [
            f"Day: {session_summary['date']}, Session ID: {session_summary['session_id']}",
            f"Start Time: {session_summary['start_time']}, End Time: {session_summary['end_time']}",
            f"Total Session Time (seconds): {session_summary['total_session_time_seconds']}, Total User Questions: {session_summary['total_user_questions']}"
        ]
        log_file.write('\n'.join(log_entries) + '\n')
        for interaction in session_summary["interactions"]:
            log_file.write(f"{interaction['role'].title()} Time: {interaction['time']}, {interaction['role'].title()}: {interaction['content']}\n")
        log_file.write("\n")

def update_daily_summary(session_summary, log_dir):
    summary_log_path = os.path.join(log_dir, f"{session_summary['date']}_summary.log")
    
    # Actualización o creación del resumen diario
    if not os.path.exists(summary_log_path):
        # Inicialización si el archivo no existe
        total_responses = len([i for i in session_summary['interactions'] if i['role'] == 'assistant'])
        summary_content = [
            f"Day: {session_summary['date']}",
            "Total Sessions: 1",
            f"Total Session Time (seconds): {session_summary['total_session_time_seconds']}",
            f"Total Assistant Responses: {total_responses}"
        ]
    else:
        # Actualización si el archivo ya existe
        with open(summary_log_path, 'r') as summary_file:
            lines = summary_file.readlines()
        
        total_sessions = int(lines[1].split(": ")[1]) + 1
        total_time = int(lines[2].split(": ")[1]) + session_summary['total_session_time_seconds']
        total_responses = int(lines[3].split(": ")[1]) + len([i for i in session_summary['interactions'] if i['role'] == 'user'])
        summary_content = [
            f"Day: {session_summary['date']}",
            f"Total Sessions: {total_sessions}",
            f"Total Session Time (seconds): {total_time}",
            f"Total Assistant Responses: {total_responses}"
        ]

    # Escritura del resumen actualizado
    with open(summary_log_path, 'w') as summary_file:
        summary_file.write('\n'.join(summary_content) + '\n\n')

def update_active_session_log(session_id, messages):
    active_sessions = {}
    if os.path.exists(ACTIVE_SESSIONS_FILE):
        with open(ACTIVE_SESSIONS_FILE, 'r') as file:
            active_sessions = json.load(file)


    # Determina el tiempo de actividad y el número de preguntas para la sesión actual
    start_time = datetime.strptime(messages[0]["time"], "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now()
    active_sessions[session_id] = {
        "day": current_time.strftime('%Y-%m-%d'),
        "active_time_seconds": (current_time - start_time).total_seconds(),
        "number_of_questions": sum(1 for message in messages if message["role"] == "user")
    }

    # Actualiza el archivo de sesiones activas
    with open(ACTIVE_SESSIONS_FILE, 'w') as file:
        json.dump(active_sessions, file)

def clear_inactive_sessions(session_id=None):
    if os.path.exists(ACTIVE_SESSIONS_FILE):
        with open(ACTIVE_SESSIONS_FILE, 'r') as file:
            active_sessions = json.load(file)

        # Elimina la sesión actual si se ha finalizado específicamente
        if session_id and session_id in active_sessions:
            del active_sessions[session_id]
        else:
            # Aquí podrías implementar lógica adicional para detectar inactividad
            pass

        with open(ACTIVE_SESSIONS_FILE, 'w') as file:
            json.dump(active_sessions, file)

def finalize_session(messages, session_id):
    start_time = datetime.strptime(messages[0]["time"], "%Y-%m-%d %H:%M:%S")
    end_time = datetime.now()
    session_summary = {
        "date": end_time.strftime("%Y-%m-%d"),
        "session_id": session_id,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_session_time_seconds": int((end_time - start_time).total_seconds()),
        "total_user_questions": sum(1 for m in messages if m["role"] == "user"),
        "interactions": messages
    }
    #append_to_daily_log(session_summary, LOG_DIR)
    update_daily_summary(session_summary, LOG_DIR)
    clear_inactive_sessions(session_id)  # Limpia la sesión específica del log de activos
    return session_summary

@st.cache_data(show_spinner=False)
def load_data():
    # Carga o inicializa el índice de datos del chatbot
    with st.spinner(text="Procesando..."):
        if not os.path.exists(PERSIST_DIR):
            docs = SimpleDirectoryReader("datos").load_data()
            Settings.llm = OpenAI(model=MODEL, temperature=TEMPERATURE, system_prompt=PROMPT)
            index = VectorStoreIndex.from_documents(docs)
            index.storage_context.persist(persist_dir=PERSIST_DIR)
            print("Vectorizando información...")
        else:
            storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
            index = load_index_from_storage(storage_context)
            print("Recuperando información...")
    return index

index = load_data()
chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

# Inicio de la interfaz de usuario del Chatbot en Streamlit
st.header("ChatBot 📚")

# Variables
if 'show_input' not in st.session_state or 'show_button' not in st.session_state or 'finish_click' not in st.session_state:
    st.session_state.finish_click = False
    st.session_state.show_input = True
    st.session_state.show_button = True

# Recuperación o inicialización de la sesión
if "session_id" not in st.session_state:    
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []    
    print(f"Se creo un nuevo IdSesion: {st.session_state.session_id}")
    st.session_state.messages = load_session_data(st.session_state.session_id)   
else:    
    #st.session_state.messages = load_session_data(st.session_state.session_id)
    print("Se recupero información de la sesión existente")
    contador += 1
    
print(f"El contador esta en {contador}")

# Pregunta del usuario
if st.session_state.show_input:
    if cuestion := st.chat_input("Su Pregunta!"):
        question_time = datetime.now()
        # Añadir la pregunta del usuario a los mensajes de la sesión
        print(f"La sesión {st.session_state.session_id} hizo la siguiente pregunta: {cuestion}")
        st.session_state.messages.append({"role": "user", "content": cuestion, "time": question_time.strftime("%Y-%m-%d %H:%M:%S")})
        # Guardar los mensajes actualizados
        save_session_data(st.session_state.session_id, st.session_state.messages)
        # Actualizar el log de la sesión activa
        update_active_session_log(st.session_state.session_id, st.session_state.messages)


# Verificación de inactividad en cada interacción
is_active, countdown = check_inactivity(st.session_state.session_id, st.session_state.messages)

if not is_active:
    # Finalizar la sesión por inactividad y mostrar mensaje de error
    summary = finalize_session(st.session_state.messages, st.session_state.session_id)
    st.error("La sesión ha sido finalizada por inactividad.")
elif countdown is not None:
    # Mostrar la cuenta regresiva para la finalización de la sesión
    st.warning(f"Tu sesión está a punto de finalizar por inactividad. Tiempo restante: {int(countdown)} segundos.")


# Visualización de mensajes y respuesta del asistente
for message in st.session_state.messages:
    role = message["role"]
    time = message.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    content = message["content"]
    print(f"La ultima respuesta de la sesion {st.session_state.session_id} es : {content}") 
    if role == "user":
        st.caption(f"😀: {content}")
    else:  # role == "assistant"
        st.caption(f"🤖: {content}")
        
def generate_prompt(messages):
    prompt =  PROMPT_GENERAL + " " + PROMPT_ESPECIFICO + "\n"
    for msg in messages:
        if msg['role'] == 'user':
            prompt += f"Usuario: {msg['content']}\n"            
        elif msg['role'] == 'assistant':
            prompt += f"Asistente: {msg['content']}\n"
        print(f"el prompt es: {prompt}")            
    return prompt
            
# Verificar si el último mensaje es del usuario antes de esperar la respuesta del asistente
if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
    with st.spinner("Pensando..."):
        current_prompt = generate_prompt(st.session_state.messages)
        response = chat_engine.chat(current_prompt)
        response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Verificar la coherencia de la respuesta.
        if not response.response or response.response.isspace():
            response_text = "No entiendo, ¿en qué puedo ayudarte?"
        else:
            response_text = response.response
            
        message = {
            "role": "assistant",
            "content": response_text,
            "time": response_time,            
        }
        st.session_state.messages.append(message)
        save_session_data(st.session_state.session_id, st.session_state.messages)
        print(f"La respues es: {response.response}")
        st.caption(f"🤖: {response.response}")

if st.session_state.show_button:
    # Botón para finalizar manualmente la sesión
    if st.button('Finalizar Chat'):
        print("Hizo click en finalizar el chat.")
        summary = finalize_session(st.session_state.messages, st.session_state.session_id)    
        st.session_state.show_input = False
        st.session_state.show_button = False
        st.success('Chat finalizado. Gracias por usar el ChatBot.') 
