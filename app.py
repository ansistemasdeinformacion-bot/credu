@app.route("/consultar", methods=["POST"])
def consultar():
    try:
        data = request.get_json()
        cedula = str(data.get("cedula"))

        resultado = df[df["CEDULA"].astype(str) == cedula]

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