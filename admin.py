from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import os
from datetime import datetime
from database import init_db, obtener_resumen_mensual, buscar_por_cedula, exportar_todas_consultas

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Inicializar base de datos
init_db()

# Credenciales del administrador
ADMIN_USER = "admin"
ADMIN_PASSWORD = "credu2026"

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
    
    año_actual = datetime.now().year
    mes_actual = datetime.now().month
    
    # Obtener resumen del mes actual
    consultas_por_dia, docentes_mes = obtener_resumen_mensual(año_actual, mes_actual)
    
    return render_template('admin_dashboard.html',
                         año_actual=año_actual,
                         mes_actual=mes_actual,
                         consultas_por_dia=consultas_por_dia,
                         docentes_mes=docentes_mes)

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
    
    return jsonify({
        "success": True,
        "resultados": [[r[0], r[1], r[2], r[3]] for r in resultados]
    })

@admin_bp.route('/exportar')
def exportar():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    df = exportar_todas_consultas()
    archivo_exportar = f"reporte_consultas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(archivo_exportar, index=False, encoding='utf-8')
    
    return jsonify({"success": True, "archivo": archivo_exportar})