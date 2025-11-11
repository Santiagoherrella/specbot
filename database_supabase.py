"""
database_supabase.py - Módulo de gestión de base de datos PostgreSQL (Supabase)
Almacena el historial de análisis de PDFs en Supabase.
Detecta automáticamente si está en modo desarrollo o producción.
Trabaja con la tabla HISTORIAL existente.
"""

import os
import psycopg2
from datetime import datetime
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Detectar el entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def is_production():
    """Verifica si la aplicación está corriendo en producción"""
    return ENVIRONMENT.lower() == "production"

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
    Verifica y actualiza la tabla historial existente.
    Solo agrega la columna tablas_tecnicas si no existe.
    NO crea una nueva tabla.
    """
    if not is_production():
        print("⚠️ MODO DESARROLLO - Base de datos no se modificará")
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Solo agregar columna tablas_tecnicas si no existe
        cur.execute("""
            DO $$ 
            BEGIN 
                BEGIN
                    ALTER TABLE historial ADD COLUMN tablas_tecnicas TEXT;
                    RAISE NOTICE 'Columna tablas_tecnicas agregada';
                EXCEPTION
                    WHEN duplicate_column THEN 
                        RAISE NOTICE 'Columna tablas_tecnicas ya existe';
                END;
            END $$;
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tabla historial verificada y actualizada (PRODUCCIÓN)")
    except Exception as e:
        print(f"❌ Error al verificar tabla historial: {e}")

def guardar_analisis(usuario, nombre_pdf, resumen, tablas=None):
    """
    Guarda el análisis en la tabla historial existente (solo en producción).
    
    Args:
        usuario (str): Nombre del usuario que realizó el análisis
        nombre_pdf (str): Nombre del archivo PDF analizado
        resumen (str): Texto completo del resumen generado
        tablas (str, optional): Tablas técnicas generadas
    
    Returns:
        int o bool: ID del registro insertado en producción, True en desarrollo
    """
    if not is_production():
        print(f"⚠️ MODO DESARROLLO - No se guardará en base de datos: {nombre_pdf}")
        return True
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO historial (usuario, nombre_pdf, resumen, tablas_tecnicas, fecha_hora)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (usuario, nombre_pdf, resumen, tablas, datetime.now()))
        
        registro_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Análisis guardado en historial (PRODUCCIÓN): {nombre_pdf} - ID: {registro_id}")
        return registro_id
    except Exception as e:
        print(f"❌ Error al guardar en base de datos: {e}")
        return False

def buscar_por_nombre_pdf(nombre_pdf):
    """
    Busca si ya existe un análisis para un PDF específico en historial (solo en producción).
    
    Args:
        nombre_pdf (str): Nombre del archivo PDF
    
    Returns:
        dict: Análisis encontrado o None si no existe
    """
    if not is_production():
        print(f"⚠️ MODO DESARROLLO - No se buscará en base de datos: {nombre_pdf}")
        return None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, usuario, nombre_pdf, resumen, tablas_tecnicas, fecha_hora
            FROM historial
            WHERE nombre_pdf = %s
            ORDER BY fecha_hora DESC
            LIMIT 1
        """, (nombre_pdf,))
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        if resultado:
            print(f"✅ Análisis previo encontrado en historial (PRODUCCIÓN): {nombre_pdf}")
        
        return resultado
    except Exception as e:
        print(f"❌ Error al buscar en base de datos: {e}")
        return None

def obtener_historial(usuario=None, limite=50):
    """
    Obtiene el historial de análisis (solo en producción).
    
    Args:
        usuario (str, optional): Si se especifica, filtra por usuario
        limite (int): Número máximo de registros a devolver
    
    Returns:
        list: Lista de diccionarios con los registros
    """
    if not is_production():
        print("⚠️ MODO DESARROLLO - No hay historial disponible")
        return []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if usuario:
            cur.execute("""
                SELECT id, usuario, nombre_pdf, resumen, tablas_tecnicas, fecha_hora
                FROM historial
                WHERE usuario = %s
                ORDER BY fecha_hora DESC
                LIMIT %s
            """, (usuario, limite))
        else:
            cur.execute("""
                SELECT id, usuario, nombre_pdf, resumen, tablas_tecnicas, fecha_hora
                FROM historial
                ORDER BY fecha_hora DESC
                LIMIT %s
            """, (limite,))
        
        resultados = cur.fetchall()
        cur.close()
        conn.close()
        
        return resultados
    except Exception as e:
        print(f"❌ Error al obtener historial: {e}")
        return []

def obtener_analisis_por_id(analisis_id):
    """
    Obtiene un análisis específico por su ID de la tabla historial (solo en producción).
    
    Args:
        analisis_id (int): ID del análisis
    
    Returns:
        dict: Diccionario con los datos del análisis o None si no existe
    """
    if not is_production():
        print(f"⚠️ MODO DESARROLLO - No se buscará análisis por ID: {analisis_id}")
        return None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, usuario, nombre_pdf, resumen, tablas_tecnicas, fecha_hora
            FROM historial
            WHERE id = %s
        """, (analisis_id,))
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        return resultado
    except Exception as e:
        print(f"❌ Error al obtener análisis por ID: {e}")
        return None

def obtener_estadisticas():
    """
    Obtiene estadísticas generales de la tabla historial (solo en producción).
    
    Returns:
        dict: Diccionario con estadísticas
    """
    if not is_production():
        print("⚠️ MODO DESARROLLO - No hay estadísticas disponibles")
        return {
            "total_analisis": 0,
            "total_usuarios": 0,
            "top_usuarios": []
        }
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total de análisis
        cur.execute("SELECT COUNT(*) FROM historial")
        total_analisis = cur.fetchone()[0]
        
        # Total de usuarios únicos
        cur.execute("SELECT COUNT(DISTINCT usuario) FROM historial")
        total_usuarios = cur.fetchone()[0]
        
        # Análisis por usuario (top 5)
        cur.execute("""
            SELECT usuario, COUNT(*) as total
            FROM historial
            GROUP BY usuario
            ORDER BY total DESC
            LIMIT 5
        """)
        top_usuarios = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "total_analisis": total_analisis,
            "total_usuarios": total_usuarios,
            "top_usuarios": top_usuarios
        }
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {e}")
        return {
            "total_analisis": 0,
            "total_usuarios": 0,
            "top_usuarios": []
        }
