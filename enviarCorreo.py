import csv
import json
import os
import shutil
import time
import xml.etree.ElementTree as ET
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class EnviarCorreo:
    def __init__(self):
        if os.path.exists("rutas_configuracion.json"):
            with open('rutas_configuracion.json', 'r') as f:
                data = json.load(f)

            print(data['Ruta de Carpetas'])
            self.path = data['Ruta de Carpetas']
            self.puerto = data['Puerto']
            self.host = data['Host']
            self.contrasena = data['password']
            self.correo = data['Correo']
        else:
            raise FileNotFoundError("El archivo 'rutas_configuracion.json' no existe.")

    def otro(self, escenario_id):
        if os.path.exists("escenario_ids.csv"):
            csv_file_pathd = os.path.abspath("escenario_ids.csv")
            print('existe', csv_file_pathd)
        else:
            print('no existe')
            return

        csv_file_path = csv_file_pathd
        try:
            if os.path.exists("rutas_configuracion.json"):
                with open('rutas_configuracion.json', 'r') as f:
                    data = json.load(f)

                print(data['Ruta de Carpetas'])
                self.path = data['Ruta de Carpetas']

            with open(csv_file_path, "r", newline='') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        escenario_id = row[0]

            if escenario_id is not None:
                full_path = os.path.join(self.path, escenario_id, 'timbrado')
                print("aaaaaaaaaaaaaaaaaaa", full_path)

                print("Contents of the directory:")
                for filename in os.listdir(full_path):
                    print(filename)

                procesados_path = os.path.join(full_path, 'procesados.txt')
                procesados2_path = os.path.join(full_path, 'procesados2.txt')
                universo_path = os.path.join(full_path, 'procesados_universo')
                os.makedirs(universo_path, exist_ok=True)
                universo_file_path = os.path.join(universo_path, 'procesados_universo.txt')

                # Leer y actualizar líneas de 'procesados.txt'
                with open(procesados_path, 'r') as file:
                    lines = file.readlines()

                with open(procesados_path, 'w') as file:
                    for line in lines:
                        if ", OK" not in line:
                            file.write(line.strip() + ", OK\n")
                        else:
                            file.write(line)

                # Copiar las líneas que no tienen 'OK' a 'procesados2.txt' y 'procesados_universo.txt'
                lines_to_copy = [line for line in lines if ", OK" not in line]
                with open(procesados2_path, 'w') as proc2_file:
                    proc2_file.writelines(lines_to_copy)
                with open(universo_file_path, 'w') as univ_file:
                    univ_file.writelines(lines_to_copy)

                print("Las líneas han sido actualizadas y movidas a 'procesados2.txt' y 'procesados_universo.txt'.")

                lines_to_keep = []
                with open(procesados2_path, 'r') as file:
                    for line in file:
                        line_without_ok = line.replace(", OK", "")
                        if line_without_ok.count('|') == 5:
                            last_field = line_without_ok.split('|')[-1].strip()
                            if re.match(r"[^@]+@[^@]+\.[^@]+", last_field):
                                print("Correct line:", line)
                                data = line_without_ok.split('|')
                                alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                for i, item in enumerate(data):
                                    print(f"{alphabet[i]}: {item}")
                                rfc = data[0]
                                nombre = data[1]
                                xmlPDF = data[3]
                                uuid = data[4]
                                
                                destino = data[5]
                                # Concatenar A y D
                                concatenated = rfc + xmlPDF
                                print("Concatenado A+D:", concatenated)
                                
                                # Verificar si existen archivos que empiecen con concatenated
                                matching_files = [f for f in os.listdir(full_path) if f.startswith(concatenated)]
                                if matching_files:
                                    print("Archivos encontrados que empiezan con", concatenated)
                                    for file in matching_files:
                                        print(file)
                                else:
                                    print("No se encontraron archivos que empiecen con", concatenated)

                                # Enviar notificación con archivos adjuntos
                                result = self.send_notification(destino, xmlPDF, rfc, nombre, uuid, full_path, matching_files)
                                print(result)
                                if ", OK" not in line:
                                    line = line.strip() + ", OK\n"
                            else:
                                print("Incorrect line (invalid email):", line)
                                lines_to_keep.append(line)
                        else:
                            print("Incorrect line (wrong number of pipes):", line)
                            lines_to_keep.append(line)

                with open(procesados2_path, 'w') as file:
                    file.writelines(lines_to_keep)
            else:
                print("No escenario_id found.")
        except FileNotFoundError as e:
            print("Error: El archivo no existe.", e)
        except Exception as e:
            print("Error desconocido:", e)

    def send_notification(self, destino, xml_pdf, rfc, nombre, uuid, full_path, attachments):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.correo
            msg['To'] = destino
            msg['CC'] = "rocencran@hotmail.com"
            msg['Subject'] = f"QNA 08 CFDI {xml_pdf} de {rfc} {nombre}"

            body = f"""Estimado colaborador

Por medio de este conducto realizamos el envío del comprobante fiscal digital {xml_pdf} de su recibo de nómina.

COLEGIO NACIONAL DE EDUCACION PROFESIONAL TECNICA"""
            msg.attach(MIMEText(body, 'plain'))

            for file in attachments:
                file_path = os.path.join(full_path, file)
                if os.path.exists(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
                    msg.attach(part)

            server = smtplib.SMTP(self.host, self.puerto)
            server.starttls()
            server.login(self.correo, self.contrasena)
            text = msg.as_string()
            server.sendmail(self.correo, destino, text)
            time.sleep(2)
            server.quit()
            return "Ok"
        except Exception as e:
            return f"Error: {str(e)}"

