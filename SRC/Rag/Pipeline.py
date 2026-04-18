import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Configurar rutas y cargar Prompts locales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_PATH = os.path.normpath(os.path.join(BASE_DIR, '..', 'Prompts'))
sys.path.append(PROMPTS_PATH)

try:
    from Prompt_system import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
except ImportError:
    print("⚠️ Advertencia: No se detectó Prompt_system.py. Usando configuración básica.")
    SYSTEM_PROMPT = "Eres un asistente académico de Duoc UC."
    USER_PROMPT_TEMPLATE = "Contexto: {context}\nPregunta: {question}\nRespuesta:"

load_dotenv()

def main():
    print("=" * 50)
    print("🤖 SISTEMA RAG DUOC UC - LISTO PARA DESPEGUE")
    print("=" * 50)

    # A. CONFIGURACIÓN DEL LLM (Nube - GitHub Models)
    print("\n[1/4] Conectando con el cerebro (GPT-4o-mini)...")
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0.3,
        # Usamos la API Key directamente del entorno
        openai_api_key=os.getenv("GITHUB_TOKEN"),
        # IMPORTANTE: Esta URL es la que GitHub Models usa para compatibilidad con OpenAI
        openai_api_base="https://models.inference.ai.azure.com" 
    )

    # B. CARGA DE DOCUMENTOS (Local)
    data_folder = os.path.normpath(os.path.join(BASE_DIR, '..', '..', 'Datos', 'Internos'))
    print(f"\n[2/4] Leyendo reglamentos en: {data_folder}")
    
    docs = []
    if os.path.exists(data_folder):
        for filename in os.listdir(data_folder):
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(data_folder, filename))
                docs.extend(loader.load())
                print(f" ✅ PDF cargado: {filename}")
    
    if not docs:
        print("❌ ERROR: No se encontraron archivos PDF. Revisa la carpeta Datos/Internos.")
        return

    # C. EMBEDDINGS Y VECTOR STORE (Local - Evita errores 404)
    print("\n[3/4] Generando base de datos vectorial local...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    splits = text_splitter.split_documents(docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # D. CONFIGURACIÓN DE LA CADENA (IE5 - Arquitectura)
    print("\n[4/4] Orquestando cadena de respuesta...")
    prompt = ChatPromptTemplate.from_template(USER_PROMPT_TEMPLATE)

    chain = (
        {
            "context": retriever, 
            "question": RunnablePassthrough(),
            "system": lambda x: SYSTEM_PROMPT
        }
        | prompt 
        | llm 
        | StrOutputParser()
    )

    print("\n" + "-" * 30)
    print("✨ ASISTENTE ACTIVO. Escribe 'salir' para terminar.")
    print("-" * 30)

    while True:
        pregunta = input("\nPregunta Estudiante: ")
        if pregunta.lower() in ['salir', 'exit', 'q']: break
        if not pregunta.strip(): continue

        print("🔍 Consultando reglamentos...")
        try:
            respuesta = chain.invoke(pregunta)
            print(f"\nRespuesta IA:\n{respuesta}")
        except Exception as e:
            print(f"❌ Error al procesar la consulta: {e}")

if __name__ == "__main__":
    main()