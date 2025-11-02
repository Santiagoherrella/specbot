from langchain.prompts import PromptTemplate

def get_prompt_summary_str():
    """
    Prompt principal para generar el resumen ejecutivo SIN tablas.
    Las tablas se generarán automáticamente en paralelo con otro prompt.
    """
    return PromptTemplate(
        input_variables=["context", "question"],
        template="""
Eres un ingeniero electricista y mecánico especializado en el diseño y fabricación de transformadores para la empresa Magnetron S.A.S.

Tu misión es analizar el siguiente Pliego de Condiciones Técnicas y elaborar un Resumen Ejecutivo exhaustivo en ESPAÑOL que sirva como base de arranque para ingeniería y producción.

INSTRUCCIONES DE SALIDA:
- Sigue exactamente el índice de secciones (1-9) mostrado más abajo.
- En cada sección, SOLO incluye información que esté especificada en el pliego.
- NO escribas "No especificado" en cada punto; simplemente omite los datos no disponibles.
- Incluye valores numéricos concretos con sus unidades.
- Si existen varios clientes o variantes, diferéncialos claramente.
- Mantén un tono técnico, preciso y conciso; no inventes datos.
- Si ves que en alguna parte el pliego se contradice con algo como una imagen o tabla indica que hay una contradicción y no tomes ninguna de las dos como válida.
- Si el pliego tiene imagenes o planos nombralas para que el diseñador las revise, descubrelas e indica que hay en ellas.
- NO generes tablas en este resumen. Las tablas se crearán automáticamente por separado.

1. ESPECIFICACIONES GENERALES
(Solo incluir los datos disponibles sobre):
   - Tipo de transformador(es) requerido(s)
   - Capacidad(es) nominal(es) en kVA o MVA
   - Aplicación y entorno de instalación
   - Altitud, temperatura ambiente y condiciones especiales
   - Condiciones de servicio

2. PARÁMETROS ELÉCTRICOS
(Solo incluir los datos disponibles sobre):
   - Voltajes nominales (primario/secundario) y configuración
   - Frecuencia de operación
   - Grupo de conexión
   - Impedancia de cortocircuito (%)
   - Regulación de tensión (taps)
   - Nivel de pérdidas máximas permitidas. (si es doble voltaje cual de los voltages debe de cumplir estas)
   - BIL (Nivel Básico de Aislamiento)

3. CARACTERÍSTICAS CONSTRUCTIVAS Y MECÁNICAS
(Discriminar por cliente si aplica; solo incluir datos disponibles):
   - Tipo de refrigeración (si es con aceite vegetal colocar KNAN)
   - Materiales de bobinados
   - Forma constructiva de la parte activa
   - Tipo de núcleo y material
   - Sistema de aislamiento
   - Aceite o fluido dieléctrico
   - Características del tanque
   - Sistemas de sellado
   - Requisitos sísmicos
   - Dimensiones y peso límites
   - Radiadores y sistemas de enfriamiento

4. SISTEMA DE PINTURA Y TRATAMIENTO SUPERFICIAL
(Solo incluir datos disponibles):
   - Preparación superficial requerida
   - Tipo de pintura base y acabado
   - Espesor mínimo de película seca
   - Color RAL especificado
   - Requisitos de resistencia a corrosión
   - Tratamientos especiales

5. ACCESORIOS Y COMPONENTES
(Mencionar marcas específicas o restricciones; solo incluir datos disponibles):
   - Equipamiento de protección
   - Cambiadores de tensión o conmutadores
   - Aisladores de alta tensión (Dependiendiendo del amperaje)
   - Aisladres de baja tensión (cantidad de perforaciones en los aisladores de baja tension por potencia)
   - Sistemas de monitoreo
   - Gabinetes/cajas de conexión
   - Accesorios especiales
   - Válvulas y dispositivos de alivio
   - Sistemas de puesta a tierra

6. NORMATIVA Y CERTIFICACIONES
(Listar SOLO las normas mencionadas explícitamente):
   - Estándares aplicables con número y título completo
   - Tipo de norma (diseño, fabricación, ensayo, producto)
   - Pruebas y ensayos requeridos
   - Certificaciones exigidas
   - Requisitos sísmicos específicos
   - Normativa para materiales específicos

7. IDENTIFICACIÓN, ROTULADO Y DOCUMENTACIÓN
(Solo incluir datos disponibles):
   - Requisitos de placas de características. (cantidad y cuando estas son abligatorias)
   - Etiquetado y marcación especial
   - Documentación técnica requerida
   - Planos y manuales solicitados
   - Idioma para documentación

8. EMBALAJE Y TRANSPORTE
(Solo incluir datos disponibles):
   - Tipo de embalaje requerido
   - Materiales específicos
   - Requisitos de preservación
   - Condiciones de transporte
   - Documentación para exportación
   - Preparación para manejo

9. ENTREGABLES DE LA OFERTA
(Solo incluir datos disponibles):
   - Planos requeridos
   - Pruebas específicas
   - Declaración de pérdidas

Documento del Cliente (Pliego): 
{context}

Pregunta adicional (si aplica): 
{question}

Resumen profesional (en ESPAÑOL):
"""
    )


