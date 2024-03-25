from chatbot_core import ChatbotCore
from session_manager import SessionManager
from streamlit_ui import StreamlitUI
from log_manager import LogManager
from datetime import datetime
import streamlit as st
import os

print("Se ingreso a main.")
# Definir parámetros iniciales o cargarlos de un archivo de configuración/env.

API_KEY = os.getenv('OPENAI_API_KEY')
if API_KEY is None:
    raise Exception("Por favor, configura la variable de entorno OPENAI_API_KEY.")
MODEL = 'gpt-4'
TEMPERATURE = 0.5
PERSIST_DIR = 'storage'
SESSION_DATA_DIR = 'session_data'
LOG_DIR = 'log_data'

# Variables configurables para tiempos de inactividad (en segundos)
INACTIVITY_TIMEOUT = 300  # 5 minutos para finalización de sesión
WARNING_TIME = 60  # 1 minutos para comenzar la cuenta regresiva

# Configuración del prompt que guiará las respuestas del asistente
PROMPT_GENERAL = ""
PROMPT_ESPECIFICO = ""
PROMPT = PROMPT_GENERAL + " " + PROMPT_ESPECIFICO
with st.spinner(text="Procesando..."):
    index = ChatbotCore.load_index(API_KEY, MODEL, TEMPERATURE, PERSIST_DIR, PROMPT)

# Inicializa las clases a utilizar
print("Estamos en main y empezaremos a inicializar los componentes")
chatbot_core = ChatbotCore(index, PROMPT_GENERAL, PROMPT_ESPECIFICO)  # Asume la inicialización adecuada de tu ChatbotCore.
session_manager = SessionManager(SESSION_DATA_DIR,INACTIVITY_TIMEOUT)
log_manager = LogManager(LOG_DIR)

# Callback para obtener respuestas del chatbot
def get_response(user_input, session_id):
    print("Estamos en main en el proceso de get response")
    response = chatbot_core.get_response(user_input)
    session_manager.update_session(session_id, "user", user_input)
    session_manager.update_session(session_id, "assistant", response)
    log_manager.update_active_session_log(st.session_state['session_id'],st.session_state.messages) 
    return response

streamlit_ui = StreamlitUI(
    get_response_callback=get_response,
    update_session_callback=session_manager.update_session,
    load_session_data_callback=session_manager.load_session_data,
    finalize_session_callback=lambda session_id: finalize_session(session_id),
)

def start_session():
    print("Estamos en main en el proceso de inicio de sesión")    
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = session_manager.start_new_session()
        print(f"Se creo la sesión con Id: {st.session_state['session_id']}")    
        log_manager.update_active_session_log(st.session_state['session_id'], [])       
    streamlit_ui.run()

def finalize_session(session_id):
    print("Estamos en main en el proceso de fin de sesión")
    # Función para finalizar la sesión y actualizar el log
    session_data = session_manager.load_session_data(session_id)    
    session_end_time = datetime.now()   
    session_start_time = datetime.strptime(session_data['messages'][0]['time'], "%Y-%m-%d %H:%M:%S") if session_data['messages'] else session_end_time
    session_summary = {
       'date': session_end_time.strftime('%Y-%m-%d'),
        'session_id': session_id,
        'start_time': session_start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': session_end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_session_time_seconds': (session_end_time - session_start_time).total_seconds(),
        'total_user_questions': len([m for m in session_data['messages'] if m['role'] == 'user']),
        'interactions': session_data['messages']
    }
    log_manager.append_to_daily_log(session_summary)
    log_manager.update_existing_summary(LOG_DIR, session_summary)  # Actualiza resumen diario.
    session_manager.end_session(session_id)
    
    log_manager.clear_inactive_sessions(LOG_DIR, session_id)

start_session()