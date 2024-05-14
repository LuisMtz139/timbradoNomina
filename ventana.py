import csv
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os.path
import sys

class ConfiguracionRutas:
    def __init__(self, on_close_callback=None):
        self.on_close_callback = on_close_callback
        self.app = tk.Tk()
        self.app.title('Configuración de Rutas')

        self.ruta_carpetas_entry = tk.Entry(self.app)
        self.ruta_final_service_entry = tk.Entry(self.app)
        self.ruta_json_entry = tk.Entry(self.app)

        # Crear etiquetas y entradas para rutas
        self.create_entry("Ruta de Carpetas:", self.ruta_carpetas_entry)
        self.create_entry("Ruta Final del Servicio:", self.ruta_final_service_entry)
        self.create_entry("Ruta del Archivo JSON:", self.ruta_json_entry)

        tk.Button(self.app, text="Guardar", command=self.guardar_y_cerrar).pack(pady=20)


    def create_entry(self, label_text, entry):
        tk.Label(self.app, text=label_text).pack(fill='x', padx=10, pady=5)
        entry.pack(fill='x', padx=10)


    def guardar_rutas(self):
        rutas = {
            "Ruta de Carpetas": self.ruta_carpetas_entry.get().replace('\\', '\\'),
            "Ruta Final del Servicio": self.ruta_final_service_entry.get().replace('\\', '\\'),
            "Ruta del Archivo JSON": self.ruta_json_entry.get().replace('\\', '\\'),
            "Puerto": 587,
            "Host": "smtp-relay.brevo.com",
            "password": "xsmtpsib-b091af1f5321eef397a4dea6a6951e9c656384ab1eda5ee4272400d277fb5be9-FNQaqpG1xfLRsjZW",
            "Correo": "rocencran@hotmail.com"
        }

        with open("rutas_configuracion.json", "w") as archivo_json:
            json.dump(rutas, archivo_json, indent=4)

        # Crear archivo escenario_ids.csv
        with open("escenario_ids.csv", "w", newline='') as archivo_csv:
            pass

        # Crear archivo num_rows_after_cleaning.txt
        with open("num_rows_after_cleaning.txt", "w") as archivo_txt:
            pass
            #archivo_txt.write("Contenido del archivo num_rows_after_cleaning.txt")

    def seleccionar_ruta(self, entry):
        ruta = filedialog.askdirectory()
        if ruta:
            entry.delete(0, tk.END)
            entry.insert(0, ruta)

    def guardar_y_cerrar(self):
        self.guardar_rutas()
        if self.on_close_callback:
            self.on_close_callback()
        self.app.destroy()

def main():
    try:
        configuracion = ConfiguracionRutas()
        if hasattr(configuracion, 'app'):
            configuracion.app.mainloop()
    except KeyboardInterrupt:
        sys.exit()

if __name__ == "__main__":
    main()
