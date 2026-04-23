import pandas as pd

def obtener_todos_docentes():
    """Obtiene todos los docentes directamente del Excel"""
    try:
        df = pd.read_excel("docentes.xlsx")
        docentes = []
        for _, row in df.iterrows():
            try:
                cedula = str(row.get('CEDULA', '')).strip()
                if not cedula or cedula == 'nan':
                    continue
                nombre = str(row.get('NOMBRE COMPLETO', '')).strip()
                correo = str(row.get('CORREO INSTITUCIONAL', '')).strip().lower()
                contraseña = str(row.get('CONTRASEÑA', '')).strip()
                personalizada = "personalizada" in contraseña.lower()
                
                docentes.append({
                    "cedula": cedula,
                    "nombre": nombre,
                    "correo": correo,
                    "contraseña": contraseña,
                    "personalizada": personalizada
                })
            except:
                continue
        return docentes
    except Exception as e:
        print(f"Error leyendo Excel: {e}")
        return []

def migrar_excel_a_postgres(excel_path="docentes.xlsx"):
    return {"success": True, "migrados": 0, "errores": 0}

def agregar_docente(cedula, nombre, correo, contraseña):
    return {"success": False, "error": "Configuración en proceso"}

def actualizar_docente(cedula, nombre, correo, contraseña):
    return {"success": False, "error": "Configuración en proceso"}

def eliminar_docente(cedula):
    return {"success": False, "error": "Configuración en proceso"}

def obtener_docente_por_cedula(cedula):
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