import sqlite3
from datetime import datetime
import pandas as pd

DB_NAME = "consultas.db"

def init_db():
    """Crea la tabla de consultas si no existe"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            correo TEXT NOT NULL,
            cedula TEXT NOT NULL,
            nombre TEXT NOT NULL,
            mes INTEGER,
            año INTEGER,
            dia INTEGER,
            hora INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada")

def registrar_consulta_db(correo, cedula, nombre):
    """Registra una consulta en la base de datos"""
    try:
        ahora = datetime.now()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consultas (fecha, correo, cedula, nombre, mes, año, dia, hora)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ahora.strftime("%Y-%m-%d %H:%M:%S"), correo, cedula, nombre, ahora.month, ahora.year, ahora.day, ahora.hour))
        conn.commit()
        conn.close()
        print(f"✅ Consulta registrada: {correo}")
        return True
    except Exception as e:
        print(f"❌ Error registrando consulta: {e}")
        return False

def obtener_resumen_mensual(año, mes):
    """Obtiene resumen de consultas por mes"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Consultas por día del mes
    cursor.execute('''
        SELECT dia, COUNT(*) as total 
        FROM consultas 
        WHERE año = ? AND mes = ? 
        GROUP BY dia 
        ORDER BY dia
    ''', (año, mes))
    consultas_por_dia = cursor.fetchall()
    
    # Docentes que consultaron en el mes
    cursor.execute('''
        SELECT DISTINCT cedula, nombre, correo, COUNT(*) as consultas
        FROM consultas 
        WHERE año = ? AND mes = ? 
        GROUP BY cedula
        ORDER BY consultas DESC
    ''', (año, mes))
    docentes_mes = cursor.fetchall()
    
    conn.close()
    return consultas_por_dia, docentes_mes

def buscar_por_cedula_detallado(cedula):
    """Busca todas las consultas de una cédula específica con detalles"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT fecha, correo, cedula, nombre, dia, mes, año, hora 
        FROM consultas 
        WHERE cedula = ? 
        ORDER BY fecha DESC
    ''', (cedula,))
    resultados = cursor.fetchall()
    conn.close()
    
    # Formatear resultados con fecha legible
    detalles = []
    for r in resultados:
        detalles.append({
            "fecha_completa": r[0],
            "correo": r[1],
            "cedula": r[2],
            "nombre": r[3],
            "dia": r[4],
            "mes": r[5],
            "año": r[6],
            "hora": r[7]
        })
    return detalles

def obtener_años_disponibles():
    """Obtiene lista de años con consultas registradas"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT año FROM consultas ORDER BY año DESC')
    años = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Agregar años desde 2026 hasta el actual si no existen
    año_actual = datetime.now().year
    años_set = set(años)
    for año in range(2026, año_actual + 2):  # +2 para incluir año siguiente
        if año not in años_set:
            años.append(año)
    
    return sorted(set(años), reverse=True)

def exportar_todas_consultas():
    """Exporta todas las consultas a DataFrame"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, fecha, correo, cedula, nombre, mes, año, dia, hora FROM consultas ORDER BY fecha DESC", conn)
    conn.close()
    return df