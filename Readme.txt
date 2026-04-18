# Proyecto RAG - Asistente Academico Duoc UC

## Que hace
Es un sistema basico que responde preguntas sobre reglamentos y calendarios de Duoc usando documentos locales.

## Como usar
1. Crea un entorno virtual: `python -m venv venv`
2. Activalo: 
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
3. Instala dependencias: `pip install -r requirements.txt`
4. Agrega tu clave en `.env`
5. Coloca PDFs en `data/internos/`
6. Ejecuta: `python src/rag/pipeline.py`

## Decisiones de diseño (IL1.4)
- Chunk size 500: equilibrio entre contexto suficiente y precision
- FAISS: no requiere servidor externo, ideal para prototipos
- Temperatura 0.3: respuestas estables y menos creativas
- Limite: no funciona bien con tablas complejas o imagenes dentro del PDF

## Uso de IA
Se utilizo Qwen3.6 para estructura de codigo, revision de estilo y generacion de diagrama Mermaid.
Todas las pruebas y ajustes finales fueron validados manualmente.

##Version de python utilizada
3.9.13
