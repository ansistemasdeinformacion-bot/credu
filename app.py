from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "clave_secreta_credu_2026"

# =====================================================
# CONFIGURACIÓN DE CORREO - YA CORREGIDA
# =====================================================
EMAIL_SENDER = "an.sistemasdeinformacion@uniagustiniana.edu.co"
EMAIL_PASSWORD = "hvnp lihx okqa bzyj"  # Contraseña de aplicación
EMAIL_SERVER = "smtp.gmail.com"
# =====================================================

# Cargar Excel
df = pd.read_excel("docentes.xlsx")

def enviar_correo_credenciales(destinatario, nombre, cedula, contraseña, personalizada):
    """Envía correo con credenciales usando TLS"""
    try:
        asunto = "🔐 Tus credenciales institucionales - CREDU"
        
        if personalizada:
            cuerpo_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #0b3c6f;">🎓 Universidad Uniagustiniana</h2>
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Has solicitado tus credenciales institucionales a través de CREDU.</p>
                
                <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                    <strong>⚠️ Tu contraseña fue personalizada por ti mismo</strong><br><br>
                    En caso de que no la recuerdes, debes acercarte a la oficina de Tecnologías<br>
                    o escribir al correo: <strong>an.sistemasdeinformacion@uniagustiniana.edu.co</strong>
                </div>
                
                <p><strong>👤 Nombre:</strong> {nombre}</p>
                <p><strong>📌 Usuario (cédula):</strong> {cedula}</p>
                <p><strong>📧 Correo:</strong> {destinatario}</p>
                
                <hr>
                <p style="color: #666; font-size: 12px;">Uniagustiniana es creer en ti</p>
            </body>
            </html>
            """
        else:
            cuerpo_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #0b3c6f;">🎓 Universidad Uniagustiniana</h2>
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Has solicitado tus credenciales institucionales a través de CREDU.</p>
                
                <div style="background-color: #e8f0fe; padding: 15px; margin: 20px 0; border-radius: 10px;">
                    <p><strong>👤 Nombre:</strong> {nombre}</p>
                    <p><strong>📌 Usuario (cédula):</strong> {cedula}</p>
                    <p><strong>🔐 Contraseña:</strong> {contraseña}</p>
                    <p><strong>📧 Correo:</strong> {destinatario}</p>
                </div>
                
                <p><strong>🔐 Estas credenciales aplican para:</strong></p>
                <p><b>SIGA - KAWAK - SIPA HCM</b></p>
                
                <hr>
                <p style="color: #666; font-size: 12px;">Uniagustiniana es creer en ti</p>
            </body>
            </html>
            """
        
        msg = MIMEMultipart()
        msg['Subject'] = asunto
        msg['From'] = EMAIL_SENDER
        msg['To'] = destinatario
        msg.attach(MIMEText(cuerpo_html, 'html'))
        
        # Conectar a Gmail con TLS
        server = smtplib.SMTP(EMAIL_SERVER, 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        # Quitar espacios de la contraseña de aplicación
        password_clean = EMAIL_PASSWORD.replace(" ", "")
        server.login(EMAIL_SENDER, password_clean)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Correo enviado a {destinatario}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")
        return False

def es_personalizada(contraseña):
    """Detecta si la contraseña es personalizada"""
    if pd.isna(contraseña):
        return False
    texto = str(contraseña).lower().strip()
    return "personalizada" in texto

@app.route("/")
def index():
    """Página principal (chat) - requiere login"""
    if 'correo' not in session:
        return redirect(url_for('login_page'))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login_page():
    """Pantalla de login con correo institucional"""
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        
        # Validar dominio institucional
        if not correo.endswith("@uniagustiniana.edu.co"):
            return render_template("login.html", error="❌ Debes usar tu correo institucional (@uniagustiniana.edu.co)")
        
        # Verificar si el correo existe en el Excel
        existe = df[df["CORREO INSTITUCIONAL"].astype(str).str.lower().str.strip() == correo]
        
        if existe.empty:
            return render_template("login.html", error="❌ Correo no registrado en el sistema. Contacta a Tecnologías.")
        
        session['correo'] = correo
        return redirect(url_for('index'))
    
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    """Cerrar sesión"""
    session.clear()
    return redirect(url_for('login_page'))

@app.route("/consultar", methods=["POST"])
def consultar():
    """Consulta credenciales del docente"""
    if 'correo' not in session:
        return jsonify({"success": False, "error": "No autorizado"})
    
    try:
        data = request.get_json()
        cedula = str(data.get("cedula")).strip()
        
        # Buscar por cédula
        resultado = df[df["CEDULA"].astype(str).str.strip() == cedula]
        
        if resultado.empty:
            return jsonify({"success": False})
        
        fila = resultado.iloc[0]
        
        nombre = str(fila.get("NOMBRE COMPLETO", "Usuario"))
        correo_destino = str(fila.get("CORREO INSTITUCIONAL", "No registrado"))
        contraseña = fila.get("CONTRASEÑA", "")
        personalizada = es_personalizada(contraseña)
        
        # Enviar correo real
        enviado = enviar_correo_credenciales(correo_destino, nombre, cedula, str(contraseña), personalizada)
        
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