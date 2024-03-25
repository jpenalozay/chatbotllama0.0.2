# streamlit_ui.py

import streamlit as st
from datetime import datetime

class StreamlitUI:
    print("Estamos en Streamlit UI")
    def __init__(self, get_response_callback, update_session_callback, load_session_data_callback, finalize_session_callback):
        self.get_response_callback = get_response_callback
        self.update_session = update_session_callback
        self.load_session_data = load_session_data_callback
        self.finalize_session_callback = finalize_session_callback
        print("Se ingreso a Streamlit init.")

    def run(self):
        # Método principal para correr la interfaz de usuario de Streamlit.
        print("Se ingreso a Streamlit run.")
        st.header("ChatBot 📚")
        
        if "messages" not in st.session_state.keys(): # Initialize the chat message history
            print("Estamos en Streamlit run en ingresar el primer mensaje")
            st.session_state.messages = [
                {"role": "assistant", "content": "¿En que puedo ayudarte?", "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            ]
        
        if 'user_input' not in st.session_state:
            st.chat_input("Su pregunta!")
        else:
            st.session_state.user_input = st.chat_input("Su pregunta!")#, on_submit=self.handle_query) # Prompt for user input and save to chat history}
            print(f"Se ingreso la siguinete pregunta: {st.session_state.user_input}")
            if st.session_state.user_input:
                print("Se va guarda la pregunta")            
                st.session_state.messages.append({"role": "user", "content": st.session_state.user_input, "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            
        if 'user_input' not in st.session_state:
            print("Se crea y se inicializa a : user_input")
            st.session_state.user_input = ''        
        
        print(f"En Streamlit run session_id : {st.session_state.session_id} pregunto: {st.session_state.user_input}")
        self.handle_query()
        self.display_chat()
   
        if st.button('Finalizar Chat'):
            print("Se ingreso al boton finalizar el chat")
            self.finalize_session()
            st.success('Chat finalizado. Gracias por usar el ChatBot.')
            if 'session_id' in st.session_state:
                del st.session_state['session_id']

    def handle_query(self):
        print("Se ingreso a Streamlit handle query.")
        print(f"En Streamlit en handle_query. La sesion {st.session_state.session_id} ingreso la siguiente pregunta: {st.session_state.user_input}.")
        user_input = st.session_state.user_input
        if user_input:
            response = self.get_response_callback(user_input, st.session_state.session_id)
            print(f"Estamos en Streamlit Handle query. {st.session_state.session_id } pregunta:{user_input} y la respuesta: {response}")
            st.session_state.messages.append({"role": "assistant", "content": response, "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            st.session_state.user_input = ''  # Restablece el campo de entrada.

    def display_chat(self):
        print("Se ingreso a Streamlit display chat.")
        # Utiliza el callback para obtener los datos de la sesión.
        for message in st.session_state.messages:
            print("Se va visualizar los mensajes")
            with st.chat_message(message['role']): 
                st.write(message['content'])
        
    def finalize_session(self):
        print("Se ingreso a Streamlit finalize session.")
        # Aquí pasamos el session_id correctamente al callback.
        self.finalize_session_callback(st.session_state.session_id)
        if 'session_id' in st.session_state:
            del st.session_state['session_id']
