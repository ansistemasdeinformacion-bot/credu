import sqlite3
from datetime import datetime
import pytz
import pandas as pd

DB_NAME = "consultas.db"

def init_db():
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
    print("✅ Base de datos SQLite inicializada")

def registrar_consulta_db(correo, cedula, nombre):
    try:
        bogota_tz = pytz.timezone('America/Bogota')
        ahora = datetime.now(bogota_tz)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consultas (fecha, correo, cedula, nombre, mes, año, dia, hora)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ahora.strftime("%Y-%m-%d %H:%M:%S"), correo, cedula, nombre, ahora.month, ahora.year, ahora.day, ahora.hour))
        conn.commit()
        conn.close()
        print(f"✅ Consulta registrada: {correo} - {ahora.strftime('%d/%m/%Y %I:%M:%S %p')}")
        return True
    except Exception as e:
        print(f"❌ Error registrando consulta: {e}")
        return False

def obtener_resumen_mensual(año, mes):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT dia, COUNT(*) as total FROM consultas WHERE año = ? AND mes = ? GROUP BY dia ORDER BY dia', (año, mes))
    consultas_por_dia = cursor.fetchall()
    cursor.execute('SELECT DISTINCT cedula, nombre, correo, COUNT(*) as consultas FROM consultas WHERE año = ? AND mes = ? GROUP BY cedula ORDER BY consultas DESC', (año, mes))
    docentes_mes = cursor.fetchall()
    conn.close()
    return consultas_por_dia, docentes_mes

def buscar_por_cedula(cedula):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT fecha, correo, cedula, nombre, dia, mes, año, hora FROM consultas WHERE cedula = ? ORDER BY fecha DESC', (cedula,))
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def obtener_años_disponibles():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT año FROM consultas ORDER BY año DESC')
    años = [row[0] for row in cursor.fetchall()]
    conn.close()
    año_actual = datetime.now(pytz.timezone('America/Bogota')).year
    años_set = set(años)
    for año in range(2026, año_actual + 2):
        if año not in años_set:
            años.append(año)
    return sorted(set(años), reverse=True)

def exportar_todas_consultas():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, fecha, correo, cedula, nombre, mes, año, dia, hora FROM consultas ORDER BY fecha DESC", conn)
    conn.close()
    # Formatear fecha para exportación
    if not df.empty:
        df['fecha_formateada'] = pd.to_datetime(df['fecha']).dt.strftime('%d/%m/%Y %I:%M:%S %p')
    return df