import csv
from datetime import datetime

def registrar_consulta(correo, cedula, nombre):
    """Registra cada consulta en un archivo CSV para estadísticas"""
    try:
        archivo = "consultas.csv"
        existe = os.path.isfile(archivo)
        
        with open(archivo, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not existe:
                writer.writerow(["FECHA", "CORREO", "CEDULA", "NOMBRE"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), correo, cedula, nombre])
        print(f"✅ Consulta registrada: {correo}")
    except Exception as e:
        print(f"❌ Error registrando consulta: {e}")