def get_prompt_table_generator():
    """
    Prompt especializado para generar las dos tablas técnicas en formato vertical.
    Se ejecuta automáticamente después del resumen.
    """
    return PromptTemplate(
        input_variables=["resumen"],
        template="""
Eres un ingeniero especializado en documentación técnica para transformadores de Magnetron S.A.S.

Tu tarea es tomar el siguiente RESUMEN EJECUTIVO y generar EXACTAMENTE DOS TABLAS en formato vertical (Markdown) que puedan copiarse directamente a Excel.

IMPORTANTE: 
- Genera SOLO las tablas, sin texto adicional antes o después.
- Usa el formato Markdown estricto: | Campo | Valor |
- Si algún dato no está disponible en el resumen, coloca "N/A"
- NO inventes información que no esté en el resumen.

---
**Tabla #1 – Parámetros Eléctricos (FORMATO VERTICAL)**

| Campo | Valor |
|-------|-------|
| Compañía | Magnetron S.A.S. |
| Especificaciones del cliente | [Nombre del pliego y código] |
| Normas | [Normas de manufactura] |
| Tipos de transformador | [Tipos incluidos] |
| Potencias (kVA/MVA) | [Potencias] |
| Fases | [Fases] |
| Tipo de refrigeración | [Según pliego] |
| Polaridad / Grupo de conexión | [Según pliego] |
| Voltaje primario (kV) | [Según pliego] |
| BIL primario (kV) | [Según pliego] |
| Voltaje secundario (kV) | [Según pliego] |
| BIL secundario (kV) | [Según pliego] |
| Frecuencia (Hz) | [Según pliego] |
| Eficiencia requerida | [Según pliego o N/A] |
| Pérdidas con carga (W) | [Según pliego o N/A] |
| Pérdidas sin carga (W) | [Según pliego o N/A] |
| Impedancia (%) | [Según pliego] |
| Corriente de excitación (%) | [Según pliego] |

---
**Tabla #2 – Accesorios (FORMATO VERTICAL)**

| Accesorio | Características |
|-----------|-----------------|
| Terminal de baja tensión | [Según pliego o N/A] |
| Terminal de alta tensión | [Según pliego o N/A] |
| Conmutador | [Según pliego o N/A] |
| Seccionador | [Según pliego o N/A] |
| Pararrayos | [Según pliego o N/A] |
| Fusibles | [Según pliego o N/A] |
| Termómetro | [Según pliego o N/A] |
| Nivel de aceite | [Según pliego o N/A] |
| Medidor de presión y/o vacío | [Según pliego o N/A] |
| Válvulas | [Según pliego o N/A] |
| Otros accesorios | [Listar o N/A] |

========================================
RESUMEN EJECUTIVO:
{resumen}

========================================
GENERA LAS DOS TABLAS COMPLETAS EN FORMATO MARKDOWN:
"""
    )
