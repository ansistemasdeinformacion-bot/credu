from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import sqlite3
import pytz
from database import (obtener_resumen_mensual, buscar_por_cedula, 
                     exportar_todas_consultas, obtener_años_disponibles)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ADMIN_USER = "admin"
ADMIN_PASSWORD = "credu2026"

def formatear_fecha_colombia(fecha_str):
    """Convierte fecha YYYY-MM-DD HH:MM:SS a DD/MM/YYYY HH:MM:SS"""
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        bogota_tz = pytz.timezone('America/Bogota')
        dt = bogota_tz.localize(dt)
        return dt.strftime("%d/%m/%Y %I:%M:%S %p")
    except:
        return fecha_str

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        if usuario == ADMIN_USER and password == ADMIN_PASSWORD:
            session['admin_logged'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            return render_template('admin_login.html', error="❌ Usuario o contraseña incorrectos")
    
    return render_template('admin_login.html', error=None)

@admin_bp.route('/logout')
def admin_logout():
    session.pop('admin_logged', None)
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/dashboard')
def dashboard():
    if not session.get('admin_logged'):
        return redirect(url_for('admin.admin_login'))
    
    bogota_tz = pytz.timezone('America/Bogota')
    ahora = datetime.now(bogota_tz)
    año_actual = ahora.year
    mes_actual = ahora.month
    años_disponibles = obtener_años_disponibles()
    
    consultas_por_dia, docentes_mes = obtener_resumen_mensual(año_actual, mes_actual)
    
    # Obtener consultas recientes con formato colombiano
    conn = sqlite3.connect('consultas.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT fecha, nombre, correo, cedula 
        FROM consultas 
        ORDER BY fecha DESC 
        LIMIT 50
    ''')
    consultas_recientes = cursor.fetchall()
    conn.close()
    
    consultas_lista = []
    for r in consultas_recientes:
        consultas_lista.append({
            "fecha": formatear_fecha_colombia(r[0]),
            "nombre": r[1],
            "correo": r[2],
            "cedula": r[3]
        })
    
    return render_template('admin_dashboard.html',
                         año_actual=año_actual,
                         mes_actual=mes_actual,
                         consultas_por_dia=consultas_por_dia,
                         docentes_mes=docentes_mes,
                         años_disponibles=años_disponibles,
                         consultas_recientes=consultas_lista)

@admin_bp.route('/cambiar_mes', methods=['POST'])
def cambiar_mes():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    data = request.get_json()
    año = data.get('año', datetime.now().year)
    mes = data.get('mes', datetime.now().month)
    
    consultas_por_dia, docentes_mes = obtener_resumen_mensual(año, mes)
    
    return jsonify({
        "success": True,
        "consultas_por_dia": consultas_por_dia,
        "docentes_mes": [[d[0], d[1], d[2], d[3]] for d in docentes_mes]
    })

@admin_bp.route('/buscar', methods=['POST'])
def buscar():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    data = request.get_json()
    cedula = data.get('cedula', '').strip()
    
    if not cedula:
        return jsonify({"success": False, "error": "Ingrese una cédula"})
    
    resultados = buscar_por_cedula(cedula)
    
    resultados_formateados = []
    for r in resultados:
        resultados_formateados.append({
            "fecha": formatear_fecha_colombia(r[0]),
            "correo": r[1],
            "cedula": r[2],
            "nombre": r[3],
            "dia": r[4],
            "mes": r[5],
            "año": r[6],
            "hora": r[7]
        })
    
    return jsonify({"success": True, "resultados": resultados_formateados})

@admin_bp.route('/exportar')
def exportar():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    df = exportar_todas_consultas()
    archivo_exportar = f"reporte_consultas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(archivo_exportar, index=False, encoding='utf-8')
    
    return jsonify({"success": True, "archivo": archivo_exportar})