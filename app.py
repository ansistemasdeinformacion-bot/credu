from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Cargar Excel
df = pd.read_excel("docentes.xlsx")

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

        if not resultado.empty:
            fila = resultado.iloc[0]

            nombre = str(fila.get("NOMBRE COMPLETO", "Usuario"))
            correo = str(fila.get("CORREO INSTITUCIONAL", "No registrado"))

            return jsonify({
                "success": True,
                "nombre": nombre,
                "correo": correo
            })
        else:
            return jsonify({"success": False})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"success": False})

# IMPORTANTE PARA RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)