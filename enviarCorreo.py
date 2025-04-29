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

            # Procesar líneas una por una
            for i, line in enumerate(lines):
                if ", OK" in line:
                    continue  # Saltar líneas que ya tienen OK

                line = line.strip()
                if line.count('|') == 5:
                    data = line.split('|')
                    if re.match(r"[^@]+@[^@]+\.[^@]+", data[5].strip()):
                        print(f"\nProcesando línea {i + 1}:", line)
                        rfc = data[0].strip()
                        nombre = data[1].strip()
                        xmlPDF = data[3].strip()
                        uuid = data[4].strip()
                        destino = data[5].strip()
                        concatenated = rfc + xmlPDF

                        matching_files = [f for f in os.listdir(full_path) if f.startswith(concatenated)]
                        if matching_files:
                            print("Archivos encontrados:", matching_files)
                            result = self.send_notification(destino, xmlPDF, rfc, nombre, uuid, full_path, matching_files, quincena_no)
                            
                            if result == "Ok":
                                print("Correo enviado exitosamente. Actualizando archivos...")
                                # Actualizar la línea en la lista principal
                                lines[i] = line + ", OK\n"
                                
                                # Actualizar procesados.txt inmediatamente
                                with open(procesados_path, 'w', encoding='utf-8') as file:
                                    file.writelines(lines)
                                
                                # Actualizar procesados2.txt sin la línea que acabamos de procesar
                                remaining_lines = [l for l in lines if ", OK" not in l]
                                with open(procesados2_path, 'w', encoding='utf-8') as file:
                                    file.writelines(remaining_lines)
                                
                                print("Archivos actualizados correctamente.")
                                time.sleep(2)  # Pequeña pausa entre correos
                            else:
                                print(f"Error al enviar correo: {result}")
                        else:
                            print(f"No se encontraron archivos que empiecen con {concatenated}")
                    else:
                        print(f"Email inválido en línea: {line}")
                else:
                    print(f"Formato de línea inválido: {line}")

        except FileNotFoundError as e:
            print("Error: El archivo no existe.", e)
        except Exception as e:
            print("Error desconocido:", e)
            raise

    def send_notification(self, destino, xml_pdf, rfc, nombre, uuid, full_path, attachments, quincena_no):
        try:
            print("\nIntentando enviar correo...")
            print(f"De: {self.correo}")
            print(f"Para: {destino}")
            print(f"Asunto: QNA {quincena_no} CFDI {xml_pdf} de {rfc} {nombre}")

            msg = MIMEMultipart()
            msg['From'] = self.correo
            msg['To'] = destino
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
            server.login(self.correo, self.contrasena)
            print("Inicio de sesión SMTP exitoso")
            
            text = msg.as_string()
            recipients = [destino]
            server.sendmail(self.correo, recipients, text)
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