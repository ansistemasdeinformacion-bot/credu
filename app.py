from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'credu_secret_key_2025'

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/credu')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ============================================
# RUTAS PRINCIPALES - CHATBOT
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_docente():
    if request.method == 'POST':
        correo = request.form.get('correo')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM docentes WHERE correo = %s", (correo,))
        docente = cur.fetchone()
        cur.close()
        conn.close()
        
        if docente:
            session['docente_correo'] = correo
            session['docente_nombre'] = docente['nombre_completo']
            session['docente_cedula'] = docente['cedula']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="❌ Correo no encontrado")
    
    return render_template('login.html')

@app.route('/consultar', methods=['POST'])
def consultar():
    if not session.get('docente_correo'):
        return jsonify({'success': False, 'mensaje': 'Sesión no iniciada'})
    
    data = request.get_json()
    cedula_ingresada = data.get('cedula', '').strip()
    cedula_real = session.get('docente_cedula')
    
    if cedula_ingresada != cedula_real:
        return jsonify({'success': False, 'mensaje': '❌ La cédula ingresada no coincide con nuestros registros.'})
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM docentes WHERE cedula = %s", (cedula_real,))
    docente = cur.fetchone()
    cur.close()
    conn.close()
    
    if docente:
        return jsonify({
            'success': True,
            'nombre': docente['nombre_completo'],
            'correo': docente['correo'],
            'cedula': docente['cedula'],
            'personalizada': docente.get('personalizada', False)
        })
    
    return jsonify({'success': False, 'mensaje': 'Error al obtener datos'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_docente'))

# ============================================
# PANEL DE ADMINISTRACIÓN
# ============================================

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'tecnounia2025':
            session['admin_logged'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error=True)
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/docentes')
def admin_docentes():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    return render_template('admin_docentes.html')

@app.route('/admin/graficas')
def admin_graficas():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    return render_template('admin_graficas.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged', None)
    return redirect(url_for('admin_login'))

# ============================================
# API PARA ADMINISTRADOR
# ============================================

@app.route('/admin/api/docentes')
def api_docentes():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT cedula, nombre_completo as nombre, correo, contrasena as contraseña FROM docentes ORDER BY nombre_completo")
    docentes = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify({'success': True, 'docentes': docentes})

@app.route('/admin/agregar_docente', methods=['POST'])
def agregar_docente():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO docentes (cedula, nombre_completo, correo, contrasena)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cedula) DO UPDATE SET
                nombre_completo = EXCLUDED.nombre_completo,
                correo = EXCLUDED.correo,
                contrasena = EXCLUDED.contrasena
        """, (data['cedula'], data['nombre'], data['correo'], data['contraseña']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/admin/actualizar_docente', methods=['POST'])
def actualizar_docente():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE docentes 
            SET nombre_completo = %s, correo = %s, contrasena = %s
            WHERE cedula = %s
        """, (data['nombre'], data['correo'], data['contraseña'], data['cedula']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/admin/eliminar_docente', methods=['POST'])
def eliminar_docente():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM docentes WHERE cedula = %s", (data['cedula'],))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/admin/migrar_excel', methods=['POST'])
def migrar_excel():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    
    try:
        import pandas as pd
        df = pd.read_excel('docentes.xlsx')
        conn = get_db_connection()
        cur = conn.cursor()
        migrados = 0
        errores = 0
        
        for _, row in df.iterrows():
            try:
                cedula = str(row['CEDULA']).strip()
                nombre = str(row['NOMBRE COMPLETO']).strip()
                correo = str(row['CORREO INSTITUCIONAL']).strip().lower()
                contrasena = str(row['CONTRASEÑA']).strip()
                
                cur.execute("""
                    INSERT INTO docentes (cedula, nombre_completo, correo, contrasena)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (cedula) DO UPDATE SET
                        nombre_completo = EXCLUDED.nombre_completo,
                        correo = EXCLUDED.correo,
                        contrasena = EXCLUDED.contrasena
                """, (cedula, nombre, correo, contrasena))
                migrados += 1
            except:
                errores += 1
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'migrados': migrados, 'errores': errores})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/datos_grafica')
def datos_grafica():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    valores = [0] * 12
    
    return jsonify({
        'success': True,
        'meses': meses,
        'valores': valores,
        'total_consultas': 0,
        'promedio_mensual': 0,
        'mejor_mes': '',
        'peor_mes': ''
    })

@app.route('/admin/cambiar_mes', methods=['POST'])
def cambiar_mes():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    return jsonify({'success': True, 'consultas_por_dia': [], 'docentes_mes': []})

@app.route('/admin/buscar', methods=['POST'])
def buscar():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    return jsonify({'success': True, 'resultados': []})

@app.route('/admin/exportar', methods=['POST'])
def exportar():
    if not session.get('admin_logged'):
        return jsonify({'success': False})
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)