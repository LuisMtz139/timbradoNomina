from datetime import datetime
import glob
import json
import shutil
import sys
import tkinter as tk
from tkinter import ttk, StringVar, messagebox
import os
import urllib.parse
import xml.etree.ElementTree as ET
import subprocess
import csv
from enviarCorreo import EnviarCorreo
from enviarProceso2 import DataPorceso2
from enviarTest import DataSender
from modal_Json import Application
from tableError import TableError
import re

from ventana import ConfiguracionRutas

class VistaPrincipal:
    def validar_quincena(self, input):
        if input.isdigit() or input == "":
            return True
        return False

    def validar_campos(self, *args):
        if self.entries['Quincena No.'].get() and self.dropdown.get():
            self.button2.config(state=tk.NORMAL)
        else:
            self.button2.config(state=tk.DISABLED)

    def configure_row_colors(self):
        self.table.tag_configure('oddrow', background='#E0E0F8')  # Color azul claro
        self.table.tag_configure('evenrow', background='white')  # Color blanco
        self.table.tag_configure('lastrow', background='purple')  # Color morado para la última fila
        self.table.tag_configure('greenrow', background='green')  # Color verde para la última fila
        self.table.tag_configure('selectedrow', background='#FFD580')

        num_rows_before = len(self.table.get_children())

        for i, row in enumerate(self.table.get_children()):
            tag = 'oddrow' if i % 2 == 0 else 'evenrow'
            self.table.item(row, tags=(tag,))

        num_rows_after = len(self.table.get_children())
        if num_rows_after > num_rows_before:
            last_row_id = self.table.get_children()[-1]
            self.table.item(last_row_id, tags=())
            self.table.item(last_row_id, tags=('greenrow',))
            self.table.see(last_row_id)

    def __init__(self, master):
        self.master = master
        self.master.title("Conalep-timbrado")
        self.initialize_ui()

    def initialize_ui(self):
        self.num_filas = 0
        self.escenario_id_seleccionado = None
        
        if os.path.exists("rutas_configuracion.json"):
            with open('rutas_configuracion.json', 'r') as f:
                data = json.load(f)

            print(data['Ruta de Carpetas'])
            self.path = data['Ruta de Carpetas']
        
        vcmd = self.master.register(self.validar_quincena)
        
        self.master.state('zoomed')
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=1)
        self.inner_frame = tk.Frame(self.main_frame, bd=2, relief=tk.SOLID)
        self.inner_frame.pack(fill=tk.BOTH, expand=1, padx=20, pady=20)
        
        inputs = ['Escenario Id', 'Quincena No.']
        self.entries = {}
        self.num_rows_cleaned = {}
    
        for i, input_text in enumerate(inputs):
            tk.Label(self.inner_frame, text=input_text, font=("Arial", 15)).grid(row=0, column=i, padx=10)
            if input_text == 'Quincena No.':
                self.quincena_var = StringVar()
                self.quincena_var.trace('w', self.validar_campos)
                entry = tk.Entry(self.inner_frame, textvariable=self.quincena_var, validate="key", validatecommand=(vcmd, '%P'),
                                width=20, bg='light yellow', font=("Arial", 15), justify='center')
            else:
                entry = tk.Entry(self.inner_frame, width=20, bg='light yellow', font=("Arial", 15), justify='center')
            entry.grid(row=1, column=i, padx=45)
            self.entries[input_text] = entry
            
        tk.Label(self.inner_frame, text="Registro Patronal", font=("Arial", 15)).grid(row=0, column=len(inputs), padx=20, sticky=tk.W)
        
        options = ['ORDINARIA IMSSS','TXT ADMINISTRATIVO', 'ORDINARIA ISSSTE', 'EXTRAORDINARIA IMSSS', 'EXTRAORDINARIA ISSSTE']
        self.dropdown = ttk.Combobox(self.inner_frame, values=options, font=("Arial", 15), state="readonly", style="Custom.TCombobox", width=30)
        self.dropdown.grid(row=1, column=len(inputs), padx=20, sticky=tk.W)
        self.dropdown.bind("<<ComboboxSelected>>", self.validar_campos)

        self.inner_frame.style = ttk.Style()
        self.inner_frame.style.theme_use("default")
        self.inner_frame.style.configure("Custom.TCombobox", selectbackground=self.inner_frame.cget("background"), selectforeground="black", anchor="center", background="lightyellow") 
        
        self.button_eliminar = tk.Button(self.inner_frame, text='Eliminar', font=("Arial", 13), bg='light yellow', command=self.confirmar_eliminar)
        self.button_eliminar.grid(row=1, column=len(self.entries)+2, padx=10, sticky=tk.E)
        self.button_eliminar.config(state=tk.DISABLED)  # Deshabilitar el botón al inicio
            
        self.inner_frame.style.configure("Custom.TCombobox.Listbox", background="lightyellow")
        button = tk.Button(self.inner_frame, text='Nuevo', font=("Arial", 13), bg='light yellow', command=self.resetear_campos)
        button.grid(row=1, column=len(inputs), padx=10, sticky=tk.E)

        self.inner_frame.grid_columnconfigure(len(inputs), weight=1)
        self.inner_frame.grid_columnconfigure(len(inputs)+1, minsize=90)

        self.button2 = tk.Button(self.inner_frame, text='Crear escenario', font=("Arial", 13), bg='light yellow', command=self.crear_escenario)
        self.button2.grid(row=1, column=len(inputs)+1, padx=10, sticky=tk.E)
        self.button2.config(state=tk.DISABLED)  # Deshabilitar el botón al inicio
        
        self.table = ttk.Treeview(self.inner_frame)
        self.table['columns'] = ('#1', '#2', '#3', '#4')
        self.table.column('#0', width=0, stretch=tk.NO)
        self.table.column('#1', width=150, stretch=tk.YES, anchor='center')
        self.table.column('#2', width=150, stretch=tk.YES, anchor='center')
        self.table.column('#3', width=150, stretch=tk.YES, anchor='center')
        self.table.column('#4', width=150, stretch=tk.YES, anchor='center')

        self.table.heading('#1', text='ESCENARIO ID', anchor='center')
        self.table.heading('#2', text='QUINCENA NO.', anchor='center')
        self.table.heading('#3', text='TIPONOMINA', anchor='center')
        self.table.heading('#4', text='POR_TIMBRAR', anchor='center')
        self.table.tag_configure('lightgreenrow', background='#90EE90')  # Configurar el estilo lightgreenrow con color verde claro

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10))
        self.table.place(relx=0.5, rely=0.50, relwidth=0.99, relheight=0.7, anchor=tk.CENTER) 

        self.cargar_datos_escenario()
        self.configurar_envio_datos()
        self.configure_row_colors()

        self.num_rows_cleaned = {}

        self.table.bind("<ButtonRelease-1>", self.mostrar_escenario_id)
        
    def confirmar_eliminar(self):
        if messagebox.askyesno("Confirmar eliminación", "¿Estás seguro de que deseas eliminar este escenario?"):
            self.eliminar_func()
        
    def eliminar_func(self):
        selected_item = self.table.focus()
        escenario_id = self.table.item(selected_item, "values")[0] if selected_item else None
        if escenario_id:
            self.eliminar_fila_csv(escenario_id)
            print("Fila eliminada del archivo CSV.")
            self.cargar_datos_escenario()
            self.seguir_ultima_fila()
            self.button_eliminar.config(state=tk.DISABLED)  
        else:
            print("No se ha seleccionado ningún Escenario ID.")
        
    def mostrar_escenario_id(self, event):
        if event:
            for i, row in enumerate(self.table.get_children()):
                tag = 'oddrow' if i % 2 == 0 else 'evenrow'
                self.table.item(row, tags=(tag,))

            item = self.table.focus()
            values = self.table.item(item, "values") if item else None
            if values:
                escenario_id = values[0]
                quincena_no = values[1]
                print("Escenario ID seleccionado:", escenario_id)
                print("Quincena No. seleccionado:", quincena_no)
                self.button_eliminar.config(state=tk.NORMAL)
                self.escenario_id_seleccionado = escenario_id
                self.quincena_no_seleccionado = quincena_no  # Guardar Quincena No. seleccionado
                self.table.item(item, tags=('selectedrow',))
            else:
                self.button_eliminar.config(state=tk.DISABLED)
                self.escenario_id_seleccionado = None
                self.quincena_no_seleccionado = None  
        
    def configurar_envio_datos(self):
        self.button_pressed = False

        def on_button_press():
            if self.button['state'] == tk.DISABLED:
                self.button_pressed = False
                print(self.button_pressed)
            else:
                self.button_pressed = True
                print(self.button_pressed)
                self.iniciar_proceso_de_timbrado()
                self.cargar_datos_escenario()
                self.configure_row_colors()
                self.resetear_campos()

        self.button = tk.Button(self.main_frame, text="Timbrado", command=on_button_press)
        self.button.place(relx=0.1, rely=0.9, anchor=tk.CENTER)
        self.button.config(width=25, height=2, font=("Arial", 13))
        self.button.config(state=tk.NORMAL)

        self.other_button = tk.Button(self.main_frame, text="Dispersar por correo",
                                    command=lambda: [self.mandar_correo(), self.cargar_datos_escenario()])
        self.other_button.place(relx=0.3, rely=0.9, anchor=tk.E)
        self.other_button.config(width=25, height=2, font=("Arial", 13))

        self.button_nuevo = tk.Button(self.master, text="Datos fiscales", command=self.create_new_application)
        self.button_nuevo.place(relx=0.5, rely=0.9, anchor=tk.CENTER)
        self.button_nuevo.config(width=25, height=2, font=("Arial", 13))
        self.button_nuevo.config(state=tk.NORMAL)

        self.button_actualizar = tk.Button(self.main_frame, text="Extraccion XML", command=self.Extraccion)
        self.button_actualizar.place(relx=0.7, rely=0.9, anchor=tk.CENTER)
        self.button_actualizar.config(width=25, height=2, font=("Arial", 13))
        self.button_actualizar.config(state=tk.NORMAL)

        
            

    def Extraccion(self):
        if os.path.exists("rutas_configuracion.json"):
            with open('rutas_configuracion.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            print("El archivo 'rutas_configuracion.json' no existe.")
            return

        print(data['Ruta de Carpetas'])
        print(data['RutaFinalService'])
        print(data['RutaJSON'])
        self.path = data['Ruta de Carpetas']

        # Crear la carpeta "extraccion" si no existe
        extraccion_folder = os.path.join(self.path, self.escenario_id_seleccionado, "extraccion")
        if not os.path.exists(extraccion_folder):
            os.makedirs(extraccion_folder)
            print(f"La carpeta 'extraccion' ha sido creada correctamente en la siguiente ubicación:\n{extraccion_folder}")
        else:
            print(f"La carpeta 'extraccion' ya existe en la siguiente ubicación:\n{extraccion_folder}")

        print("Extracción de xml...")
        if hasattr(self, 'escenario_id_seleccionado') and self.escenario_id_seleccionado:
            print("ID del escenario seleccionado:", self.escenario_id_seleccionado)
            full_path = os.path.join(self.path, self.escenario_id_seleccionado)
            print("Ruta completa del escenario:", full_path)

            if os.path.exists(full_path):
                print("Contenidos de la carpeta:")
                for content in os.listdir(full_path):
                    print(content)

                # Buscar la carpeta 'timbrado'
                timbrado_path = os.path.join(full_path, 'timbrado')
                if os.path.exists(timbrado_path):
                    print("Contenidos de la carpeta 'timbrado':")
                    for content in os.listdir(timbrado_path):
                        print(content)

                    # Buscar el archivo 'procesados.txt'
                    timbrados_file_path = os.path.join(timbrado_path, 'procesados.txt')
                    if os.path.exists(timbrados_file_path):
                        print("Contenido del archivo 'procesados.txt':")
                        with open(timbrados_file_path, 'r', encoding='utf-8') as file:
                            for line in file:
                                parts = line.split('|')
                                print(parts[0], parts[3])  # Imprime solo los elementos de interés

                                if len(parts[3]) > 10:
                                    print("La línea '" + line.strip() + "' es un txt")
                                    # Buscar un archivo xml que comienza con el nombre de la posición 0
                                    xml_file_path = os.path.join(timbrado_path, parts[0] + '*.xml')
                                    xml_files = glob.glob(xml_file_path)

                                    if xml_files:
                                        print("Archivo XML encontrado:", xml_files[0])
                                        # Formar el nuevo nombre del archivo XML
                                        new_file_name = "P" + parts[3][2:16] + '.xml'
                                        new_xml_file_path = os.path.join(extraccion_folder, new_file_name)
                                        # Copiar y renombrar el archivo XML
                                        shutil.copy(xml_files[0], new_xml_file_path)
                                        print("Archivo XML renombrado y copiado:", new_xml_file_path)
                                    else:
                                        print("No se encontró ningún archivo XML que comienza con", parts[0])
                                else:
                                    print("La línea '" + line.strip() + "' no es un txt")
                                    # Buscar un archivo xml que comienza con el nombre de la posición 0
                                    xml_file_path = os.path.join(timbrado_path, parts[0] + '*.xml')
                                    xml_files = glob.glob(xml_file_path)

                                    if xml_files:
                                        print("Archivo XML encontrado:", xml_files[0])
                                        # Parsear el archivo XML y encontrar el elemento 'NumEmpleado'
                                        tree = ET.parse(xml_files[0])
                                        root = tree.getroot()
                                        receptor = root.find('.//{http://www.sat.gob.mx/nomina12}Receptor')
                                        if receptor is not None:
                                            num_empleado = receptor.get('NumEmpleado')
                                            if num_empleado is not None:
                                                print("NumEmpleado encontrado:", num_empleado)

                                                # Verificar la existencia del archivo CSV
                                                csv_file_path = "escenario_ids.csv"
                                                if os.path.exists(csv_file_path):
                                                    print('El archivo "escenario_ids.csv" existe:', os.path.abspath(csv_file_path))
                                                else:
                                                    print('El archivo "escenario_ids.csv" no existe.')
                                                    return

                                                # Leer el archivo CSV
                                                with open(csv_file_path, "r", newline='', encoding='utf-8') as file:
                                                    reader = csv.reader(file)
                                                    for row in reader:
                                                        if row and row[0] == self.escenario_id_seleccionado:
                                                            print("Escenario ID encontrado en CSV:", row)
                                                            # Formar la ruta
                                                            current_year = datetime.now().strftime('%y')
                                                            ruta = "P" + current_year + row[2] + num_empleado
                                                            print("Ruta formada:", ruta)
                                                            # Hacer una copia del archivo XML y nombrarlo según la ruta formada
                                                            new_xml_file_name = os.path.join(extraccion_folder, ruta + ".xml")
                                                            shutil.copy(xml_files[0], new_xml_file_name)
                                                            print("Copia del archivo XML creada:", new_xml_file_name)
                                            else:
                                                print("La etiqueta 'NumEmpleado' no tiene valor.")
                                        else:
                                            print("No se encontró la etiqueta 'Receptor' en el archivo XML.")
                                    else:
                                        print("No se encontró ningún archivo XML que comienza con", parts[0])
                            else:
                                print("El archivo 'procesados.txt' no existe.")
                else:
                    print("La carpeta 'timbrado' no existe.")
            else:
                print("La carpeta especificada no existe.")
        else:
            print("No se ha seleccionado ningún escenario.")


    def create_new_application(self):
        new_app = Application()  # Crea una nueva instancia de Application
        new_app.mainloop()  
        self.auto_load_escenario()
            

    
    def validar_campos(self, *args):
        if self.entries['Quincena No.'].get() and self.dropdown.get():
            self.button2.config(state=tk.NORMAL)  
        else:
            self.button2.config(state=tk.DISABLED)  

    
    def mandar_correo(self):
        if self.escenario_id_seleccionado and self.quincena_no_seleccionado:
            try:
                # Construye la ruta base para el escenario seleccionado
                base_path = os.path.join(self.path, self.escenario_id_seleccionado)
                # Construye la ruta completa hacia la carpeta 'timbrado' dentro del escenario
                print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', self.escenario_id_seleccionado)
                full_path = os.path.join(base_path, 'timbrado')

                # Verifica si el directorio de 'timbrado' existe y si contiene el archivo 'procesados.txt'
                if os.path.exists(full_path) and os.path.exists(os.path.join(full_path, 'procesados.txt')):
                    correo = EnviarCorreo()
                    correo.otro(self.escenario_id_seleccionado, self.quincena_no_seleccionado)  # Pasar Quincena No. como parámetro
                else:
                    print(f"No se encontraron los archivos necesarios en el directorio {full_path}.")

            except FileNotFoundError:
                print("El archivo escenario_ids.csv no existe.")
        else:
            print("No se ha seleccionado ningún escenario ID o Quincena No.")

        
        
    def iniciar_proceso_de_timbrado(self):
        if self.escenario_id_seleccionado:
            print("Sí, se seleccionó un Escenario ID antes de presionar Timbrado:", self.escenario_id_seleccionado)
            dataPorceso2 = DataPorceso2()
            dataPorceso2.enviar_datos(self.entries, self.dropdown, self.path, self.mostrar_vista_errores,self.escenario_id_seleccionado )
            self.cargar_datos_escenario()
            self.resetear_campos()
            self.configure_row_colors()
        else:
            print("No, no se seleccionó un Escenario ID antes de presionar Timbrado")
            data_sender = DataSender()
            data_sender.enviar_datos(self.entries, self.dropdown, self.path, self.mostrar_vista_errores)
            self.cargar_datos_escenario()
            self.configure_row_colors()



    def on_button_state_change(self, *args):
        if self.button_state.get() == 'normal':
            self.cargar_datos_escenario()

    def obtener_num_filas_limpiadas(self, escenario_id):
        self.filas_limpiadas = {} 
        try:
            if os.path.exists("num_rows_after_cleaning.txt"):
                    csv_file_pathd = os.path.abspath("num_rows_after_cleaning.txt")
                    print('existe ',csv_file_pathd )
            else:
                    print('no existe')

            self.num_rows_file_path = csv_file_pathd
            with open(self.num_rows_file_path, 'r') as file:
                for line in file:
                    if line.startswith(f"Escenario ID: {escenario_id}"):
                        self.num_filas = int(line.split(":")[-1].strip())
                        self.filas_limpiadas[escenario_id] = self.num_filas  
                        return self.num_filas
        except FileNotFoundError:
            print("El archivo num_rows_after_cleaning.txt no se encontró.")
        except ValueError:
            print("Error al leer el número de filas limpiadas para el Escenario ID:", escenario_id)
        return 0
    
    
    
    def check_and_refresh_table(self):
        rows = self.table.get_children()
        if not rows:
            return
        last_row = rows[-1]
        por_timbrar_value = self.table.item(last_row, 'values')[3]
        if por_timbrar_value == '0':
            self.cargar_datos_escenario()
            
    def cargar_datos_escenario(self):
        for row in self.table.get_children():
            self.table.delete(row)
        try:
            if os.path.exists("escenario_ids.csv"):
                csv_file_pathd = os.path.abspath("escenario_ids.csv")
                print('existe ',csv_file_pathd )
            else:
                print('no existe')

            csv_file_path = csv_file_pathd

            with open(csv_file_path, "r", newline='') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row: 
                        num_filas = '' 
                        escenario_id = row[0]
                        quincena_no = row[2] if len(row) > 2 else ''
                        registro_patronal = row[3] if len(row) > 3 else ''
                        status = row[4] if len(row) > 4 else ''
                        comparar = self.comparar_escenario_ids()
                        if comparar is not None and escenario_id in comparar:
                            num_filas = comparar[escenario_id]
                        if not num_filas:  
                            num_filas = status
                        else:  
                            print(num_filas)
                        self.table.insert('', 'end', values=(escenario_id, quincena_no, registro_patronal, num_filas))
                        self.configure_row_colors()
                    
            for row in self.table.get_children():
                values = self.table.item(row, 'values')
        except FileNotFoundError:
            print("El archivo no existe, se creará al guardar un nuevo escenario.")
            

    def eliminar_fila_csv(self, escenario_id):
        if os.path.exists("escenario_ids.csv"):
                csv_file_pathd = os.path.abspath("escenario_ids.csv")
                print('existe ',csv_file_pathd )
        else:
                print('no existe')

        csv_file_path = csv_file_pathd
        
        temp_file_path = os.path.join(os.path.dirname(__file__), 'temp_escenario_ids.csv')

        with open(csv_file_path, "r", newline='') as file, open(temp_file_path, "w", newline='') as temp_file:
            reader = csv.reader(file)
            writer = csv.writer(temp_file)

            for row in reader:
                if row and row[0] == escenario_id:
                    self.eliminar_carpeta_escenario(escenario_id)
                    continue  
                writer.writerow(row)

        os.remove(csv_file_path)  
        os.rename(temp_file_path, csv_file_path)  

    def eliminar_carpeta_escenario(self, escenario_id):
        ruta_carpeta = os.path.join(self.path, escenario_id)
        if os.path.exists(ruta_carpeta):
            shutil.rmtree(ruta_carpeta)
            print(f"Carpeta del escenario {escenario_id} eliminada correctamente.")
        else:
            print(f"La carpeta del escenario {escenario_id} no existe.")


    def eliminar_func(self):
        selected_item = self.table.focus()
        escenario_id = self.table.item(selected_item, "values")[0] if selected_item else None
        if escenario_id:
            self.eliminar_fila_csv(escenario_id)
            print("Fila eliminada del archivo CSV.")
            self.cargar_datos_escenario()
            self.seguir_ultima_fila()
            self.button_eliminar.config(state=tk.DISABLED)  
        else:
            print("No se ha seleccionado ningún Escenario ID.")



    def obtener_num_rows(self):
        print('obtner valores txt')
        try:
            if os.path.exists("num_rows_after_cleaning.txt"):
                    csv_file_pathd = os.path.abspath("num_rows_after_cleaning.txt")
                    print('existe ',csv_file_pathd )
            else:
                    print('no existe')

            self.num_rows_file_path = csv_file_pathd
            with open(self.num_rows_file_path, 'r') as file:
                for line in file:
                    if line.startswith("Escenario ID:"):
                        escenario_id = line.split(":")[1].strip()
                        print(escenario_id)
        except FileNotFoundError:
            pass
        return 0
    
    def leer_primero_valor_escenario_ids(self):
        print('archivo csv')
        try:
            if os.path.exists("escenario_ids.csv"):
                csv_file_pathd = os.path.abspath("escenario_ids.csv")
                print('existe ',csv_file_pathd )
            else:
                print('no existe')

            csv_file_path = csv_file_pathd
            
            with open(csv_file_path, "r", newline='') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row: 
                        primer_valor = row[0]
                        print(primer_valor)
        except FileNotFoundError:
            print("El archivo no existe.")
            
    def comparar_escenario_ids(self):
            valores_texto = {} 
            valores_csv = set()  
            try:
                if os.path.exists("num_rows_after_cleaning.txt"):
                    csv_file_pathd = os.path.abspath("num_rows_after_cleaning.txt")
                    print('existe ',csv_file_pathd )
                else:
                    print('no existe')

                self.num_rows_file_path = csv_file_pathd
                with open(self.num_rows_file_path, 'r') as file:
                    for line in file:
                        if line.startswith("Escenario ID:"):
                            escenario_id = line.split(":")[1].strip()
                            num = next(file).split(":")[1].strip()  
                            valores_texto[escenario_id] = num
                    return valores_texto
            except FileNotFoundError:
                print("El archivo de texto no existe.")
            try:
                if os.path.exists("escenario_ids.csv"):
                    csv_file_pathd = os.path.abspath("escenario_ids.csv")
                    print('existe ',csv_file_pathd )
                else:
                    print('no existe')

                csv_file_path = csv_file_pathd
                
                with open(csv_file_path, "r", newline='') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if row: 
                            primer_valor = row[0]
                            valores_csv.add(primer_valor)
                            print(f"Primer valor del archivo CSV: {primer_valor}")
            except FileNotFoundError:
                print("El archivo CSV no existe.")
                return None
            
            valores_comunes = set(valores_texto.keys()).intersection(valores_csv)
            
            if valores_comunes:
                print("Valores presentes tanto en el archivo de texto como en el archivo CSV:")
                for valor in valores_comunes:
                    print(f"Escenario ID: {valor}, Número de filas limpiadas: {valores_texto[valor]}")
            else:
                print("No hay valores comunes entre el archivo de texto y el archivo CSV.")
                return None
            
    def agrupar_valores(self):
        valores_agrupados = {}

        try:
            if os.path.exists("num_rows_after_cleaning.txt"):
                    csv_file_pathd = os.path.abspath("num_rows_after_cleaning.txt")
                    print('existe ',csv_file_pathd )
            else:
                    print('no existe')

            self.num_rows_file_path = csv_file_pathd
            with open(self.num_rows_file_path, 'r') as file:
                for line in file:
                    if line.startswith("Escenario ID:"):
                        escenario_id = line.split(":")[1].strip()
                        valores_agrupados.setdefault(escenario_id, [])
        except FileNotFoundError:
            print("El archivo num_rows_after_cleaning.txt no se encontró.")

        try:
            if os.path.exists("escenario_ids.csv"):
                csv_file_pathd = os.path.abspath("escenario_ids.csv")
                print('existe ',csv_file_pathd )
            else:
                print('no existe')

            csv_file_path = csv_file_pathd

            with open(csv_file_path, "r", newline='') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row: 
                        primer_valor = row[0]
                        valores_agrupados.setdefault(primer_valor, [])
        except FileNotFoundError:
            print("El archivo escenario_ids.csv no existe.")

        for key, value in valores_agrupados.items():
            print(f"Valor: {key}, Apariciones: {len(value)}")
    

    def crear_escenario(self):
        now = datetime.now()
        now_str = now.strftime("%m%d%Y%H%M")
        quincena_no = self.entries['Quincena No.'].get()
        tipo_nomina = self.dropdown.get()
        registro_patronal = self.dropdown.get()

        self.entries['Escenario Id'].delete(0, tk.END)
        self.entries['Escenario Id'].insert(0, now_str)
        self.entries['Escenario Id'].config(state="readonly")  
        self.entries['Escenario Id'].bind("<FocusIn>", lambda event: self.entries['Escenario Id'].config(state="readonly")) 
        
        if os.path.exists("escenario_ids.csv"):
                csv_file_pathd = os.path.abspath("escenario_ids.csv")
                print('existe ',csv_file_pathd )
        else:
                print('no existe')

        csv_file_path = csv_file_pathd

        with open(csv_file_path, "a", newline='') as file:
            writer = csv.writer(file)
            writer.writerow([now_str, now.strftime("%Y-%m-%d %H:%M"), quincena_no, registro_patronal])

        base_dir = os.path.join(self.path, now_str)
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'erroneos'), exist_ok=True)
        universo_dir = os.path.join(base_dir, 'universo')
        os.makedirs(universo_dir, exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'timbrado'), exist_ok=True)
        subprocess.run(['explorer', universo_dir])

        new_row = self.table.insert('', 'end', values=(now_str, quincena_no, tipo_nomina, ''))
        self.configure_row_colors()
        
        self.seguir_ultima_fila()
        self.button.config(state=tk.NORMAL)


    def seguir_ultima_fila(self):
        rows = self.table.get_children()
        if rows:
            last_row_id = rows[-1]
            self.table.item(last_row_id, tags=())  
            self.table.item(last_row_id, tags=('lightgreenrow',))
            self.table.see(last_row_id)

    def mostrar_vista_errores(self):
        if hasattr(self, 'new_window') and self.new_window.winfo_exists():
            return
        
        
        
        
        if os.path.exists("escenario_ids.csv"):
                csv_file_pathd = os.path.abspath("escenario_ids.csv")
                print('existe ',csv_file_pathd )
        else:
                print('no existe')

        csv_file_path = csv_file_pathd
        
        quincena_no_encoded = ''
        registro_patronal_encoded = ''

        try:
            with open(csv_file_path, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == self.escenario_id_seleccionado:
                        valor1, valor2, valor3, valor4 = row[:4]
                        quincena_no_encoded = urllib.parse.quote(valor3)
                        registro_patronal_encoded = urllib.parse.quote(valor4)
                        print(f"valor1 = {valor1}, valor2 = {valor2}, valor3 = {valor3}, valor4 = {valor4}")
        except FileNotFoundError:
            print(f"No se encontró el archivo {csv_file_path}")

        escenario_id = self.escenario_id_seleccionado.strip() if self.escenario_id_seleccionado and self.escenario_id_seleccionado.strip() else self.entries['Escenario Id'].get().strip()
        quincena_no = quincena_no_encoded.strip() if quincena_no_encoded and quincena_no_encoded.strip() else self.entries['Quincena No.'].get().strip()
        registro_patronal_text = registro_patronal_encoded.strip() if registro_patronal_encoded and registro_patronal_encoded.strip() else self.dropdown.get().strip()

        self.new_window = tk.Toplevel(self.master)
        self.app = TableError(self.new_window, escenario_id, quincena_no, registro_patronal_text)
        window_x = self.master.winfo_x()
        window_y = self.master.winfo_y()
        self.new_window.geometry("+%d+%d" % (window_x, window_y))



    def cerrar(self):
        self.master.destroy()
        
    def resetear_campos(self):
        # Limpiar todos los campos de entrada
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        
        # Resetear el combobox a su estado inicial
        self.dropdown.set('')
        
        # Asegurarse de que el campo 'Escenario Id' esté limpio y en estado normal
        self.entries['Escenario Id'].config(state=tk.NORMAL)
        self.entries['Escenario Id'].delete(0, tk.END)
        
        # Cargar los datos de los escenarios para refrescar la tabla
        self.cargar_datos_escenario()
        
        # Desactivar cualquier botón que requiera una selección o datos específicos
        if hasattr(self, 'button_eliminar'):
            self.button_eliminar.config(state=tk.NORMAL)
        if hasattr(self, 'button'):
            self.button.config(state=tk.NORMAL)
        
        # Eliminar cualquier selección de escenario previamente seleccionada
        self.escenario_id_seleccionado = None

        if hasattr(self, 'table'):
            self.table.selection_remove(self.table.selection())

        print("Campos y estado de la interfaz reseteados al estado inicial.")


        
    def refresh_table_periodically(self):
        self.check_and_refresh_table()
        self.master.after(1000, self.refresh_table_periodically)
        
    def refresh_table(self):
        self.cargar_datos_escenario()
        self.configure_row_colors()

    def auto_load_escenario(self):
        self.crear_escenario()
        self.master.after(5000, self.auto_load_escenario)
        
        
def main():
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal

    def start_vista_principal():
        VistaPrincipal(root)

    if os.path.exists("rutas_configuracion.json"):
        start_vista_principal()
    else:
        ConfiguracionRutas(on_close_callback=start_vista_principal)

    root.mainloop()

if __name__ == "__main__":
    main()