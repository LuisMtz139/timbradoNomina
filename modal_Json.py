import json
import os
import tkinter as tk
import xml.etree.ElementTree as ET

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Actualizar datos")

        window_width = 700
        window_height = 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        position_top = int((screen_height - window_height) / 2)
        position_right = int((screen_width - window_width) / 2)
        self.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

        self.create_widgets()
        
        
        if os.path.exists("rutas_configuracion.json"):
            with open('rutas_configuracion.json', 'r') as f:
                data = json.load(f)
        
            print(data['Ruta de Carpetas'])
            print(data['RutaFinalService'])
            print(data['RutaJSON'])
            
            
        
        self.path = data['Ruta de Carpetas']
        self.json_path = data['RutaJSON']
        
        
    def create_widgets(self):
        self.search_label = tk.Label(self, text="Buscar por RFC", font=('Helvetica', 12))  
        self.search_label.grid(row=0, column=0, pady=(20, 5), padx=(20, 10), sticky="w")

        self.search_entry = tk.Entry(self, width=30, font=('Helvetica', 12))
        self.search_entry.grid(row=1, column=0, padx=(20, 10), pady=(0, 5), sticky="w")

        self.update_button = tk.Button(self, text="Buscar", command=self.update_data, width=15, font=('Helvetica', 12))
        self.update_button.grid(row=1, column=1, padx=(0, 20), pady=(0, 5), sticky="w")

        self.result_frame = tk.Frame(self)
        self.result_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="w")

        # self.rfc_label = tk.Label(self.result_frame, text="RFC:", font=('Helvetica', 12))
        # self.rfc_label.grid(row=0, column=0, padx=(20, 5), pady=5, sticky="w")
        self.rfc_entry = tk.Entry(self.result_frame, font=('Helvetica', 12), width= 45)
        #self.rfc_entry.grid(row=0, column=1, padx=(20, 5), pady=5, sticky="w")

        self.nombre_label = tk.Label(self.result_frame, text="Nombre Receptor:", font=('Helvetica', 12))
        self.nombre_label.grid(row=1, column=0, padx=(20, 5), pady=5, sticky="w")
        self.nombre_entry = tk.Entry(self.result_frame, font=('Helvetica', 12), width= 45)
        self.nombre_entry.grid(row=1, column=1, padx=(20, 5), pady=5, sticky="w")

        self.domicilio_label = tk.Label(self.result_frame, text="Domicilio Fiscal Receptor:", font=('Helvetica', 12))
        self.domicilio_label.grid(row=2, column=0, padx=(20, 5), pady=5, sticky="w")
        self.domicilio_entry = tk.Entry(self.result_frame, font=('Helvetica', 12), width= 45)
        self.domicilio_entry.grid(row=2, column=1, padx=(20, 5), pady=5, sticky="w")

        self.save_button = tk.Button(self, text="Guardar", command=self.save_data, width=15, font=('Helvetica', 12))
        self.save_button.grid(row=4, column=1, padx=(0, 20), pady=(20, 5), sticky="e")

    def update_data(self):
        rfc_to_search = self.search_entry.get()
    
        try:
            with open(f"{self.json_path}/datos.json", 'r') as f:
                data = json.load(f)
                for item in data["Datos"]: 
                    if item["Rfc"] == rfc_to_search: 
                        self.rfc_entry.insert(0, item['Rfc'])
                        self.nombre_entry.insert(0, item['NombreReceptor'])
                        self.domicilio_entry.insert(0, item['DomicilioFiscalReceptor'])
                        break 
                else:  
                    print(f"No se encontró el RFC {rfc_to_search}")
        except Exception as e:
            print(f"Error al leer el archivo: {e}")
    
        print(f"Path: {self.path}")
        print(f"Actualizando datos para: {self.search_entry.get()}")

    def save_data(self):
        rfc_to_search = self.search_entry.get() 
    
        try:
            with open(f"{self.json_path}/datos.json", 'r') as f:  
                data = json.load(f)
    
            for item in data["Datos"]: 
                if item["Rfc"] == rfc_to_search: 
                    item['Rfc'] = self.rfc_entry.get().replace("RFC: ", "")
                    item['NombreReceptor'] = self.nombre_entry.get().replace("Nombre Receptor: ", "")
                    item['DomicilioFiscalReceptor'] = self.domicilio_entry.get().replace("Domicilio Fiscal Receptor: ", "")    
            with open(f"{self.json_path}/datos.json", 'w') as f:  
                json.dump(data, f)
    
        except Exception as e:
            print(f"Error al leer o guardar el archivo: {e}")
        self.destroy()