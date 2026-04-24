from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'credu_secret_key_2025')

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/credu')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def inicializar_tabla():
    """Crea la tabla docentes si no existe"""
    conn = get_db_connection()
    cur = conn.cursor()
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
    cur.close()
    conn.close()
    print("✅ Tabla 'docentes' verificada/creada correctamente")

inicializar_tabla()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def docente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('docente_logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route('/')
def index():
    return jsonify({'mensaje': 'API CREDU funcionando', 'status': 'ok'})

# ============================================
# LOGIN PARA DOCENTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        contrasena = request.form.get('contrasena')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM docentes WHERE cedula = %s AND contrasena = %s", (cedula, contrasena))
        docente = cur.fetchone()
        cur.close()
        conn.close()
        
        if docente:
            session['docente_logged_in'] = True
            session['docente_cedula'] = cedula
            session['docente_nombre'] = docente['nombre_completo']
            return redirect(url_for('dashboard_docente'))
        else:
            return render_template('login.html', error=True)
    
    return render_template('login.html')

@app.route('/dashboard')
@docente_required
def dashboard_docente():
    return render_template('dashboard.html', nombre=session.get('docente_nombre'))

# ============================================
# PANEL ADMINISTRADOR
# ============================================

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
@admin_required
def admin_dashboard():
    return render_template('admin.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.pop('docente_logged_in', None)
    session.pop('docente_cedula', None)
    session.pop('docente_nombre', None)
    return redirect(url_for('login_page'))

# ============================================
# API - CRUD DOCENTES (para admin)
# ============================================

@app.route('/api/docentes', methods=['GET'])
@admin_required
def get_docentes():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
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
        return jsonify(docentes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/docentes', methods=['POST'])
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def migrar_excel():
    if 'excel' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['excel']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    try:
        df = pd.read_excel(file)
        df.columns = df.columns.str.lower().str.strip()
        
        columnas_necesarias = ['cedula', 'contrasena', 'nombre_completo', 'correo']
        for col in columnas_necesarias:
            if col not in df.columns:
                return jsonify({'error': f'Falta la columna: {col}'}), 400
        
        migrados = 0
        errores = 0
        
        conn = get_db_connection()
        cur = conn.cursor()
        
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