# Proyecto DARA PRO - Asistente Academico Multi-Agente Duoc UC

## Que hace el sistema
Es un Centro de Operaciones e Infraestructura Multi-Agente avanzada basada en un motor RAG (Retrieval-Augmented Generation). 
Permite auditar, trazar y responder consultas complejas sobre reglamentos institucionales y procesos academicos de Duoc UC utilizando bases de datos vectoriales locales.

## Guia de Instalacion y Uso
1. Crear un entorno virtual: python -m venv venv
2. Activalo: 
   - Windows (PowerShell/CMD): venv\Scripts\activate
   - Mac / Linux: source venv/bin/activate
3. Instalar dependencias del sistema: pip install -r requirements.txt
4. Configurar credenciales: Crea un archivo .env en la raiz del proyecto y agrega tu token de infraestructura: GITHUB_TOKEN=tu_token_aqui
5. Cargar Documentacion Institucional: Fijarse en los archivos PDF del reglamento en la ruta corporativa exacta: Datos/Internos/
6. Ejecutar el Centro de Operaciones (Dashboard): streamlit run SRC/Rag/Dashboard.py

## Decisiones de Diseno e Ingenieria
- Estrategia de Chunking (Size 1000 / Overlap 150): Se expandio el tamano de corte a 1000 caracteres para capturar articulos reglamentarios completos de Duoc UC sin fragmentar las clausulas juridicas, manteniendo un overlap de 150 para no perder la coherencia semantica entre bloques adyacentes.
- Base Vectorial FAISS (cpu): Implementacion en local empotrada que no requiere servidores ni costos de infraestructura externa, garantizando portabilidad absoluta y despliegue rapido en la maquina de evaluacion.
- Modelo Cognitivo (GPT-4o-Mini a traves de GitHub Models): Configurado con una temperatura baja de 0.1 para mitigar alucinaciones y forzar respuestas estrictamente deterministas basadas en el reglamento institucional.
- Limites Detectados: Limitacion en la lectura nativa de estructuras tabulares densas u diagramas complejos embebidos dentro de archivos PDF escaneados.

## EVALUACION 3 - Innovacion en Usabilidad y UX (PC Desktop)
A diferencia de las interfaces de chat moviles tradicionales (donde la entrada de texto se ubica en la base), la plataforma DARA PRO implementa un diseno invertido adaptado especialmente para pantallas de escritorio:
- Entrada Superior Fija: Reduce drasticamente la fatiga visual al mantener el foco y la barra de busqueda en el cuadrante superior de la pantalla, evitando desplazamientos oculares innecesarios.
- Renderizado por Pares Invertidos: Agrupa cronologicamente cada bloque de interaccion (Pregunta/Respuesta), posicionando el par mas reciente en el tope del contenedor para asegurar claridad y visibilidad inmediata en monitores anchos de PC.
- Modo Oscuro de Alta Fidelidad: Sincroniza la paleta de colores institucional de Duoc UC (Azul marino y acentos amarillos) con un fondo atenuado de bajo contraste, optimizando la legibilidad de las hojas de ruta generadas en Markdown.

## Declaracion de Uso de IA
Se utilizo asistencia de IA avanzada para la aceleracion del desarrollo, estructuracion de layouts de CSS, revision de estilos de interfaces y optimizacion del enrutador jerarquico del Supervisor. Todos los casos de prueba operativos, enmascaramiento de PII y flujos de blindaje perimetral anti-jailbreak fueron validados y auditados manualmente.

## Version de Python utilizada
3.9.13