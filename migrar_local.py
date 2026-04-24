import psycopg2
import pandas as pd

DATABASE_URL = "postgresql://postgres:TXgQLFmGGuRULLfysGALdYaaUUKthKco@shinkansen.proxy.rlwy.net:57517/railway"

def get_db_connection():
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
    print("✅ Tabla docentes creada/verificada")

def migrar_excel():
    init_db()
    df = pd.read_excel("docentes.xlsx")
    print(f"📊 Filas en Excel: {len(df)}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    migrados = 0
    errores = 0
    
    for idx, row in df.iterrows():
        try:
            cedula = str(row['CEDULA']).strip()
            nombre = str(row['NOMBRE COMPLETO']).strip()
            correo = str(row['CORREO INSTITUCIONAL']).strip().lower()
            contraseña = str(row['CONTRASEÑA']).strip()
            personalizada = "personalizada" in contraseña.lower()
            
            cursor.execute('''
                INSERT INTO docentes (cedula, nombre_completo, correo, contraseña, personalizada)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (cedula) DO NOTHING
            ''', (cedula, nombre, correo, contraseña, personalizada))
            migrados += 1
            
            if migrados % 100 == 0:
                print(f"Procesados: {migrados}")
                
        except Exception as e:
            errores += 1
            print(f"❌ Error en fila {idx}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ Migrados: {migrados}, ❌ Errores: {errores}")

if __name__ == "__main__":
    migrar_excel()