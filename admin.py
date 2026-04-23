from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, send_file
from datetime import datetime
import sqlite3
import pytz
import pandas as pd
from io import BytesIO
from database import (obtener_resumen_mensual, buscar_por_cedula, 
                     exportar_todas_consultas, obtener_años_disponibles)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ADMIN_USER = "admin"
ADMIN_PASSWORD = "credu2026"

def formatear_fecha_colombia(fecha_str):
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
            session.permanent = True
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
    
    consultas_dict = {dia: total for dia, total in consultas_por_dia}
    
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
                         consultas_por_dia=consultas_dict,
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
        "consultas_por_dia": [[d[0], d[1]] for d in consultas_por_dia],
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

@admin_bp.route('/exportar', methods=['POST'])
def exportar():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    try:
        data = request.get_json()
        año = data.get('año', datetime.now().year)
        mes = data.get('mes', datetime.now().month)
        
        conn = sqlite3.connect('consultas.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fecha, correo, cedula, nombre, hora 
            FROM consultas 
            WHERE año = ? AND mes = ? 
            ORDER BY fecha DESC
        ''', (año, mes))
        resultados = cursor.fetchall()
        conn.close()
        
        datos = []
        for r in resultados:
            fecha_str = r[0]
            fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
            hora_formateada = fecha_obj.strftime("%I:%M:%S %p")
            datos.append({
                "Fecha": fecha_formateada,
                "Hora": hora_formateada,
                "Nombre del Docente": r[3],
                "Correo del Docente": r[1],
                "Cédula del Docente": r[2]
            })
        
        df = pd.DataFrame(datos)
        
        if df.empty:
            df = pd.DataFrame(columns=["Fecha", "Hora", "Nombre del Docente", "Correo del Docente", "Cédula del Docente"])
        
        meses = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
                 7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
        
        nombre_mes = meses.get(mes, 'Mes')
        nombre_archivo = f"reporte_consultas_{nombre_mes}_{año}.xlsx"
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'Consultas {nombre_mes} {año}', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"Error exportando: {e}")
        return jsonify({"success": False, "error": str(e)})

# ============================================
# GRÁFICAS ESTADÍSTICAS
# ============================================

@admin_bp.route('/graficas')
def graficas():
    if not session.get('admin_logged'):
        return redirect(url_for('admin.admin_login'))
    return render_template('admin_graficas.html')

@admin_bp.route('/datos_grafica')
def datos_grafica():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    año = request.args.get('año', type=int)
    if not año:
        año = datetime.now().year
    
    conn = sqlite3.connect('consultas.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT mes, COUNT(*) as total 
        FROM consultas 
        WHERE año = ? 
        GROUP BY mes 
        ORDER BY mes
    ''', (año,))
    resultados = cursor.fetchall()
    conn.close()
    
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    valores = [0] * 12
    for mes, total in resultados:
        valores[mes - 1] = total
    
    total_consultas = sum(valores)
    promedio_mensual = round(total_consultas / 12, 1) if total_consultas > 0 else 0
    
    mejor_mes = ""
    peor_mes = ""
    if total_consultas > 0:
        max_valor = max(valores)
        min_valor = min([v for v in valores if v > 0]) if any(v > 0 for v in valores) else 0
        if max_valor > 0:
            mejor_mes = meses[valores.index(max_valor)]
        if min_valor > 0:
            peor_mes = meses[valores.index(min_valor)]
    
    return jsonify({
        "success": True,
        "meses": meses,
        "valores": valores,
        "total_consultas": total_consultas,
        "promedio_mensual": promedio_mensual,
        "mejor_mes": mejor_mes,
        "peor_mes": peor_mes
    })

# ============================================
# GESTIÓN DE DOCENTES
# ============================================

@admin_bp.route('/docentes')
def docentes_page():
    if not session.get('admin_logged'):
        return redirect(url_for('admin.admin_login'))
    return render_template('admin_docentes.html')

@admin_bp.route('/api/docentes')
def api_docentes():
    if not session.get('admin_logged'):
        return jsonify({"success": False})
    
    from database_pg import obtener_todos_docentes
    docentes = obtener_todos_docentes()
    return jsonify({"success": True, "docentes": docentes})

@admin_bp.route('/agregar_docente', methods=['POST'])
def agregar_docente_route():
    if not session.get('admin_logged'):
        return jsonify({"success": False, "error": "No autorizado"})
    
    from database_pg import agregar_docente
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
    
    from database_pg import actualizar_docente
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
    
    from database_pg import eliminar_docente
    data = request.get_json()
    resultado = eliminar_docente(data.get('cedula'))
    return jsonify(resultado)

@admin_bp.route('/migrar_excel', methods=['POST'])
def migrar_excel():
    if not session.get('admin_logged'):
        return jsonify({"success": False, "error": "No autorizado"})
    
    try:
        from database_pg import migrar_excel_a_postgres
        import os
        
        # Obtener información del directorio para debug
        cwd = os.getcwd()
        archivos = os.listdir('.')
        excel_existe = os.path.exists('docentes.xlsx')
        
        resultado = migrar_excel_a_postgres()
        
        # Agregar debug a la respuesta
        resultado["debug"] = {
            "cwd": cwd,
            "archivos": archivos,
            "excel_existe": excel_existe
        }
        
        return jsonify(resultado)
    except Exception as e:
        import traceback
        return jsonify({
            "success": False, 
            "error": str(e), 
            "traceback": traceback.format_exc()
        })