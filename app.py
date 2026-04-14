from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import os
from database_pg import (
    init_db_pg, obtener_docente_por_cedula, registrar_consulta_pg,
    obtener_todos_docentes, agregar_docente, actualizar_docente, eliminar_docente,
    migrar_excel_a_postgres
)

app = Flask(__name__)
app.secret_key = "clave_secreta_credu_2026"

# Inicializar base de datos PostgreSQL
init_db_pg()

# Verificar si hay docentes en la BD, si no, migrar desde Excel
def verificar_y_migrar():
    docentes = obtener_todos_docentes()
    if len(docentes) == 0:
        print("📦 No hay docentes en PostgreSQL. Migrando desde Excel...")
        resultado = migrar_excel_a_postgres()
        if resultado["success"]:
            print(f"✅ Migración exitosa: {resultado['migrados']} docentes migrados")
        else:
            print(f"❌ Error en migración: {resultado.get('error', 'Desconocido')}")

verificar_y_migrar()

def es_personalizada(contraseña):
    if pd.isna(contraseña):
        return False
    texto = str(contraseña).lower().strip()
    return "personalizada" in texto

@app.route("/")
def index():
    if 'correo' not in session:
        return redirect(url_for('login_page'))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        
        if not correo.endswith("@uniagustiniana.edu.co"):
            return render_template("login.html", error="❌ Debes usar tu correo institucional (@uniagustiniana.edu.co)")
        
        # Verificar en PostgreSQL
        docentes = obtener_todos_docentes()
        existe = any(d['correo'] == correo for d in docentes)
        
        if not existe:
            return render_template("login.html", error="❌ Correo no registrado en el sistema. Contacta a Tecnologías.")
        
        session['correo'] = correo
        return redirect(url_for('index'))
    
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route("/consultar", methods=["POST"])
def consultar():
    if 'correo' not in session:
        return jsonify({"success": False, "error": "No autorizado"})
    
    try:
        data = request.get_json()
        cedula = str(data.get("cedula")).strip()
        correo_sesion = session['correo']
        
        # Buscar en PostgreSQL
        docente = obtener_docente_por_cedula(cedula)
        
        if not docente:
            return jsonify({"success": False, "error": "Cédula no encontrada"})
        
        # Validar que el correo de sesión coincida
        if correo_sesion != docente['correo']:
            return jsonify({
                "success": False,
                "mensaje": f"❌ La cédula {cedula} no corresponde a tu cuenta. Solo puedes consultar tus propias credenciales."
            })
        
        # Registrar consulta
        registrar_consulta_pg(docente['correo'], docente['cedula'], docente['nombre'])
        
        return jsonify({
            "success": True,
            "nombre": docente['nombre'],
            "correo": docente['correo'],
            "personalizada": docente['personalizada'],
            "enviado": True
        })
        
    except Exception as e:
        print(f"ERROR en consulta: {e}")
        return jsonify({"success": False, "error": "Error interno"})

# Importar y registrar el panel de administración
from admin_pg import admin_bp
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)