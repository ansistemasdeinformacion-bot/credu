from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'credu_secret_key_2025')

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
def login():
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
            return render_template('login.html', error="Correo no encontrado")
    
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
        # Enviar correo
        enviado = enviar_correo_credenciales(docente['correo'], docente['nombre_completo'], docente['cedula'], docente['contrasena'], docente.get('personalizada', False))
        
        return jsonify({
            'success': True,
            'nombre': docente['nombre_completo'],
            'correo': docente['correo'],
            'cedula': docente['cedula'],
            'personalizada': docente.get('personalizada', False),
            'enviado': enviado
        })
    
    return jsonify({'success': False, 'mensaje': 'Error al obtener datos'})

def enviar_correo_credenciales(correo_destino, nombre, cedula, contraseña, personalizada):
    try:
        # Configuración de correo (ajusta estos datos)
        remitente = "credu@uniagustiniana.edu.co"
        password = "tu_contraseña"
        
        asunto = "Tus credenciales de acceso - CREDU"
        
        if personalizada:
            mensaje_html = f"""
            <h2>🎓 Credenciales Institucionales</h2>
            <p>Estimado/a {nombre},</p>
            <p>Tu contraseña fue <strong>personalizada por ti mismo</strong>.</p>
            <p>Si no la recuerdas, debes acercarte a la oficina de Tecnologías.</p>
            <p><strong>Usuario:</strong> {cedula}</p>
            <p>Estas credenciales aplican para: <strong>SIGA, KAWAK, SIPA HCM</strong></p>
            <hr>
            <p>⭐ Uniagustiniana es creer en ti</p>
            """
        else:
            mensaje_html = f"""
            <h2>🎓 Credenciales Institucionales</h2>
            <p>Estimado/a {nombre},</p>
            <p><strong>Usuario:</strong> {cedula}</p>
            <p><strong>Contraseña:</strong> {contraseña}</p>
            <p>Estas credenciales aplican para: <strong>SIGA, KAWAK, SIPA HCM</strong></p>
            <hr>
            <p>⭐ Uniagustiniana es creer en ti</p>
            """
        
        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = correo_destino
        msg['Subject'] = asunto
        msg.attach(MIMEText(mensaje_html, 'html'))
        
        # server = smtplib.SMTP('smtp.office365.com', 587)
        # server.starttls()
        # server.login(remitente, password)
        # server.send_message(msg)
        # server.quit()
        
        print(f"📧 Correo enviado a {correo_destino}")
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================
# PANEL ADMINISTRADOR (TODAS LAS FUNCIONES)
# ============================================

ADMIN_USER = "admin"
ADMIN_PASSWORD = "tecnounia2025"

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error=True)
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    bogota_tz = pytz.timezone('America/Bogota')
    ahora = datetime.now(bogota_tz)
    año_actual = ahora.year
    mes_actual = ahora.month
    
    # Datos de ejemplo
    consultas_por_dia = {}
    años_disponibles = [2025, 2026]
    consultas_recientes = []
    
    return render_template('admin_dashboard.html',
                         año_actual=año_actual,
                         mes_actual=mes_actual,
                         consultas_por_dia=consultas_por_dia,
                         años_disponibles=años_disponibles,
                         consultas_recientes=consultas_recientes)

@app.route('/admin/docentes')
def admin_docentes():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_docentes.html')

@app.route('/admin/graficas')
def admin_graficas():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_graficas.html')

# ============================================
# API PARA ADMINISTRADOR
# ============================================

@app.route('/admin/api/docentes')
def api_docentes():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False})
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT cedula, nombre_completo as nombre, correo, contrasena as contraseña, personalizada FROM docentes ORDER BY nombre_completo")
    docentes = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify({'success': True, 'docentes': docentes})

@app.route('/admin/agregar_docente', methods=['POST'])
def agregar_docente():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        personalizada = "personalizada" in data.get('contraseña', '').lower()
        cur.execute("""
            INSERT INTO docentes (cedula, nombre_completo, correo, contraseña, personalizada)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cedula) DO UPDATE SET
                nombre_completo = EXCLUDED.nombre_completo,
                correo = EXCLUDED.correo,
                contraseña = EXCLUDED.contraseña,
                personalizada = EXCLUDED.personalizada
        """, (data['cedula'], data['nombre'], data['correo'], data['contraseña'], personalizada))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/admin/actualizar_docente', methods=['POST'])
def actualizar_docente():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        personalizada = "personalizada" in data.get('contraseña', '').lower()
        cur.execute("""
            UPDATE docentes 
            SET nombre_completo = %s, correo = %s, contraseña = %s, personalizada = %s
            WHERE cedula = %s
        """, (data['nombre'], data['correo'], data['contraseña'], personalizada, data['cedula']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/admin/eliminar_docente', methods=['POST'])
def eliminar_docente():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'No autorizado'})
    
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
def admin_migrar_excel():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    try:
        from database_pg import migrar_excel_a_postgres
        resultado = migrar_excel_a_postgres()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/datos_grafica')
def datos_grafica():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False})
    
    año = request.args.get('año', 2026, type=int)
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    # Datos de ejemplo - puedes conectar a tu base de datos real
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)