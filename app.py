from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import psycopg2
import os
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Configuración de subida de archivos
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de la base de datos (Railway PostgreSQL)
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://usuario:contraseña@localhost:5432/credu')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# PÁGINA DE LOGIN DEL ADMINISTRADOR
# ============================================
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Credenciales (cámbialas por las que quieras)
        if username == 'admin' and password == 'tecnounia2025':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error=True)
    
    return render_template('admin_login.html')

# ============================================
# PANEL DE ADMINISTRACIÓN (DASHBOARD)
# ============================================
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obtener todos los docentes
    cur.execute("SELECT cedula, nombre_completo, correo, contrasena FROM docentes ORDER BY nombre_completo")
    docentes = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin.html', docentes=docentes)

# ============================================
# API: MIGRAR EXCEL A BASE DE DATOS
# ============================================
@app.route('/api/migrar-excel', methods=['POST'])
def migrar_excel():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    if 'excel' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['excel']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Formato no permitido. Use .xlsx o .xls'}), 400
    
    try:
        # Leer el Excel
        df = pd.read_excel(file)
        
        # Verificar que tenga las columnas necesarias
        columnas_requeridas = ['cedula', 'contrasena', 'nombre_completo', 'correo']
        columnas_excel = [col.lower() for col in df.columns]
        
        for col in columnas_requeridas:
            if col not in columnas_excel:
                return jsonify({'error': f'Falta la columna: {col}'}), 400
        
        # Renombrar columnas a minúsculas
        df.columns = [col.lower() for col in df.columns]
        
        migrados = 0
        errores = 0
        errores_lista = []
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Crear tabla si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS docentes (
                cedula VARCHAR(20) PRIMARY KEY,
                nombre_completo VARCHAR(200) NOT NULL,
                correo VARCHAR(100) NOT NULL UNIQUE,
                contrasena VARCHAR(100) NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        for _, row in df.iterrows():
            try:
                cedula = str(row['cedula']).strip()
                contrasena = str(row['contrasena']).strip()
                nombre_completo = str(row['nombre_completo']).strip()
                correo = str(row['correo']).strip()
                
                # Validar datos
                if not cedula or not contrasena or not nombre_completo or not correo:
                    errores += 1
                    errores_lista.append(f"Fila con datos vacíos - Cédula: {cedula}")
                    continue
                
                # Insertar o actualizar
                cur.execute("""
                    INSERT INTO docentes (cedula, nombre_completo, correo, contrasena)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (cedula) DO UPDATE SET
                        nombre_completo = EXCLUDED.nombre_completo,
                        correo = EXCLUDED.correo,
                        contrasena = EXCLUDED.contrasena
                """, (cedula, nombre_completo, correo, contrasena))
                
                migrados += 1
                
            except Exception as e:
                errores += 1
                errores_lista.append(f"Error en fila {_}: {str(e)}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'migrados': migrados,
            'errores': errores,
            'mensaje': f'Migración completada',
            'detalles': errores_lista[:10]  # primeros 10 errores
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 500

# ============================================
# API: CRUD DE DOCENTES
# ============================================
@app.route('/api/docentes', methods=['GET'])
def get_docentes():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if search:
        cur.execute("""
            SELECT cedula, nombre_completo, correo, contrasena 
            FROM docentes 
            WHERE cedula ILIKE %s OR nombre_completo ILIKE %s OR correo ILIKE %s
            ORDER BY nombre_completo
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cur.execute("SELECT cedula, nombre_completo, correo, contrasena FROM docentes ORDER BY nombre_completo")
    
    docentes = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify([{
        'cedula': d[0],
        'nombre_completo': d[1],
        'correo': d[2],
        'contrasena': d[3]
    } for d in docentes])

@app.route('/api/docentes', methods=['POST'])
def add_docente():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO docentes (cedula, nombre_completo, correo, contrasena)
            VALUES (%s, %s, %s, %s)
        """, (data['cedula'], data['nombre_completo'], data['correo'], data['contrasena']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cur.close()
        conn.close()

@app.route('/api/docentes/<cedula>', methods=['PUT'])
def update_docente(cedula):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE docentes 
            SET nombre_completo = %s, correo = %s, contrasena = %s
            WHERE cedula = %s
        """, (data['nombre_completo'], data['correo'], data['contrasena'], cedula))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cur.close()
        conn.close()

@app.route('/api/docentes/<cedula>', methods=['DELETE'])
def delete_docente(cedula):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM docentes WHERE cedula = %s", (cedula,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cur.close()
        conn.close()

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)