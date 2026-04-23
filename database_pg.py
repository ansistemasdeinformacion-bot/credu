import os
import psycopg2
import pandas as pd

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL no configurada")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()
    print("✅ Tabla docentes verificada")

def obtener_todos_docentes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT cedula, nombre_completo, correo, contraseña, personalizada FROM docentes ORDER BY nombre_completo')
        resultados = cursor.fetchall()
        conn.close()
        return [{"cedula": r[0], "nombre": r[1], "correo": r[2], "contraseña": r[3], "personalizada": r[4]} for r in resultados]
    except Exception as e:
        print(f"Error: {e}")
        return []

def migrar_excel_a_postgres(excel_path="docentes.xlsx"):
    try:
        init_db()
        
        print(f"🔍 Leyendo archivo: {excel_path}")
        df = pd.read_excel(excel_path)
        print(f"📊 Filas encontradas: {len(df)}")
        print(f"📋 Columnas: {list(df.columns)}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        migrados = 0
        errores = 0
        
        for idx, row in df.iterrows():
            try:
                # Usar los nombres exactos de las columnas
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
                
            except KeyError as e:
                errores += 1
                print(f"❌ Error en fila {idx}: Columna no encontrada - {e}")
                continue
            except Exception as e:
                errores += 1
                print(f"❌ Error en fila {idx}: {e}")
                continue
        
        conn.commit()
        conn.close()
        print(f"✅ Migrados: {migrados}, ❌ Errores: {errores}")
        return {"success": True, "migrados": migrados, "errores": errores}
    except Exception as e:
        print(f"❌ Error general: {e}")
        return {"success": False, "error": str(e)}

def agregar_docente(cedula, nombre, correo, contraseña):
    try:
        init_db()
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM docentes WHERE cedula = %s', (cedula,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def obtener_docente_por_cedula(cedula):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT cedula, nombre_completo, correo, contraseña, personalizada FROM docentes WHERE cedula = %s', (cedula,))
        r = cursor.fetchone()
        conn.close()
        if r:
            return {"cedula": r[0], "nombre": r[1], "correo": r[2], "contraseña": r[3], "personalizada": r[4]}
        return None
    except:
        return None