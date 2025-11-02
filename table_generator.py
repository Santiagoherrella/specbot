"""
table_generator.py - Módulo para generación automática de tablas técnicas

Genera las dos tablas (Parámetros Eléctricos y Accesorios) en paralelo
basándose en el resumen ejecutivo generado.
"""

from promots import get_prompt_table_generator


def generar_tablas_desde_resumen(resumen_texto, llm_instance):
    """
    Genera las dos tablas técnicas a partir del resumen ejecutivo.
    
    Args:
        resumen_texto (str): El texto completo del resumen ejecutivo generado
        llm_instance: Instancia del modelo LLM (OpenAI o Gemini)
    
    Returns:
        str: Las dos tablas en formato Markdown listas para mostrar/exportar
    """
    try:
        # Obtener el prompt especializado para tablas
        prompt_tablas = get_prompt_table_generator()
        
        # Formatear el prompt con el resumen
        prompt_formateado = prompt_tablas.format(resumen=resumen_texto)
        
        # Invocar el LLM para generar las tablas
        print("🔧 Generando tablas técnicas en paralelo...")
        respuesta = llm_instance.invoke(prompt_formateado)
        
        # Extraer el contenido de la respuesta
        if hasattr(respuesta, 'content'):
            tablas_generadas = respuesta.content
        else:
            tablas_generadas = str(respuesta)
        
        print("✅ Tablas generadas exitosamente")
        return tablas_generadas
        
    except Exception as e:
        print(f"❌ Error al generar tablas: {e}")
        return f"Error al generar las tablas: {str(e)}"


def extraer_tabla_individual(tablas_completas, numero_tabla):
    """
    Extrae una tabla específica del texto completo de tablas.
    
    Args:
        tablas_completas (str): Texto con ambas tablas
        numero_tabla (int): 1 o 2 para extraer Tabla #1 o Tabla #2
    
    Returns:
        str: La tabla solicitada en formato Markdown
    """
    try:
        if numero_tabla == 1:
            # Buscar desde "Tabla #1" hasta "Tabla #2"
            inicio = tablas_completas.find("Tabla #1")
            fin = tablas_completas.find("Tabla #2")
            if inicio != -1 and fin != -1:
                return tablas_completas[inicio:fin].strip()
        elif numero_tabla == 2:
            # Buscar desde "Tabla #2" hasta el final
            inicio = tablas_completas.find("Tabla #2")
            if inicio != -1:
                return tablas_completas[inicio:].strip()
        
        return "Tabla no encontrada"
    
    except Exception as e:
        return f"Error al extraer tabla: {str(e)}"


def convertir_markdown_a_texto_excel(tabla_markdown):
    """
    Convierte una tabla en formato Markdown a texto separado por tabulaciones
    para copiar fácilmente a Excel.
    
    Args:
        tabla_markdown (str): Tabla en formato Markdown
    
    Returns:
        str: Texto separado por tabulaciones listo para Excel
    """
    try:
        lineas = tabla_markdown.split('\n')
        resultado = []
        
        for linea in lineas:
            # Ignorar líneas vacías y separadores
            if linea.strip() and not linea.strip().startswith('|---'):
                # Limpiar la línea de pipes y espacios extras
                campos = [campo.strip() for campo in linea.split('|') if campo.strip()]
                # Unir con tabulaciones
                resultado.append('\t'.join(campos))
        
        return '\n'.join(resultado)
    
    except Exception as e:
        return f"Error al convertir tabla: {str(e)}"
