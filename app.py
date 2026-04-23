from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import os
import csv
from datetime import datetime
import pytz
from database import init_db, registrar_consulta_db

app = Flask(__name__)
app.secret_key = "clave_secreta_credu_2026"

# ============================================
# CONFIGURACIÓN DE SESIÓN (MANTENER LOGIN)
# ============================================
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas (en segundos)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Cambiar a True en producción con HTTPS

# Inicializar base de datos
init_db()

# Cargar Excel
df = pd.read_excel("docentes.xlsx")

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
        
        existe = df[df["CORREO INSTITUCIONAL"].astype(str).str.lower().str.strip() == correo]
        
        if existe.empty:
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
        
        resultado = df[df["CEDULA"].astype(str).str.strip() == cedula]
        
        if resultado.empty:
            return jsonify({"success": False, "error": "Cédula no encontrada"})
        
        fila = resultado.iloc[0]
        correo_registrado = str(fila.get("CORREO INSTITUCIONAL", "")).strip().lower()
        
        if correo_sesion != correo_registrado:
            return jsonify({
                "success": False, 
                "mensaje": f"❌ La cédula {cedula} no corresponde a tu cuenta. Solo puedes consultar tus propias credenciales."
            })
        
        nombre = str(fila.get("NOMBRE COMPLETO", "Usuario"))
        correo_destino = correo_registrado
        contraseña = fila.get("CONTRASEÑA", "")
        personalizada = es_personalizada(contraseña)
        
        registrar_consulta_db(correo_destino, cedula, nombre)
        
        return jsonify({
            "success": True,
            "nombre": nombre,
            "correo": correo_destino,
            "personalizada": personalizada,
            "enviado": True
        })
        
    except Exception as e:
        print(f"ERROR en consulta: {e}")
        return jsonify({"success": False, "error": "Error interno"})

# Importar y registrar el panel de administración
from admin import admin_bp
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)