import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI
from llama_index.core.settings import Settings

class ChatbotCore:
    print("Estamos en el core del Chatbot")
    def __init__(self, index, prompt_general='', prompt_especifico=''):
        # Inicialización con parámetros configurables y prompts.
        self.prompt_general = prompt_general
        self.prompt_especifico = prompt_especifico
        self.prompt = self.prompt_general + " " + self.prompt_especifico 
        self.index = index   
        print("Estamos en el core del Chatbot en init")
    
    def load_index(api_key, model, temperature, persist_dir, prompt):
        os.environ["OPENAI_API_KEY"] = api_key
        if not os.path.exists(persist_dir):
            docs = SimpleDirectoryReader("datos").load_data()
            Settings.llm = OpenAI(model=model, temperature=temperature, system_prompt=prompt)
            index = VectorStoreIndex.from_documents(docs)
            index.storage_context.persist(persist_dir=persist_dir)
        else:
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            index = load_index_from_storage(storage_context)
        return index
    
    def generate_prompt(self, messages):
        prompt_user = self.prompt_general + " " + self.prompt_especifico + "\n"
        for msg in messages:
            role_prefix = "Usuario" if msg['role'] == 'user' else "Asistente"
            prompt_user += f"{role_prefix}: {msg['content']}\n"
        return prompt_user

    def get_response(self, question):
        # Obtiene la respuesta basada en la pregunta proporcionada.
        print("Estamos en el core en get response")               
        chat_engine = self.index.as_chat_engine(chat_mode="condense_question", verbose=True)        
        response = chat_engine.chat(question)
        return response.response.strip() if response.response else "Lo siento, no tengo una respuesta."
