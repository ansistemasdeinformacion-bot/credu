import psycopg2
import os
import pandas as pd
from datetime import datetime

# Configuración de la base de datos (desde variables de entorno)
def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Para desarrollo local (instalar PostgreSQL localmente)
        return psycopg2.connect(
            host="localhost",
            database="credu_db",
            user="postgres",
            password="tu_contraseña"
        )
    return psycopg2.connect(database_url)

def init_db_pg():
    """Inicializa las tablas en PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de docentes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS docentes (
            id SERIAL PRIMARY KEY,
            cedula VARCHAR(20) UNIQUE NOT NULL,
            nombre_completo VARCHAR(200) NOT NULL,
            correo VARCHAR(100) UNIQUE NOT NULL,
            contraseña VARCHAR(100) NOT NULL,
            personalizada BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de consultas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultas_pg (
            id SERIAL PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            correo VARCHAR(100) NOT NULL,
            cedula VARCHAR(20) NOT NULL,
            nombre VARCHAR(200) NOT NULL,
            mes INTEGER,
            año INTEGER,
            dia INTEGER,
            hora INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos PostgreSQL inicializada")

def migrar_excel_a_postgres(excel_path="docentes.xlsx"):
    """Migra todos los docentes del Excel a PostgreSQL"""
    try:
        df = pd.read_excel(excel_path)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        migrados = 0
        errores = 0
        
        for _, row in df.iterrows():
            try:
                cedula = str(row['CEDULA']).strip()
                nombre = str(row['NOMBRE COMPLETO']).strip()
                correo = str(row['CORREO INSTITUCIONAL']).strip().lower()
                contraseña = str(row['CONTRASEÑA']).strip()
                personalizada = "personalizada" in contraseña.lower()
                
                cursor.execute('''
                    INSERT INTO docentes (cedula, nombre_completo, correo, contraseña, personalizada)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (cedula) DO UPDATE SET
                        nombre_completo = EXCLUDED.nombre_completo,
                        correo = EXCLUDED.correo,
                        contraseña = EXCLUDED.contraseña,
                        personalizada = EXCLUDED.personalizada,
                        updated_at = CURRENT_TIMESTAMP
                ''', (cedula, nombre, correo, contraseña, personalizada))
                migrados += 1
            except Exception as e:
                print(f"Error migrando fila: {e}")
                errores += 1
        
        conn.commit()
        conn.close()
        return {"success": True, "migrados": migrados, "errores": errores}
    except Exception as e:
        return {"success": False, "error": str(e)}

def obtener_docente_por_cedula(cedula):
    """Obtiene un docente por su cédula"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cedula, nombre_completo, correo, contraseña, personalizada
        FROM docentes WHERE cedula = %s
    ''', (cedula,))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        return {
            "cedula": resultado[0],
            "nombre": resultado[1],
            "correo": resultado[2],
            "contraseña": resultado[3],
            "personalizada": resultado[4]
        }
    return None

def obtener_todos_docentes():
    """Obtiene todos los docentes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT cedula, nombre_completo, correo, contraseña, personalizada FROM docentes ORDER BY nombre_completo')
    resultados = cursor.fetchall()
    conn.close()
    return [{"cedula": r[0], "nombre": r[1], "correo": r[2], "contraseña": r[3], "personalizada": r[4]} for r in resultados]

def agregar_docente(cedula, nombre, correo, contraseña):
    """Agrega un nuevo docente"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        personalizada = "personalizada" in contraseña.lower()
        cursor.execute('''
            INSERT INTO docentes (cedula, nombre_completo, correo, contraseña, personalizada)
            VALUES (%s, %s, %s, %s, %s)
        ''', (cedula, nombre, correo, contraseña, personalizada))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def actualizar_docente(cedula, nombre, correo, contraseña):
    """Actualiza un docente existente"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        personalizada = "personalizada" in contraseña.lower()
        cursor.execute('''
            UPDATE docentes 
            SET nombre_completo = %s, correo = %s, contraseña = %s, personalizada = %s, updated_at = CURRENT_TIMESTAMP
            WHERE cedula = %s
        ''', (nombre, correo, contraseña, personalizada, cedula))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def eliminar_docente(cedula):
    """Elimina un docente"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM docentes WHERE cedula = %s', (cedula,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def registrar_consulta_pg(correo, cedula, nombre):
    """Registra una consulta en PostgreSQL"""
    try:
        ahora = datetime.now()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consultas_pg (fecha, correo, cedula, nombre, mes, año, dia, hora)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (ahora, correo, cedula, nombre, ahora.month, ahora.year, ahora.day, ahora.hour))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error registrando consulta: {e}")
        return False

def obtener_resumen_mensual_pg(año, mes):
    """Obtiene resumen de consultas por mes desde PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT dia, COUNT(*) as total 
        FROM consultas_pg 
        WHERE año = %s AND mes = %s 
        GROUP BY dia 
        ORDER BY dia
    ''', (año, mes))
    consultas_por_dia = cursor.fetchall()
    
    cursor.execute('''
        SELECT DISTINCT cedula, nombre, correo, COUNT(*) as consultas
        FROM consultas_pg 
        WHERE año = %s AND mes = %s 
        GROUP BY cedula, nombre, correo
        ORDER BY consultas DESC
    ''', (año, mes))
    docentes_mes = cursor.fetchall()
    
    conn.close()
    return consultas_por_dia, docentes_mes

def buscar_por_cedula_detallado_pg(cedula):
    """Busca consultas de una cédula específica"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT fecha, correo, cedula, nombre, dia, mes, año, hora 
        FROM consultas_pg 
        WHERE cedula = %s 
        ORDER BY fecha DESC
    ''', (cedula,))
    resultados = cursor.fetchall()
    conn.close()
    
    detalles = []
    for r in resultados:
        detalles.append({
            "fecha_completa": r[0].strftime("%Y-%m-%d %H:%M:%S"),
            "correo": r[1],
            "cedula": r[2],
            "nombre": r[3],
            "dia": r[4],
            "mes": r[5],
            "año": r[6],
            "hora": r[7]
        })
    return detalles

def obtener_años_disponibles_pg():
    """Obtiene años con consultas registradas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT año FROM consultas_pg ORDER BY año DESC')
    años = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    año_actual = datetime.now().year
    años_set = set(años)
    for año in range(2026, año_actual + 2):
        if año not in años_set:
            años.append(año)
    
    return sorted(set(años), reverse=True)

def exportar_todas_consultas_pg():
    """Exporta todas las consultas a DataFrame"""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, fecha, correo, cedula, nombre, mes, año, dia, hora FROM consultas_pg ORDER BY fecha DESC", conn)
    conn.close()
    return df