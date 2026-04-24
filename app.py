from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'credu_secret_key_2025')

# Configuración de la base de datos
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/credu')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route('/')
def index():
    return jsonify({'mensaje': 'API CREDU funcionando', 'status': 'ok'})

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'tecnounia2025':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error=True)
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# ============================================
# API - CRUD DOCENTES
# ============================================

@app.route('/api/docentes', methods=['GET'])
@login_required
def get_docentes():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if search:
        cur.execute("""
            SELECT cedula, nombre_completo, correo, contrasena 
            FROM docentes 
            WHERE cedula::TEXT ILIKE %s OR nombre_completo ILIKE %s OR correo ILIKE %s
            ORDER BY nombre_completo
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cur.execute("SELECT cedula, nombre_completo, correo, contrasena FROM docentes ORDER BY nombre_completo")
    
    docentes = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(docentes)

@app.route('/api/docentes', methods=['POST'])
@login_required
def add_docente():
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
@login_required
def update_docente(cedula):
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
@login_required
def delete_docente(cedula):
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

# ============================================
# API - MIGRAR EXCEL
# ============================================

@app.route('/api/migrar-excel', methods=['POST'])
@login_required
def migrar_excel():
    if 'excel' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['excel']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    try:
        df = pd.read_excel(file)
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.lower().str.strip()
        
        columnas_necesarias = ['cedula', 'contrasena', 'nombre_completo', 'correo']
        for col in columnas_necesarias:
            if col not in df.columns:
                return jsonify({'error': f'Falta la columna: {col}'}), 400
        
        migrados = 0
        errores = 0
        
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
                
                if not cedula or not contrasena or not nombre_completo or not correo:
                    errores += 1
                    continue
                
                cur.execute("""
                    INSERT INTO docentes (cedula, nombre_completo, correo, contrasena)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (cedula) DO UPDATE SET
                        nombre_completo = EXCLUDED.nombre_completo,
                        correo = EXCLUDED.correo,
                        contrasena = EXCLUDED.contrasena
                """, (cedula, nombre_completo, correo, contrasena))
                
                migrados += 1
                
            except Exception:
                errores += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'migrados': migrados,
            'errores': errores,
            'mensaje': f'{migrados} docentes migrados, {errores} errores'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)