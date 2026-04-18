# Arquitectura de la solucion

```mermaid
graph LR
    A[Usuario] --> B[Prompt + Pregunta]
    B --> C[Orquestador / Pipeline]
    C --> D[Retriever FAISS]
    D --> E[Documentos chunked]
    E --> F[LLM + Contexto]
    F --> G[Respuesta citada]
    G --> A