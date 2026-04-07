from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "clave_secreta_credu_2026"

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
        
        resultado = df[df["CEDULA"].astype(str).str.strip() == cedula]
        
        if resultado.empty:
            return jsonify({"success": False})
        
        fila = resultado.iloc[0]
        
        nombre = str(fila.get("NOMBRE COMPLETO", "Usuario"))
        correo_destino = str(fila.get("CORREO INSTITUCIONAL", "No registrado"))
        contraseña = fila.get("CONTRASEÑA", "")
        personalizada = es_personalizada(contraseña)
        
        # Por ahora, simulamos que el correo se envió correctamente
        # Más adelante configuraremos el envío real
        enviado = True
        
        return jsonify({
            "success": True,
            "nombre": nombre,
            "correo": correo_destino,
            "personalizada": personalizada,
            "enviado": enviado
        })
        
    except Exception as e:
        print(f"ERROR en consulta: {e}")
        return jsonify({"success": False})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)