# database_pg.py - Versión que solo usa Excel (sin PostgreSQL)
import pandas as pd

def obtener_todos_docentes():
    """Obtiene todos los docentes desde el Excel"""
    try:
        df = pd.read_excel("docentes.xlsx")
        docentes = []
        for _, row in df.iterrows():
            docentes.append({
                "cedula": str(row['CEDULA']),
                "nombre": str(row['NOMBRE COMPLETO']),
                "correo": str(row['CORREO INSTITUCIONAL']),
                "contraseña": str(row['CONTRASEÑA']),
                "personalizada": "personalizada" in str(row['CONTRASEÑA']).lower()
            })
        return docentes
    except Exception as e:
        print(f"Error leyendo Excel: {e}")
        return []

def migrar_excel_a_postgres(excel_path="docentes.xlsx"):
    """Simula migración (los datos ya están en Excel)"""
    return {"success": True, "migrados": 0, "errores": 0}

def agregar_docente(cedula, nombre, correo, contraseña):
    """Función deshabilitada temporalmente"""
    return {"success": False, "error": "Gestión de docentes desde Excel por ahora"}

def actualizar_docente(cedula, nombre, correo, contraseña):
    return {"success": False, "error": "Gestión de docentes desde Excel por ahora"}

def eliminar_docente(cedula):
    return {"success": False, "error": "Gestión de docentes desde Excel por ahora"}

def obtener_docente_por_cedula(cedula):
    """Obtiene un docente por su cédula desde el Excel"""
    try:
        df = pd.read_excel("docentes.xlsx")
        resultado = df[df["CEDULA"].astype(str).str.strip() == cedula]
        if not resultado.empty:
            row = resultado.iloc[0]
            return {
                "cedula": str(row['CEDULA']),
                "nombre": str(row['NOMBRE COMPLETO']),
                "correo": str(row['CORREO INSTITUCIONAL']),
                "contraseña": str(row['CONTRASEÑA']),
                "personalizada": "personalizada" in str(row['CONTRASEÑA']).lower()
            }
        return None
    except:
        return None