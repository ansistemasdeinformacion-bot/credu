from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

# Leer archivo Excel
df = pd.read_excel('docentes.xlsx')

# Limpiar nombres de columnas
df.columns = df.columns.str.strip().str.upper()


@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/consultar', methods=['POST'])
def consultar():
    cedula = request.form['cedula']

    # Buscar docente
    docente = df[df['CEDULA'].astype(str) == cedula]

    if docente.empty:
        return "No se encontró el docente"

    docente = docente.iloc[0]

    # 🔥 FORZAR VALORES A STRING (IMPORTANTE)
    nombre = str(docente.get('NOMBRE COMPLETO', ''))
    usuario = str(docente.get('CEDULA', ''))  # ← ESTE ES EL FIX
    contraseña = str(docente.get('CONTRASEÑA', ''))

    personalizada = False

    # Detectar contraseña personalizada
    if "personalizada" in contraseña.lower():
        personalizada = True

    return render_template(
        'resultado.html',
        nombre=nombre,
        usuario=usuario,
        contraseña=contraseña,
        personalizada=personalizada
    )


# 🔥 NECESARIO PARA RENDER
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)