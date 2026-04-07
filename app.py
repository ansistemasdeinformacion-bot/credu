from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Cargar Excel
df = pd.read_excel("docentes.xlsx")

# Función para detectar si es contraseña personalizada
def es_personalizada(contraseña):
    if pd.isna(contraseña):
        return False
    texto = str(contraseña).lower().strip()
    return "personalizada" in texto

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/consultar", methods=["POST"])
def consultar():
    try:
        data = request.get_json()
        cedula = str(data.get("cedula")).strip()

        # Buscar por cédula
        resultado = df[df["CEDULA"].astype(str).str.strip() == cedula]

        if resultado.empty:
            return jsonify({"success": False})

        fila = resultado.iloc[0]

        nombre = str(fila.get("NOMBRE COMPLETO", "Usuario"))
        correo = str(fila.get("CORREO INSTITUCIONAL", "No registrado"))
        contraseña = fila.get("CONTRASEÑA", "")

        personalizada = es_personalizada(contraseña)

        # Si es personalizada, mostramos mensaje especial
        if personalizada:
            contraseña_mostrar = "contraseña personalizada"
        else:
            contraseña_mostrar = str(contraseña)

        return jsonify({
            "success": True,
            "nombre": nombre,
            "correo": correo,
            "contraseña": contraseña_mostrar,
            "personalizada": personalizada
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"success": False})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)