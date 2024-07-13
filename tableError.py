import json
import os
import re
import shutil
import tkinter as tk
from tkinter import ttk, Scrollbar
from enviarTest import DataSender


class TableError:
    def __init__(self, master, escenario_id, quincena_no, registro_patronal_text):
        self.master = master
        self.escenario_id = escenario_id
        self.quincena_no = quincena_no
        self.registro_patronal_text = registro_patronal_text
        self.files_edited = {}
        self.save_timer = None
        self.last_selection = None

        self.master.title("Conalep-timbrado")
        self.master.state('zoomed')
        self.config_path = self.load_config_path()
        self.create_scenario_directory(self.escenario_id)
        self.list_directory_contents()

        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        self.inner_frame = tk.Frame(self.main_frame, bd=2, relief=tk.SOLID)
        self.inner_frame.pack(fill=tk.BOTH, expand=1, padx=20, pady=20)

        self.new_frame = tk.Frame(self.inner_frame, bd=2, relief=tk.SOLID)
        self.new_frame.pack(fill=tk.BOTH, expand=1, padx=20, pady=(20, 70))

        self.setup_column1()
        self.setup_column2()
        self.setup_column3()

        self.button = tk.Button(self.main_frame, text="Guardar", command=self.guardar_cerrar, state=tk.NORMAL)
        self.button.place(relx=0.1, rely=0.94, anchor=tk.CENTER)
        self.button.config(width=20, height=2)

    def setup_column1(self):
        self.column1 = tk.Frame(self.new_frame, bd=2, relief=tk.SOLID)
        self.column1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.column1_label = tk.Label(self.column1, text="Datos txt", font=("Helvetica", 12, "bold"))
        self.column1_label.pack(pady=10)

        self.listbox = tk.Listbox(self.column1, height=5)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.populate_listbox()
        self.listbox.bind("<<ListboxSelect>>", self.mostrar_contenido)

        separator1 = ttk.Separator(self.new_frame, orient='vertical')
        separator1.pack(side=tk.LEFT, fill='y', padx=5)

    def setup_column2(self):
        self.column2 = tk.Frame(self.new_frame, bd=2, relief=tk.SOLID)
        self.column2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.column2_label = tk.Label(self.column2, text="Contenido", font=("Helvetica", 12, "bold"))
        self.column2_label.pack(pady=10)
        self.error_text = tk.Text(self.column2, wrap="word", height=10, width=50)
        self.error_text.pack(fill=tk.BOTH, expand=True)
        self.scrollbar = Scrollbar(self.column2, command=self.error_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.error_text.config(yscrollcommand=self.scrollbar.set)
        self.setup_text_widget()

        separator2 = ttk.Separator(self.new_frame, orient='vertical')
        separator2.pack(side=tk.LEFT, fill='y', padx=5)

    def setup_column3(self):
        self.column3 = tk.Frame(self.new_frame, bd=4, relief=tk.SOLID, width=400)
        self.column3.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        self.column3.pack_propagate(False)
        self.error_title_label = tk.Label(self.column3, text="Error", font=("Helvetica", 12, "bold"))
        self.error_title_label.pack(pady=(10, 0))

        separator3 = ttk.Separator(self.column3, orient='horizontal')
        separator3.pack(fill='x', padx=5, pady=5)

        self.escenario_id_label = tk.Label(self.column3, font=("Helvetica", 10), wraplength=380, justify=tk.LEFT)
        self.escenario_id_label.pack(pady=(0, 10))

    def cerrar(self):
        self.master.destroy()

    def mostrar_contenido(self, event=None):
        if self.listbox.curselection():
            self.last_selection = self.listbox.get(self.listbox.curselection())
        
        if self.last_selection:
            seleccion = self.last_selection
            archivo_seleccionado_path = os.path.join(self.config_path, self.escenario_id, 'universo', seleccion)
            error_file_path = os.path.join(self.config_path, self.escenario_id, 'erroneos', 'errortimbrado.txt')
            error_line = self.obtener_linea_error(error_file_path, seleccion)
            self.escenario_id_label.config(text=error_line)
            self.mostrar_contenido_archivo(archivo_seleccionado_path, seleccion)
        else:
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(tk.END, "No hay archivo seleccionado.")

    def obtener_linea_error(self, error_file_path, seleccion):
        error_line = "No se encontró información para el archivo"
        try:
            with open(error_file_path, 'r') as file:
                for line in file:
                    parts = line.split('|')
                    if len(parts) > 4 and os.path.basename(parts[4].strip()) == seleccion:
                        error_line = f"Error identificado: {line.strip()}"
                        break
                else:
                    error_line = f"No se encontró información para el archivo '{seleccion}' en errortimbrado.txt"
        except FileNotFoundError:
            error_line = "El archivo errortimbrado.txt no se encontró en la carpeta especificada."
        except Exception as e:
            error_line = f"Ocurrió un error al intentar leer el archivo errortimbrado.txt: {e}"
        return error_line

    def mostrar_contenido_archivo(self, archivo_seleccionado_path, seleccion):
        try:
            with open(archivo_seleccionado_path, 'r') as file:
                contenido = file.read()
                self.error_text.delete(1.0, tk.END)
                self.error_text.insert(tk.END, contenido)
        except FileNotFoundError:
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(tk.END, f"El archivo '{seleccion}' no se encontró.")
        except Exception as e:
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(tk.END, f"Error al leer el archivo '{seleccion}': {str(e)}")

    def setup_text_widget(self):
        self.error_text.bind("<KeyRelease>", self.on_key_release)

    def on_key_release(self, event):
        if self.save_timer:
            self.master.after_cancel(self.save_timer)
        self.save_timer = self.master.after(10, self.guardar_cambios)

    def guardar_cerrar(self):
        self.guardar_cambios()
        self.master.destroy()

    def guardar_cambios(self):
        if self.last_selection:
            archivo_seleccionado_path = os.path.join(self.config_path, self.escenario_id, 'universo', self.last_selection)
            contenido = self.error_text.get(1.0, tk.END)
            try:
                with open(archivo_seleccionado_path, 'w') as file:
                    file.write(contenido)
                self.files_edited[self.last_selection] = True
                if all(self.files_edited.values()):
                    self.button.config(state=tk.NORMAL)
            except Exception as e:
                print(f"Error al guardar cambios en {archivo_seleccionado_path}: {e}")

    def populate_listbox(self):
        universo_dir = os.path.join(self.config_path, self.escenario_id, 'universo')
        if os.path.exists(universo_dir):
            files = os.listdir(universo_dir)
            for file in files:
                if os.path.isfile(os.path.join(universo_dir, file)):
                    self.listbox.insert(tk.END, file)
                    self.files_edited[file] = False

    def load_config_path(self):
        if not os.path.exists("rutas_configuracion.json"):
            raise FileNotFoundError("El archivo rutas_configuracion.json no existe.")
        with open('rutas_configuracion.json', 'r') as f:
            data = json.load(f)
        self.path = data.get('Ruta de Carpetas')
        if not self.path or not os.path.isdir(self.path):
            raise ValueError(f"Ruta de Carpetas no es válida: {self.path}")
        return self.path

    def create_scenario_directory(self, escenario_id):
        base_dir = os.path.join(self.config_path, escenario_id)
        os.makedirs(base_dir, exist_ok=True)

    def actualizar_columna_error(self, mensaje):
        """Actualiza la columna de error con el mensaje proporcionado."""
        self.escenario_id_label.config(text=mensaje)

    def eliminar_carpeta_erroneos(self):
        path_erroneos = os.path.join(self.config_path, self.escenario_id, 'erroneos')
        try:
            if os.path.exists(path_erroneos):
                for filename in os.listdir(path_erroneos):
                    file_path = os.path.join(path_erroneos, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                print(f"Contenido de 'erroneos' eliminado correctamente en {path_erroneos}.")
            else:
                print(f"La carpeta 'erroneos' no existe en {path_erroneos}, no se necesita acción.")
        except Exception as e:
            print(f"Error al intentar limpiar la carpeta 'erroneos': {e}")

    def execute_test(self):
        try:
            self.eliminar_carpeta_erroneos()
            entries = {
                'Escenario Id': tk.StringVar(value=self.escenario_id),
                'Quincena No.': tk.StringVar(value=self.quincena_no)
            }
            dropdown = tk.StringVar(value=self.registro_patronal_text)
            data_sender = DataSender()
            def dummy_mostrar_errores():
                print("Mostrar vista de errores llamada")
            data_sender.enviar_datos(entries, dropdown, self.config_path, dummy_mostrar_errores)
            self.actualizar_columna_errores_despues_del_test()

        except Exception as e:
            print("Error durante la ejecución del test:", e)
            self.actualizar_columna_error(f"Error durante la ejecución del test: {str(e)}")

    def actualizar_columna_errores_despues_del_test(self):
        path_erroneos = os.path.join(self.config_path, self.escenario_id, 'erroneos', 'errortimbrado.txt')
        if os.path.exists(path_erroneos):
            with open(path_erroneos, 'r') as file:
                errores = file.read().strip()
                if errores:
                    self.actualizar_columna_error(errores)
                else:
                    self.actualizar_columna_error("No se encontraron errores en errortimbrado.txt.")
                    self.cerrar_ventana()
        else:
            self.actualizar_columna_error("No se encontraron errores en errortimbrado.txt.")
            self.cerrar_ventana()

    def cerrar_ventana(self):
        self.master.destroy()

    def mostrar_vista_errores(self, num_rows_after_cleaning):
        if hasattr(self, 'new_window') and self.new_window.winfo_exists():
            return

        escenario_id = self.entries['Escenario Id'].get().strip()
        quincena_no = self.entries['Quincena No.'].get().strip()
        registro_patronal_text = self.dropdown.get().strip()
        registro_patronal = ''.join(re.findall(r'\d+', registro_patronal_text))

        self.new_window = tk.Toplevel(self.master)
        self.app = TableError(self.new_window, escenario_id, quincena_no, registro_patronal_text)
        window_x = self.master.winfo_x()
        window_y = self.master.winfo_y()
        self.new_window.geometry("+%d+%d" % (window_x, window_y))

    def list_directory_contents(self):
        base_dir = os.path.join(self.config_path, self.escenario_id)
        if os.path.exists(base_dir):
            print(f"Listando contenidos de la carpeta: {base_dir}")
            with os.scandir(base_dir) as entries:
                for entry in entries:
                    print(entry.name)
                    if entry.is_dir() and entry.name == 'erroneos':
                        erroneos_folder_exists = True


def main():
    root = tk.Tk()
    app = TableError(root, "escenario1", "quincena1", "registro1")
    root.mainloop()


if __name__ == "__main__":
    main()
