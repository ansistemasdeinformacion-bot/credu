from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from database_pg import (
    init_db_pg, obtener_todos_docentes, agregar_docente, actualizar_docente,
    eliminar_docente, migrar_excel_a_postgres, obtener_resumen_mensual_pg,
    buscar_por_cedula_detallado_pg, exportar_todas_consultas_pg, obtener_años_disponibles_pg
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Inicializar base de datos
init_db_pg()

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
    años_disponibles = obtener_años_disponibles_pg()
    docentes = obtener_todos_docentes()
    
    consultas_por_dia, docentes_mes = obtener_resumen_mensual_pg(año_actual, mes_actual)
    
    return render_template('admin_dashboard.html',
                         año_actual=año_actual,
                         mes_actual=mes_actual,
                         consultas_por_dia=consultas_por_dia,
                         docentes_mes=docentes_mes,
                         años_disponibles=años_disponibles,
                         docentes=docentes)

@admin_bp.route('/cambiar_mes', methods=['POST'])
def cambiar_mes():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    data = request.get_json()
    año = data.get('año', datetime.now().year)
    mes = data.get('mes', datetime.now().month)
    
    consultas_por_dia, docentes_mes = obtener_resumen_mensual_pg(año, mes)
    
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
    
    resultados = buscar_por_cedula_detallado_pg(cedula)
    
    return jsonify({
        "success": True,
        "resultados": resultados
    })

@admin_bp.route('/exportar')
def exportar():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    df = exportar_todas_consultas_pg()
    archivo_exportar = f"reporte_consultas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(archivo_exportar, index=False, encoding='utf-8')
    
    return jsonify({"success": True, "archivo": archivo_exportar})

@admin_bp.route('/migrar_excel', methods=['POST'])
def migrar_excel():
    if not session.get('admin_logged'):
        return jsonify({"success": False, "error": "No autorizado"})
    
    resultado = migrar_excel_a_postgres()
    return jsonify(resultado)

@admin_bp.route('/docentes')
def listar_docentes():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    docentes = obtener_todos_docentes()
    return jsonify({"success": True, "docentes": docentes})

@admin_bp.route('/agregar_docente', methods=['POST'])
def agregar_docente_route():
    if not session.get('admin_logged'):
        return jsonify({"success": False, "error": "No autorizado"})
    
    data = request.get_json()
    resultado = agregar_docente(
        cedula=data.get('cedula'),
        nombre=data.get('nombre'),
        correo=data.get('correo'),
        contraseña=data.get('contraseña')
    )
    return jsonify(resultado)

@admin_bp.route('/actualizar_docente', methods=['POST'])
def actualizar_docente_route():
    if not session.get('admin_logged'):
        return jsonify({"success": False, "error": "No autorizado"})
    
    data = request.get_json()
    resultado = actualizar_docente(
        cedula=data.get('cedula'),
        nombre=data.get('nombre'),
        correo=data.get('correo'),
        contraseña=data.get('contraseña')
    )
    return jsonify(resultado)

@admin_bp.route('/eliminar_docente', methods=['POST'])
def eliminar_docente_route():
    if not session.get('admin_logged'):
        return jsonify({"success": False, "error": "No autorizado"})
    
    data = request.get_json()
    resultado = eliminar_docente(data.get('cedula'))
    return jsonify(resultado)