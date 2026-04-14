import psycopg2
import os
import pandas as pd
from datetime import datetime

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL no configurada")
    return psycopg2.connect(database_url)

def init_db_pg():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS docentes (
            id SERIAL PRIMARY KEY,
            cedula VARCHAR(20) UNIQUE NOT NULL,
            nombre_completo VARCHAR(200) NOT NULL,
            correo VARCHAR(100) UNIQUE NOT NULL,
            contraseña VARCHAR(100) NOT NULL,
            personalizada BOOLEAN DEFAULT FALSE
        )
    ''')
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
    print("✅ Base de datos inicializada")

def migrar_excel_a_postgres(excel_path="docentes.xlsx"):
    if not os.path.exists(excel_path):
        return {"success": False, "error": f"Archivo {excel_path} no encontrado"}
    
    df = pd.read_excel(excel_path)
    conn = get_db_connection()
    cursor = conn.cursor()
    migrados = 0
    errores = 0
    
    for _, row in df.iterrows():
        try:
            cedula = str(row['CEDULA']).strip()
            if not cedula or cedula == 'nan':
                errores += 1
                continue
                
            nombre = str(row['NOMBRE COMPLETO']).strip()
            if not nombre or nombre == 'nan':
                errores += 1
                continue
                
            correo = str(row['CORREO INSTITUCIONAL']).strip().lower()
            if not correo or correo == 'nan' or '@' not in correo:
                errores += 1
                continue
                
            contraseña = str(row['CONTRASEÑA']).strip()
            if not contraseña or contraseña == 'nan':
                contraseña = "pendiente"
                
            personalizada = "personalizada" in contraseña.lower()
            
            cursor.execute('''
                INSERT INTO docentes (cedula, nombre_completo, correo, contraseña, personalizada)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (cedula) DO UPDATE SET
                    nombre_completo = EXCLUDED.nombre_completo,
                    correo = EXCLUDED.correo,
                    contraseña = EXCLUDED.contraseña,
                    personalizada = EXCLUDED.personalizada
            ''', (cedula, nombre, correo, contraseña, personalizada))
            migrados += 1
            
        except Exception as e:
            errores += 1
            continue
    
    conn.commit()
    conn.close()
    return {"success": True, "migrados": migrados, "errores": errores}

def obtener_todos_docentes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT cedula, nombre_completo, correo, contraseña, personalizada FROM docentes ORDER BY nombre_completo')
    resultados = cursor.fetchall()
    conn.close()
    return [{"cedula": r[0], "nombre": r[1], "correo": r[2], "contraseña": r[3], "personalizada": r[4]} for r in resultados]

def obtener_docente_por_cedula(cedula):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT cedula, nombre_completo, correo, contraseña, personalizada FROM docentes WHERE cedula = %s', (cedula,))
    r = cursor.fetchone()
    conn.close()
    if r:
        return {"cedula": r[0], "nombre": r[1], "correo": r[2], "contraseña": r[3], "personalizada": r[4]}
    return None

def registrar_consulta_pg(correo, cedula, nombre):
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

def obtener_resumen_mensual_pg(año, mes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT dia, COUNT(*) as total FROM consultas_pg WHERE año = %s AND mes = %s GROUP BY dia ORDER BY dia', (año, mes))
    consultas_por_dia = cursor.fetchall()
    cursor.execute('SELECT DISTINCT cedula, nombre, correo, COUNT(*) as consultas FROM consultas_pg WHERE año = %s AND mes = %s GROUP BY cedula, nombre, correo ORDER BY consultas DESC', (año, mes))
    docentes_mes = cursor.fetchall()
    conn.close()
    return consultas_por_dia, docentes_mes

def buscar_por_cedula_detallado_pg(cedula):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT fecha, correo, cedula, nombre, dia, mes, año, hora FROM consultas_pg WHERE cedula = %s ORDER BY fecha DESC', (cedula,))
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
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, fecha, correo, cedula, nombre, mes, año, dia, hora FROM consultas_pg ORDER BY fecha DESC", conn)
    conn.close()
    return df