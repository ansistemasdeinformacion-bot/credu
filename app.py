from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

df = pd.read_excel("docentes.xlsx")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/consultar", methods=["POST"])
def consultar():
    data = request.json
    cedula = str(data.get("cedula"))

    resultado = df[df["CEDULA"].astype(str) == cedula]

    if not resultado.empty:
        fila = resultado.iloc[0]

        return jsonify({
            "success": True,
            "nombre": fila["NOMBRE"],
            "correo": fila["CORREO"]
        })
    else:
        return jsonify({"success": False})

if __name__ == "__main__":
    app.run(debug=True)