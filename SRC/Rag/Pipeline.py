import os
import sys
import time
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Configurar rutas y cargar Prompts locales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_PATH = os.path.normpath(os.path.join(BASE_DIR, '..', 'Prompts'))
sys.path.append(PROMPTS_PATH)

# Ruta del archivo de metricas para la Fase 3
METRICS_FILE = os.path.normpath(os.path.join(BASE_DIR, '..', '..', 'Tests', 'dara_metrics.json'))

try:
    from Prompt_system import SYSTEM_PROMPT
except ImportError:
    SYSTEM_PROMPT = """Eres el 'Duoc Academic Research Agent' (DARA), un tutor experto e inteligente de Duoc UC.
    Tu unico objetivo es guiar a los estudiantes en reglamentos, calendarios, procesos academicos y metodologia de investigacion institucional.
    Si el estudiante te solicita tareas fuera del contexto de Duoc UC, debes rechazar amablemente indicando que tu dominio esta restringido."""

# Cargar variables desde el archivo .env
load_dotenv()

# =========================================================================
# FUNCIONES DE OBSERVABILIDAD Y SEGURIDAD (IE1, IE2, IE3, IE6)
# =========================================================================

def sanitizar_entrada_pii(texto_usuario):
    """
    IE6: Detecta y enmascara de forma proactiva datos sensibles como RUTs y Correos 
    para cumplir con las directrices de privacidad en contextos de produccion.
    """
    patron_rut = r'\b(\d{1,2}(?:\.?\d{3}){2}-[\dkK])\b|\b(\d{7,8}-[\dkK])\b'
    patron_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    texto_limpio = texto_usuario
    seguridad_activada = False
    
    if re.search(patron_rut, texto_usuario):
        texto_limpio = re.sub(patron_rut, "[RUT_ANONIMIZADO]", texto_limpio)
        seguridad_activada = True
        
    if re.search(patron_email, texto_usuario):
        texto_limpio = re.sub(patron_email, "[CORREO_ANONIMIZADO]", texto_limpio)
        seguridad_activada = True
        
    return texto_limpio, seguridad_activada

def registrar_metrica(estudiante_input, respuesta_bot, ruta_seleccionada, latencia, con_error=False, detalle_error="", documentos_auditados=None, alerta_seguridad=False):
    """
    IE1, IE2, IE3: Captura y persiste las metricas operacionales en un archivo JSON 
    para la posterior visualizacion en el Dashboard de monitoreo.
    """
    if documentos_auditados is None:
        documentos_auditados = []
        
    nueva_metrica = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_usuario_anonimizado": estudiante_input,
        "longitud_respuesta_chars": len(respuesta_bot),
        "ruta_decision": ruta_seleccionada,  # 'DIRECTO', 'RAG', 'FALLBACK' o 'BLOQUEO'
        "latencia_segundos": round(latencia, 3),
        "con_error": con_error,
        "detalle_error": detalle_error,
        "documentos_fuente_auditados": documentos_auditados,
        "alerta_seguridad_pii_jailbreak": alerta_seguridad
    }
    
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    
    historial = []
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = []
            
    historial.append(nueva_metrica)
    
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

# =========================================================================
# EJECUCION PRINCIPAL DEL PIPELINE
# =========================================================================

