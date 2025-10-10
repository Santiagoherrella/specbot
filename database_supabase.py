"""
database_supabase.py - Módulo de gestión de base de datos PostgreSQL (Supabase)

Almacena el historial de análisis de PDFs en Supabase.
"""

import os
import psycopg2
from datetime import datetime
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener credenciales desde variables de entorno o Streamlit secrets
def get_db_connection():
    """Crea y retorna una conexión a la base de datos"""
    try:
        # Intenta obtener desde st.secrets (Streamlit Cloud)
        import streamlit as st
        conn_string = st.secrets["DATABASE_URL"]
    except:
        # Si no está en Streamlit, usa variable de entorno
        conn_string = os.getenv("DATABASE_URL")

    if not conn_string:
        raise ValueError("No se encontró DATABASE_URL en secrets o variables de entorno")

    conn = psycopg2.connect(conn_string)
    return conn

def init_database():
    """
    Inicializa la base de datos y crea la tabla si no existe.
    Se ejecuta al inicio de la aplicación.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Crear tabla de historial
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id SERIAL PRIMARY KEY,
            usuario TEXT NOT NULL,
            nombre_pdf TEXT NOT NULL,
            resumen TEXT NOT NULL,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Base de datos inicializada en Supabase")

def guardar_analisis(usuario, nombre_pdf, resumen):
    """
    Guarda un nuevo análisis en la base de datos.

    Args:
        usuario (str): Nombre del usuario que realizó el análisis
        nombre_pdf (str): Nombre del archivo PDF analizado
        resumen (str): Texto completo del resumen generado

    Returns:
        int: ID del registro insertado
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO historial (usuario, nombre_pdf, resumen, fecha_hora)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (usuario, nombre_pdf, resumen, datetime.now()))

    registro_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Análisis guardado con ID: {registro_id}")
    return registro_id

def buscar_por_nombre_pdf(nombre_pdf):
    """
    Busca si ya existe un análisis para un PDF específico.

    Args:
        nombre_pdf (str): Nombre del archivo PDF

    Returns:
        dict: Análisis encontrado o None si no existe
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id, usuario, nombre_pdf, resumen, fecha_hora
        FROM historial
        WHERE nombre_pdf = %s
        ORDER BY fecha_hora DESC
        LIMIT 1
    """, (nombre_pdf,))

    resultado = cursor.fetchone()
    cursor.close()
    conn.close()

    return resultado

def obtener_historial(usuario=None, limite=50):
    """
    Obtiene el historial de análisis.

    Args:
        usuario (str, optional): Si se especifica, filtra por usuario
        limite (int): Número máximo de registros a devolver

    Returns:
        list: Lista de diccionarios con los registros
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if usuario:
        cursor.execute("""
            SELECT id, usuario, nombre_pdf, resumen, fecha_hora
            FROM historial
            WHERE usuario = %s
            ORDER BY fecha_hora DESC
            LIMIT %s
        """, (usuario, limite))
    else:
        cursor.execute("""
            SELECT id, usuario, nombre_pdf, resumen, fecha_hora
            FROM historial
            ORDER BY fecha_hora DESC
            LIMIT %s
        """, (limite,))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    return resultados

def obtener_analisis_por_id(analisis_id):
    """
    Obtiene un análisis específico por su ID.

    Args:
        analisis_id (int): ID del análisis

    Returns:
        dict: Diccionario con los datos del análisis o None si no existe
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id, usuario, nombre_pdf, resumen, fecha_hora
        FROM historial
        WHERE id = %s
    """, (analisis_id,))

    resultado = cursor.fetchone()
    cursor.close()
    conn.close()

    return resultado

def obtener_estadisticas():
    """
    Obtiene estadísticas generales de la base de datos.

    Returns:
        dict: Diccionario con estadísticas
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total de análisis
    cursor.execute("SELECT COUNT(*) FROM historial")
    total_analisis = cursor.fetchone()[0]

    # Total de usuarios únicos
    cursor.execute("SELECT COUNT(DISTINCT usuario) FROM historial")
    total_usuarios = cursor.fetchone()[0]

    # Análisis por usuario (top 5)
    cursor.execute("""
        SELECT usuario, COUNT(*) as total
        FROM historial
        GROUP BY usuario
        ORDER BY total DESC
        LIMIT 5
    """)
    top_usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "total_analisis": total_analisis,
        "total_usuarios": total_usuarios,
        "top_usuarios": top_usuarios
    }

def eliminar_analisis(analisis_id):
    """
    Elimina un análisis específico por su ID.

    Args:
        analisis_id (int): ID del análisis a eliminar

    Returns:
        bool: True si se eliminó correctamente, False si no existía
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM historial WHERE id = %s", (analisis_id,))

    eliminado = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()

    return eliminado

def buscar_analisis(termino_busqueda):
    """
    Busca análisis que contengan un término en el nombre del PDF o el resumen.

    Args:
        termino_busqueda (str): Término a buscar

    Returns:
        list: Lista de análisis que coinciden con la búsqueda
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id, usuario, nombre_pdf, resumen, fecha_hora
        FROM historial
        WHERE nombre_pdf ILIKE %s OR resumen ILIKE %s
        ORDER BY fecha_hora DESC
    """, (f"%{termino_busqueda}%", f"%{termino_busqueda}%"))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    return resultados