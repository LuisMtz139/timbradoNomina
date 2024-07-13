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
            with open('rutas_configuracion.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            print("Ruta de Carpetas:", data['Ruta de Carpetas'])
            self.path = data['Ruta de Carpetas']
            self.puerto = data['Puerto']
            self.host = data['Host']
            self.contrasena = data['password']
            self.correo = data['Correo']
        else:
            raise FileNotFoundError("El archivo 'rutas_configuracion.json' no existe.")

    def otro(self, escenario_id, quincena_no):
        if not os.path.exists("escenario_ids.csv"):
            print('No existe el archivo escenario_ids.csv')
            return

        csv_file_path = os.path.abspath("escenario_ids.csv")
        print('Ruta del archivo CSV:', csv_file_path)

        try:
            with open(csv_file_path, "r", newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == escenario_id:
                        print(f"Escenario ID encontrado en CSV: {escenario_id}")
                        break
                else:
                    print(f"Escenario ID no encontrado en CSV: {escenario_id}")
                    return

            full_path = os.path.join(self.path, escenario_id, 'timbrado')
            print("Ruta completa del escenario:", full_path)

            if not os.path.exists(full_path):
                print(f"No existe la carpeta del escenario: {full_path}")
                return

            print("Contenidos de la carpeta del escenario:")
            for filename in os.listdir(full_path):
                print(filename)

            procesados_path = os.path.join(full_path, 'procesados.txt')
            procesados2_path = os.path.join(full_path, 'procesados2.txt')
            universo_path = os.path.join(full_path, 'procesados_universo')
            os.makedirs(universo_path, exist_ok=True)
            universo_file_path = os.path.join(universo_path, 'procesados_universo.txt')

            # Leer las líneas de 'procesados.txt'
            with open(procesados_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Copiar las líneas que no tienen 'OK' a 'procesados2.txt' y 'procesados_universo.txt'
            lines_to_copy = [line for line in lines if ", OK" not in line]
            with open(procesados2_path, 'w', encoding='utf-8') as proc2_file:
                proc2_file.writelines(lines_to_copy)
            with open(universo_file_path, 'w', encoding='utf-8') as univ_file:
                univ_file.writelines(lines_to_copy)

            print("Las líneas han sido movidas a 'procesados2.txt' y 'procesados_universo.txt'.")

            lines_to_keep = []
            for line in lines_to_copy:
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

                        matching_files = [f for f in os.listdir(full_path) if f.startswith(concatenated)]
                        if matching_files:
                            print("Archivos encontrados que empiezan con", concatenated)
                            for file in matching_files:
                                print(file)
                            # Enviar notificación con archivos adjuntos
                            print("Intentando enviar notificación...")
                            result = self.send_notification(destino, xmlPDF, rfc, nombre, uuid, full_path, matching_files, quincena_no)
                            if result == "Ok":
                                line = line.strip() + ", OK\n"
                        else:
                            print("No se encontraron archivos que empiecen con", concatenated)

                        if ", OK" not in line:
                            lines_to_keep.append(line)
                    else:
                        print("Incorrect line (invalid email):", line)
                        lines_to_keep.append(line)
                else:
                    print("Incorrect line (wrong number of pipes):", line)
                    lines_to_keep.append(line)

            with open(procesados2_path, 'w', encoding='utf-8') as file:
                file.writelines(lines_to_keep)
                
            # Actualizar procesados.txt con las líneas que ahora contienen ', OK'
            with open(procesados_path, 'w', encoding='utf-8') as file:
                for line in lines:
                    if line in lines_to_copy:
                        if line in lines_to_keep:
                            file.write(line)
                        else:
                            file.write(line.strip() + ", OK\n")
                    else:
                        file.write(line)

        except FileNotFoundError as e:
            print("Error: El archivo no existe.", e)
        except Exception as e:
            print("Error desconocido:", e)

    def send_notification(self, destino, xml_pdf, rfc, nombre, uuid, full_path, attachments, quincena_no):
        try:
            print("Intentando enviar correo...")
            print(f"De: {self.correo}")
            print(f"Para: {destino}")
            print(f"CC: rocencran@hotmail.com")
            print(f"Asunto: QNA {quincena_no} CFDI {xml_pdf} de {rfc} {nombre}")

            msg = MIMEMultipart()
            msg['From'] = self.correo
            msg['To'] = destino
            msg['CC'] = "rocencran@hotmail.com"
            msg['Subject'] = f"QNA {quincena_no} CFDI {xml_pdf} de {rfc} {nombre}"

            body = f"""Estimado colaborador

Por medio de este conducto realizamos el envío del comprobante fiscal digital {xml_pdf} de su recibo de nómina.

COLEGIO NACIONAL DE EDUCACION PROFESIONAL TECNICA"""
            msg.attach(MIMEText(body, 'plain'))

            print(f"Archivos a adjuntar: {attachments}")

            for file in attachments:
                file_path = os.path.join(full_path, file)
                if os.path.exists(file_path):
                    print(f"Adjuntando archivo: {file_path}")
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
                    msg.attach(part)
                else:
                    print(f"Archivo no encontrado: {file_path}")

            print("Conectando al servidor SMTP...")
            server = smtplib.SMTP(self.host, self.puerto)
            server.starttls()
            print(f"Conectado al servidor SMTP: {self.host}:{self.puerto}")
            server.login(self.correo, self.contrasena)
            print("Inicio de sesión SMTP exitoso")
            text = msg.as_string()
            print("Enviando correo a:", destino)
            server.sendmail(self.correo, destino, text)
            time.sleep(3)
            server.quit()
            print("Correo enviado con éxito.")
            return "Ok"
        except smtplib.SMTPException as e:
            print(f"Error SMTP al enviar el correo: {str(e)}")
            return f"Error SMTP: {str(e)}"
        except Exception as e:
            print(f"Error general al enviar el correo: {str(e)}")
            return f"Error: {str(e)}"
