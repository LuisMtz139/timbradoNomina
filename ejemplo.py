# main.py

import json

# Función para cargar los datos desde el archivo
def cargar_datos():
    try:
        with open("datos.json", "r") as archivo:
            datos = json.load(archivo)
    except FileNotFoundError:
        # Si el archivo no existe, retorna una lista vacía
        print("El archivo 'datos.json' no existe.")
        datos = []
    except json.JSONDecodeError:
        # Si hay un error al decodificar el archivo JSON, muestra un mensaje de error
        print("Error al decodificar el archivo JSON 'datos.json'.")
        datos = []
    return datos


# Función para guardar los datos en el archivo
def guardar_datos(datos):
    with open("datos.json", "w") as archivo:
        json.dump(datos, archivo, indent=4)

# Función principal
def main():
    # Cargar los datos existentes
    datos = cargar_datos()
    
    # Mostrar los datos actuales
    print("Datos actuales:")
    print(datos)
    
    # Obtener un nuevo dato
    nuevo_dato = input("Ingrese un nuevo dato: ")
    
    # Crear un nuevo diccionario con el dato y su índice
    nuevo_registro = {"indice": len(datos) + 1, "dato": nuevo_dato}
    
    # Agregar el nuevo registro a la lista de datos
    datos.append(nuevo_registro)
    
    # Guardar todos los datos (incluyendo los nuevos)
    guardar_datos(datos)

    # Mostrar mensaje de confirmación
    print("Dato guardado exitosamente.")

# Llamar a la función principal
if __name__ == "__main__":
    main()



# {
#     "Ruta de Carpetas": "C:\\Users\\pssbo\\Music\\config\\New folder",
#     "RutaFinalService": "C:\\Users\\pssbo\\Downloads\\FinalServiceQRluisdesarrollo\\FinalServiceQR\\CNE781229BK4_TEST",
#     "RutaJSON": "C:\\Users\\pssbo\\Downloads\\FinalServiceQRluisdesarrollo\\SellOS\\"
# }