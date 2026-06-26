import os
import sys
import time
import json
import re
import pandas as pd
import streamlit as st

# 1. INICIALIZACIÓN Y RUTAS DEL SISTEMA
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Importaciones del Backend Core de tu proyecto
from Pipeline import main as inicializar_pipeline, sanitizar_entrada_pii, registrar_metrica

# 2. CONFIGURACIÓN E IDENTIDAD DE LA INTERFAZ (MODO OSCURO INSTITUCIONAL)
st.set_page_config(
    page_title="DARA PRO - Centro de Operaciones",
    page_icon="🤖",
    layout="wide"
)

# Inyección de CSS Avanzado para forzar el contraste y legibilidad total en Fondo Oscuro
st.markdown(
    """
    <style>
        /* Fondo de la Aplicación General */
        .stApp {
            background-color: #121820 !important;
            color: #ffffff !important;
        }
        /* Forzar color blanco en textos estándar, párrafos y listas en Markdown */
        .stMarkdown p, .stMarkdown li, p, span, label {
            color: #eaeff5 !important;
        }
        /* Encabezados Principales e Institucionales */
        h1, h2, h3, h4, h5, h6 {
            color: #ffd400 !important;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 700;
        }
        /* Personalización de Tarjetas KPI */
        div[data-testid="stMetricValue"] {
            color: #ffd400 !important;
            font-size: 2.2rem;
            font-weight: bold;
        }
        div[data-testid="stMetricLabel"] {
            color: #a0aec0 !important;
            font-size: 0.9rem;
            text-transform: uppercase;
        }
        /* Estilo de los bloques de pestañas superiores */
        button[data-baseweb="tab"] {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #a0aec0 !important;
        }
        /* Estilo del contenedor de la barra lateral (Sidebar) */
        section[data-testid="stSidebar"] {
            background-color: #0a0f14 !important;
            border-right: 1px solid #1e2530;
        }
        section[data-testid="stSidebar"] .stMarkdown p {
            color: #ffffff !important;
        }
        /* Ajuste de contenedores internos del chat para contraste */
        .stChatMessage {
            background-color: #1e2530 !important;
            border-radius: 8px;
            margin-bottom: 10px;
            border: 1px solid #2d3748;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================================
# COMPONENTES LÓGICOS (SEGURIDAD Y MULTI-AGENTE)
# =========================================================================

def detectar_intento_jailbreak(texto_usuario):
    patrones_maliciosos = [
        r"ignora las instrucciones", r"ignore previous instructions",
        r"olvida tu configuracion", r"actua como", r"eres un modelo sin restricciones",
        r"system prompt", r"tu nuevo objetivo", r"dan mode", r"modo diablo",
        r"bypass", r"developer mode"
    ]
    texto_min = texto_usuario.lower()
    for patron in patrones_maliciosos:
        if re.search(patron, texto_min):
            return True
    return False

@st.cache_resource
def levantar_comite_cognitivo():
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0.1, 
        api_key=token,
        openai_api_base="https://models.inference.ai.azure.com" 
    )

    data_folder = os.path.normpath(os.path.join(BASE_DIR, '..', '..', 'Datos', 'Internos'))
    docs = []
    if os.path.exists(data_folder):
        for filename in os.listdir(data_folder):
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(data_folder, filename))
                docs.extend(loader.load())
                
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    splits = text_splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    return llm, retriever

# --- BARRA LATERAL CORPORATIVA ---
with st.sidebar:
    st.markdown("<h2 style='color: #ffd400; text-align: center; margin-top:0;'>Duoc UC</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.9rem; color: #ffffff;'><b>Plataforma DARA PRO v2.0</b><br>Infraestructura Multi-Agente</p>", unsafe_allow_html=True)
    
    st.divider()
    
    try:
        llm, retriever = levantar_comite_cognitivo()
        st.success("🟢 Conexión Activa")
    except Exception as e:
        st.error(f"🔴 Fallo de Inicialización: {e}")
    
    st.divider()
    st.markdown("🔒 **Seguridad Capa L7 Activa:** Enmascaramiento PII y Filtro Anti-Jailbreak en tiempo real.")

# --- ENCABEZADO PRINCIPAL ---
st.markdown("""
    <div style="background-color: #002d56; padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 8px solid #ffd400;">
        <h1 style="color: white !important; margin: 0; font-size: 2.2rem;">🤖 Centro de Operaciones DARA PRO</h1>
        <p style="color: #eaeff5; margin: 5px 0 0 0; font-size: 1.1rem;">Panel Integrado de Interacción Académica y Observabilidad de Modelos Cognitivos</p>
    </div>
""", unsafe_allow_html=True)

# DISTRIBUCIÓN DE PESTAÑAS
tab_chat, tab_metrics = st.tabs(["💬 Interfaz del Estudiante", "📊 Panel de Trazabilidad y KPIs"])

# --- PESTAÑA 1: CHAT DEL ESTUDIANTE ---
with tab_chat:
    st.markdown("### 🎓 Consultas de Reglamentos y Procesos Académicos")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "memoria_agentes" not in st.session_state:
        st.session_state.memoria_agentes = []

    # 1. POSICIONAMIENTO UX ESCRITORIO: La caja de preguntas se queda fija ARRIBA del todo
    prompt = st.chat_input("¿Qué deseas consultar sobre el reglamento, asistencia o asignaturas?")

    # 2. Contenedor para el historial de conversación (abajo de la barra)
    contenedor_historial = st.container()

    # Procesar la entrada si el usuario escribe algo
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        inicio_tiempo = time.time()
        error_detectado = False
        mensaje_error = ""
        ruta_actual = "DIRECTO"
        documentos_usados = []
        
        # Filtros de Seguridad
        texto_sanitizado, alerta_seguridad = sanitizar_entrada_pii(prompt)
        intento_ataque = detectar_intento_jailbreak(texto_sanitizado)
        
        if intento_ataque:
            ruta_actual = "BLOQUEO_JAILBREAK"
            alerta_seguridad = True
            respuesta_final = "🚨 **[Alerta de Seguridad]**: Se ha detectado un comando no autorizado que infringe las políticas académicas de Duoc UC. El incidente ha sido reportado en los logs inmutables."
        else:
            try:
                contexto_historial = "\n".join(st.session_state.memoria_agentes[-6:])
                
                # PROMPT FILTRO: Más permisivo con terminología universitaria/estudiantil general
                prompt_filtro = f'Analiza la consulta del estudiante: "{texto_sanitizado}". Si la consulta está relacionada directamente con la vida universitaria, reglamentos, notas, asistencia, reprobación, mallas, carreras o procesos de educación superior, responde estrictamente "SÍ". De lo contrario, responde "NO". Responde solo la palabra SÍ o NO.'
                es_academico = llm.invoke(prompt_filtro).content.strip().upper()

                if "NO" in es_academico:
                    ruta_actual = "BLOQUEO"
                    alerta_seguridad = True
                    respuesta_final = "Lo siento, como asistente oficial DARA, mi dominio de respuestas está restringido estrictamente al ámbito institucional y académico de Duoc UC."
                else:
                    # PROMPT RUTA: Enrutador dinámico refinado
                    prompt_ruta = f'Analiza el texto: "{texto_sanitizado}". Si es un saludo genérico, despedida o agradecimiento responde "DIRECTO". Si es una pregunta sobre reglas, asistencia, notas, aprobación o requisitos responde "RAG". Responde solo la palabra DIRECTO o RAG.'
                    decision_ruta = llm.invoke(prompt_ruta).content.strip().upper()

                    if "RAG" in decision_ruta:
                        ruta_actual = "RAG"
                        contexto_docs = retriever.invoke(texto_sanitizado)
                        documentos_usados = list(set([os.path.basename(d.metadata.get('source', 'Desconocido')) for d in contexto_docs]))
                        texto_contexto = "\n\n".join([d.page_content for d in contexto_docs])
                        
                        # PROMPT RAG CENTRAL: Flexibilizado para permitir inferencia semántica inteligente
                        prompt_rag = f"""
                        Eres DARA, el asistente inteligente experto en el Reglamento Académico de Duoc UC.
                        Analiza detalladamente los siguientes fragmentos extraídos de los documentos oficiales:
                        --------------------
                        {texto_contexto}
                        --------------------
                        
                        Utilizando la información anterior, responde la siguiente consulta del alumno de forma clara, precisa y profesional: "{texto_sanitizado}".
                        
                        REGLAS CRÍTICAS:
                        1. Si los documentos mencionan asistencia (como porcentajes, causales de reprobación, requisitos generales o justificaciones), usa esa información para estructurar una respuesta útil.
                        2. Solo si los fragmentos proveen información completamente ajena al tema consultado, responde únicamente la palabra "INFORMACIÓN_NO_LOCALIZADA".
                        """
                        datos_extraidos = llm.invoke(prompt_rag).content
                        
                        if "INFORMACIÓN_NO_LOCALIZADA" in datos_extraidos or len(datos_extraidos.strip()) < 10:
                            ruta_actual = "FALLBACK"
                            prompt_fallback = f'Responde de manera muy amable indicando que el dato exacto de la consulta ("{texto_sanitizado}") no pudo ser mapeado en los fragmentos del reglamento cargado en esta sesión, y recomiéndale revisar el portal o coordinar con su carrera. Firma como: Saludos cordiales,\nComité Cognitivo DARA.'
                            respuesta_final = llm.invoke(prompt_fallback).content
                        else:
                            # FORMATO PEDAGÓGICO DEFINITIVO
                            prompt_estratega = f'Toma los siguientes datos oficiales extraídos del reglamento: "{datos_extraidos}". Genera una respuesta impecable en formato de Hoja de Ruta para el estudiante que consultó: "{texto_sanitizado}". Estructura la información usando títulos, negritas y viñetas en Markdown para que sea fácil de leer en PC.'
                            respuesta_final = llm.invoke(prompt_estratega).content
                    else:
                        ruta_actual = "DIRECTO"
                        prompt_dir = f'Responde con un saludo muy cordial, atento y corporativo al estudiante. Texto del alumno: "{texto_sanitizado}". Historial reciente: {contexto_historial}. Preséntate brevemente como DARA y finaliza indicando que quedas atento a sus consultas académicas. Firma como: Saludos cordiales,\nComité Cognitivo DARA.'
                        respuesta_final = llm.invoke(prompt_dir).content

                    if "[Tu Nombre]" in respuesta_final:
                        respuesta_final = respuesta_final.replace("[Tu Nombre]", "Comité Cognitivo DARA")

            except Exception as e:
                error_detectado = True
                mensaje_error = str(e)
                ruta_actual = "ERROR"
                respuesta_final = "Lo siento, se ha registrado una anomalía de conexión."
            
            finally:
                latencia_total = time.time() - inicio_tiempo
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

        st.session_state.messages.append({"role": "assistant", "content": respuesta_final})
        st.session_state.memoria_agentes.append(f"Estudiante: {texto_sanitizado}")
        st.session_state.memoria_agentes.append(f"DARA: {respuesta_final}")

    # 3. RENDERIZACIÓN POR PARES INVERTIDOS (Los bloques más nuevos arriba, pero la Pregunta sobre la Respuesta)
    with contenedor_historial:
        lista_mensajes = st.session_state.messages
        pares = [lista_mensajes[i:i+2] for i in range(0, len(lista_mensajes), 2)]
        
        for par in reversed(pares):
            for msg in par:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

# --- PESTAÑA 2: DASHBOARD DE OBSERVABILIDAD ---
with tab_metrics:
    st.markdown("### 📊 Auditoría de Procesos en Tiempo Real")
    
    METRICS_FILE = os.path.normpath(os.path.join(BASE_DIR, '..', '..', 'Tests', 'dara_metrics.json'))
    
    if not os.path.exists(METRICS_FILE):
        st.info("💡 Realiza consultas en la pestaña anterior para visualizar la telemetría dinámica.")
    else:
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            df = pd.DataFrame(json.load(f))
            
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Transacciones Totales", f"{len(df)} peticiones")
            c2.metric("Latencia Promedio", f"{df['latencia_segundos'].mean():.2f} seg")
            c3.metric("Anomalías detectadas (IE1)", f"{df['con_error'].sum()} errores")
            c4.metric("Incidentes de Seguridad (IE6)", f"{df['alerta_seguridad_pii_jailbreak'].sum()} alertas")
            
            st.divider()
            
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("#### 📈 Monitoreo Temporal de Latencia (IE2)")
                st.line_chart(data=df, x="timestamp", y="latencia_segundos")
            with g2:
                st.markdown("#### 🤖 Distribución de Carga del Supervisor (IE4)")
                st.bar_chart(df["ruta_decision"].value_counts())
                
            st.divider()
            
            st.markdown("#### 🔍 Logs de Auditoría Operacional Inmutable (IE3)")
            st.dataframe(
                df[["timestamp", "input_usuario_anonimizado", "ruta_decision", "latencia_segundos", "documentos_fuente_auditados", "alerta_seguridad_pii_jailbreak"]], 
                use_container_width=True
            )