def main():
    print("=" * 60)
    print("🔥 ARQUITECTURA MULTI-AGENTE COGNITIVA: DARA PRO (CON OBSERVABILIDAD)")
    print("=" * 60)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: No se encontro la variable GITHUB_TOKEN en el archivo .env.")
        return

    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0.1, 
        openai_api_key=token,
        api_key=token,
        openai_api_base="https://models.inference.ai.azure.com" 
    )

    data_folder = os.path.normpath(os.path.join(BASE_DIR, '..', '..', 'Datos', 'Internos'))
    print(f"\n[1/3] Inicializando base de conocimiento y FAISS Vector Store...")
    
    docs = []
    if os.path.exists(data_folder):
        for filename in os.listdir(data_folder):
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(data_folder, filename))
                docs.extend(loader.load())
                print(f"  ✅ Documento indexado: {filename}")
    
    if not docs:
        print("ERROR: No se encontraron archivos PDF en los Datos Internos.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    splits = text_splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # SUB-AGENTE 1: El Auditor RAG (Herramienta de Consulta)
    def agente_auditor_rag(consulta_estudiante):
        print("  🔍 [Sub-Agente: Auditor RAG] Buscando evidencias en PDFs...")
        contexto_docs = retriever.invoke(consulta_estudiante)
        
        # Extraemos los nombres de los PDFs consultados para trazabilidad (IE3)
        documentos_extraidos = list(set([os.path.basename(doc.metadata.get('source', 'Desconocido')) for doc in contexto_docs]))
        texto_contexto = "\n\n".join([doc.page_content for doc in contexto_docs])
        
        prompt = f"""Basado estrictamente en este contexto institucional:
        {texto_contexto}
        
        Responde o extrae los datos clave para la siguiente consulta: "{consulta_estudiante}".
        Si la informacion no esta explicitamente en el contexto, responde unicamente con la palabra: "INFORMACIÓN_NO_ENCONTRADA"."""
        
        respuesta = llm.invoke(prompt)
        return respuesta.content, documentos_extraidos

    # SUB-AGENTE 2: El Estratega Pedagogico (Herramienta de Escritura y Razonamiento)
    def agente_estratega_pedagogico(datos_oficiales, consulta_original):
        print("  ✍️  [Sub-Agente: Estratega Pedagogico] Disenando plan de accion estrategico...")
        prompt = f"""Eres un psicopedagogo experto e institucional. Recibiste estos datos oficiales de Duoc UC:
        "{datos_oficiales}"
        
        Considerando la inquietud del alumno: "{consulta_original}", genera un plan estrategico 
        de acompanamiento en un formato tecnico y estructurado usando Markdown. Explica las reglas de forma clara 
        y disena una hoja de ruta con pasos logicos y recomendaciones organizacionales para el estudiante."""
        
        respuesta = llm.invoke(prompt)
        return respuesta.content

    print("\n[2/3] Levantando Agente Supervisor de Rutas Cognitivas...")
    
    def orquestar_comite(pregunta_usuario, historial_memoria):
        print("\n" + "-"*50)
        print(f"  🧠 [Supervisor] Evaluando complejidad e intencion de la consulta...")
        
        inicio_tiempo = time.time()
        error_detectado = False
        mensaje_error = ""
        ruta_actual = "DIRECTO"
        documentos_usados = []
        
        # Capa de Seguridad 1: Sanitizacion de Privacidad (IE6)
        texto_sanitizado, alerta_seguridad = sanitizar_entrada_pii(pregunta_usuario)
        if alerta_seguridad:
            print("  🛡️  [Seguridad] Datos sensibles detectados. Anonimizando entrada para proteccion...")
        
        try:
            contexto_historial = "\n".join(historial_memoria[-6:])
            
            # Filtro adaptativo de dominio (Seguridad de contexto - IE6)
            prompt_filtro = f"""Determina si la consulta actual: "{texto_sanitizado}" corresponde al ambito academico, curricular, 
            institucional, mallas, practicas o reglamentos de una institucion de educacion superior.
            Responde estrictamente con la palabra 'SÍ' o 'NO'."""
            
            filtro_res = llm.invoke(prompt_filtro)
            es_academico = filtro_res.content.strip().upper()

            if "NO" in es_academico:
                ruta_actual = "BLOQUEO"
                alerta_seguridad = True  # Infraccion de seguridad fuera de dominio
                respuesta_final = "Lo siento, como la plataforma oficial DARA, mi dominio de asistencia esta estrictamente restringido al ambito academico e institucional de Duoc UC. No puedo ayudarte con consultas externas."
            else:
                # Planificacion de ruta estricta
                prompt_ruta = f"""Analiza la consulta actual del alumno: "{texto_sanitizado}"
                Si el usuario solo esta saludando, despidiendose o agradeciendo de forma corta (ej: 'hola', 'gracias', 'buenas tardes'), responde 'DIRECTO'.
                Si el usuario pregunta por reglamentos, notas, fechas, mallas, convalidaciones o requisitos, responde 'RAG'."""
                
                ruta_res = llm.invoke(prompt_ruta)
                decision_ruta = ruta_res.content.strip().upper()

                if "RAG" in decision_ruta:
                    ruta_actual = "RAG"
                    datos_extraidos, documentos_usados = agente_auditor_rag(texto_sanitizado)
                    
                    if "INFORMACIÓN_NO_ENCONTRADA" in datos_extraidos or len(datos_extraidos.strip()) < 5:
                        ruta_actual = "FALLBACK"
                        print("  ⚡ [Supervisor] Datos especificos no localizados. Generando respuesta de orientacion...")
                        prompt_fallback = f"""Responde al alumno Jesus sobre su duda actual: "{texto_sanitizado}".
                        Historial de la sesion: {contexto_historial}
                        Indicale de forma muy clara y educada que el dato exacto no se encuentra en el archivo normativo actual de la base de datos, y orientalo contextualmente segun su caso.
                        Firma estrictamente al final como: 'Saludos cordiales,\nComite Cognitivo DARA'."""
                        respuesta_final = llm.invoke(prompt_fallback).content
                    else:
                        consulta_contextualizada = f"Pregunta actual: {texto_sanitizado}\nHistorial previo:\n{contexto_historial}"
                        respuesta_final = agente_estratega_pedagogico(datos_extraidos, consulta_contextualizada)
                else:
                    ruta_actual = "DIRECTO"
                    print("  ⚡ [Supervisor] Procesando saludo o interaccion corta de forma directa...")
                    prompt_directo = f"""Responde de forma amable, ejecutiva y breve al saludo del alumno Jesus.
                    Historial previo: {contexto_historial}
                    Pregunta: {texto_sanitizado}
                    Firma estrictamente al final como: 'Saludos cordiales,\nComite Cognitivo DARA'."""
                    respuesta_final = llm.invoke(prompt_directo).content

            # Post-procesamiento de firmas
            if "[Tu Nombre]" in respuesta_final or "Jesus" in respuesta_final[-30:]:
                respuesta_final = respuesta_final.replace("[Tu Nombre]", "Comite Cognitivo DARA")
                if "Jesus" in respuesta_final[-20:]:
                    respuesta_final = respuesta_final.split("Saludos")[0] + "\nSaludos cordiales,\nComite Cognitivo DARA"

        except Exception as e:
            error_detectado = True
            mensaje_error = str(e)
            ruta_actual = "ERROR"
            respuesta_final = "Lo siento, ha ocurrido un error interno en el comite de agentes."
            print(f"  ❌ [Error de Sistema]: {mensaje_error}")

        finally:
            latencia_total = time.time() - inicio_tiempo
            # Guardar metricas automaticamente en cada ciclo (IE1, IE2, IE3)
            registrar_metrica(
                estudiante_input=texto_sanitizado,
                respuesta_bot=respuesta_final,
                ruta_seleccionada=ruta_actual,
                latencia=latencia_total,
                con_error=error_detectado,
                detalle_error=mensaje_error,
                documentos_auditados=documentos_usados,
                alerta_seguridad=alerta_seguridad
            )

        historial_memoria.append(f"Estudiante: {texto_sanitizado}")
        historial_memoria.append(f"DARA: {respuesta_final}")
        return respuesta_final

    print("\n[3/3] Orquestacion y estado del sistema inicializado con exito.")
    print("-" * 65)
    print("✨ COMITÉ MULTI-AGENTE 'DARA PRO' EN LÍNEA. Escribe 'salir' para finalizar.")
    print("-" * 65)

    memoria_sesion = []

    while True:
        pregunta = input("\nEstudiante: ")
        if pregunta.lower() in ['salir', 'exit', 'q']: break
        if not pregunta.strip(): continue

        try:
            respuesta = orquestar_comite(pregunta, memoria_sesion)
            print(f"\n🔹 RESPUESTA FINAL DEL COMITÉ DARA:\n{respuesta}")
        except Exception as e:
            print(f" Anomalía detectada en el ciclo cognitivo del comite: {e}")

if __name__ == "__main__":
    main()