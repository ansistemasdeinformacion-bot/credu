from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Credenciales del administrador (puedes cambiarlas)
ADMIN_USER = "admin"
ADMIN_PASSWORD = "credu2026"

def cargar_consultas():
    """Carga el archivo CSV de consultas"""
    archivo = "consultas.csv"
    if os.path.exists(archivo):
        return pd.read_csv(archivo)
    return pd.DataFrame(columns=["FECHA", "CORREO", "CEDULA", "NOMBRE"])

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Login del administrador"""
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
    """Cerrar sesión del administrador"""
    session.pop('admin_logged', None)
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/dashboard')
def dashboard():
    """Panel principal del administrador"""
    if not session.get('admin_logged'):
        return redirect(url_for('admin.admin_login'))
    
    df = cargar_consultas()
    
    # Estadísticas
    total_consultas = len(df)
    docentes_unicos = df['CORREO'].nunique() if not df.empty else 0
    consultas_hoy = len(df[df['FECHA'].str.startswith(datetime.now().strftime("%Y-%m-%d"))]) if not df.empty else 0
    
    # Últimas 10 consultas
    ultimas_consultas = df.tail(10).to_dict('records') if not df.empty else []
    
    # Consultas por día (últimos 7 días)
    if not df.empty:
        df['FECHA_CORTA'] = pd.to_datetime(df['FECHA']).dt.date
        consultas_por_dia = df.groupby('FECHA_CORTA').size().reset_index(name='TOTAL')
        consultas_por_dia = consultas_por_dia.tail(7).to_dict('records')
    else:
        consultas_por_dia = []
    
    return render_template('admin_dashboard.html',
                         total_consultas=total_consultas,
                         docentes_unicos=docentes_unicos,
                         consultas_hoy=consultas_hoy,
                         ultimas_consultas=ultimas_consultas,
                         consultas_por_dia=consultas_por_dia)

@admin_bp.route('/exportar')
def exportar():
    """Exportar consultas a CSV"""
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    df = cargar_consultas()
    archivo_exportar = f"reporte_consultas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(archivo_exportar, index=False, encoding='utf-8')
    
    return jsonify({"success": True, "archivo": archivo_exportar})