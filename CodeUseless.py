import serial
import pymodbus
from pymodbus.client import ModbusSerialClient
import serial.tools.list_ports
import csv
import tkinter as tk
import time
from datetime import datetime
import struct
import socket
from tkinter import filedialog, messagebox


def testSendBrut():
   ser = serial.Serial(
       port='COM4',
       baudrate=9600,
       bytesize=8,
       parity='N',
       stopbits=1,
       timeout=1
   )


   # Trame Modbus RTU exemple (lecture registres)
   test_frame = bytes.fromhex("01 04 00 DE 00 03 F1 35")  # Adresse 1, fonction 04, registre 222


   try:

       for port in serial.tools.list_ports.comports():
           print(port.device, port.description)
       print("Envoi de la trame:", test_frame.hex())
       ser.write(test_frame)


       # Lecture de la réponse (doit renvoyer la même trame en bouclage)
       response = ser.read(8)
       print(ser)
       print("Réponse reçue:", response.hex() if response else "Aucune réponse")


   except Exception as e:
       print("Erreur:", e)
   finally:
       ser.close()

def testAllRegisterAndSlaveAdress():
    client = ModbusSerialClient(
        port='COM4',
        baudrate=9600,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1
    )

    if client.connect():
        print(" Début du scan des registres (0 à 300)...")
        for reg in range(0, 301):
            try:
                result = client.read_input_registers(address=reg, count=1, slave=1)
                if not result.isError():
                    print(
                        f"Réponse : registre: {reg}, valeur: {result.registers[0]}")
            except Exception as e:
                pass
        client.close()
        print("Scan terminé.")
    else:
        print(" Impossible de se connecter au port COM")

def read_registers(client, address, count, slave=1, scale=10.0):
    result = client.read_input_registers(address=address, count=count, slave=slave)
    return [register / scale for register in result.registers] if not result.isError() else None

def read_registers_status(client, address, count, name, slave=1):
    result = client.read_input_registers(address=address, count=count, slave=slave)
    return ["senseur pour " +name + " connecté" if status!=-1 else "pas de senseur pour " + name for status in result.registers] if not result.isError() else None

def read_registers_date(client, address, count, slave=1):
    result = client.read_input_registers(address=address, count=count, slave=slave)

    return [(register[0] << 16) | register[1] for register in result.registers] if not result.isError() else None

def getInfosOfCM1ToCSV():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Save CSV file",
        initialfile="cm1_data.csv"
    )

    if not file_path:
        print("Enregistrement annulé.")
        return

    client = ModbusSerialClient(
        port='COM3',
        baudrate=9600,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1
    )

    if not client.connect():
        print("Connexion échouée, branchez votre port!!")
        return

    try:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Horodatage",
                "Température (°C)", "Humidité (%)", "Pression (hPa)",
                "Vitesse Vent (m/s)", "Direction Vent (°)",
                "Rafale Vent (m/s)", "Direction Rafale (°)",
                "Taux de pluie (mm/h)", "Batterie (volts)",
                "statut du senseur de la température", "statut du senseur du vent",
            ])

            start_time = time.time()
            while time.time() - start_time < 50:
                now = time.strftime("%Y-%m-%d %H:%M:%S")

                tph = read_registers(client, 221, 3)
                wind = read_registers(client, 201, 2)
                gust = read_registers(client, 207, 2)
                rain = read_registers(client, 243, 1)
                battery = read_registers(client, 108, 1, 1, 1000)
                status_temperature = read_registers_status(client, 220, 1, "TPH")
                status_wind = read_registers_status(client, 200, 1, "Wind")
                """status_WSS =  read_registers_status(client, 200, 1, "WSS")
                status_GPS=  read_registers_status(client, 200, 1, "GPS")"""

                if tph and wind and gust and rain and battery and status_temperature and status_wind:
                    writer.writerow([
                        now,
                        tph[0], tph[1], tph[2],
                        wind[0], wind[1],
                        gust[0], gust[1],
                        rain[0],battery[0],
                        status_temperature[0], status_wind[0],
                    ])
                    print(f"[{now}] Données enregistrées!!")
                else:
                    print(f"[{now}] Une ou plusieurs lectures ont échoué!!")


        print(f"Données enregistrées dans : {file_path}")

    except KeyboardInterrupt:
        print("\nVous avez effectué un arret manuel. Enregistrement incomplet!!!!")

    finally:
        client.close()

def round_value(value, width, decimals=None):
    """
    Formate une valeur avec un nombre minimal de chiffres (zéros devant).
    """
    if decimals is not None:
        abs_val = abs(value)
        format_str = f"{{:.{decimals}f}}"
        val_str = format_str.format(round(abs_val, decimals))
    else:
        val_str = str(int(value))

    while len(val_str) < width:
        val_str = "0" + val_str

    return val_str

def send_hex_variant(ser, data):
    value = data['wd']  # 262
    byte1 = (value >> 8) & 0xFF  # 0x01
    byte2 = value & 0xFF         # 0x06
    hex_bytes = bytes([byte1, byte2])  # b'\x01\x06'
    ser.write(hex_bytes)
    print("[HEX] ", hex_bytes.hex())  # Affiche "0106"


def send_binary_structured(ser, data):
    print(">> Envoi en BINAIRE structuré")
    frame = struct.pack(
        "<2s6B6Bfffff",
        b"WX",
        int(data["ts"].strftime("%y")), data["ts"].month, data["ts"].day,
        data["ts"].hour, data["ts"].minute, data["ts"].second,
        data["ws"], data["wd"], data["temp"], data["bp"], data["batt"]
    )
    ser.write(frame)
    print("[BIN] ", frame.hex())
    time.sleep(1)

def generate_ascii_variants(base):
    endings = ["\n", "\r", "\r\n", ""]
    delimiters = [",", ";", "|"]
    variants = []

    for end in endings:
        for delim in delimiters:
            frame = base.replace(",", delim) + end
            variants.append(frame)
    return variants



def send_ascii_variants(ser, data):
    print(">> Envoi des variantes ASCII")
    base_frame = f"W2X, {data['date_str']}, {data['time_str']}, {data['ws']:.1f}, {data['wd']}, {data['temp']:+.1f}, {data['rh']}, {data['bp']:.2f}, {data['batt']:.1f}, {data['asp_temp']}, {data['status']}"
    variants = generate_ascii_variants(base_frame)

    for i, frame in enumerate(variants):
        checksum = sum(ord(c) for c in frame[:76])
        frame_final = frame.strip() + f", *{checksum}" + frame[len(frame.strip()):]
        ser.write(frame_final.encode())
        print(f"[ASCII {i+1}/{len(variants)}] {repr(frame_final)}")
        time.sleep(1)


def send_csv_to_modem_all_formats():
    try:
        ports = serial.tools.list_ports.comports()
        print("Ports disponibles :")
        for i, p in enumerate(ports):
            print(f"{i}: {p.device} - {p.description}")

        idx = int(input("Choisir le port pour l'envoi (index) : "))
        port = ports[idx].device

        ser = serial.Serial(port=port, baudrate=9600, parity='N', stopbits=1, timeout=1)
        print(f"Connexion au modem ouverte sur {port}")

        with open("cm1_data.csv", mode="r", encoding="latin1") as file:
            reader = csv.DictReader(file)
            row = next(reader)

            # Simulation de trame courte à 4 octets pour test
            # Exemple simple : @01A + \r
            while True:
                msg = "@01A".encode('ascii')  # 4 octets ASCII (sans \r)
                ser.write(msg)
                print(f"Trame envoyée ({len(msg)} octets) : {msg}")

        ser.close()
        print("Transmission terminée.")

    except KeyboardInterrupt:
        print("\nArrêt manuel.")
        ser.close()

    except Exception as e:
        print("Erreur :", e)


def receive_from_modem():
    try:
        # Lister les ports disponibles
        ports = serial.tools.list_ports.comports()
        print("Ports disponibles :")
        for i, p in enumerate(ports):
            print(f"{i}: {p.device} - {p.description}")

        # Sélectionner le port
        idx = int(input("Choisir le port pour la réception (index) : "))
        port = ports[idx].device

        # Configurer la connexion série
        ser = serial.Serial(port=port, baudrate=9600, parity='N', stopbits=1, timeout=1)
        print(f"En écoute sur {port}...")

        while True:
            # Lire une ligne depuis le port série
            line = ser.readline().decode('ascii', errors='ignore').strip()

            if line:  # Si des données ont été reçues
                print("Trame reçue:", line)

                # Vérifier le checksum si présent
                if '*' in line:
                    data_part, checksum_part = line.rsplit('*', 1)
                    calculated_checksum = sum(ord(c) for c in data_part[:76])
                    received_checksum = checksum_part.strip()

                    try:
                        if int(received_checksum) == calculated_checksum:
                            print("Checksum valide")
                        else:
                            print(f"Checksum invalide (reçu: {received_checksum}, calculé: {calculated_checksum})")
                    except ValueError:
                        print("Format de checksum invalide")

    except KeyboardInterrupt:
        print("\nRéception interrompue par l'utilisateur")
    except Exception as e:
        print("Erreur:", e)
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Connexion série fermée")


def receive_csv_over_serial():
    try:
        ports = serial.tools.list_ports.comports()
        print("Ports disponibles :")
        for i, p in enumerate(ports):
            print(f"{i}: {p.device} - {p.description}")

        idx = int(input("Choisir le port pour l'envoi (index) : "))
        port = ports[idx].device

        with serial.Serial(port, 9600, timeout=1) as ser:
            print(f"Connecté au port série {port} à {9600} bauds.")
            buffer = b''

            while True:
                data = ser.read(1024)  # lecture par bloc
                if not data:
                    continue  # timeout, on attend encore
                buffer += data

                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    print(line.decode('ascii', errors='replace').strip())

    except serial.SerialException as e:
        print(f"Erreur de port série : {e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

def loopback_test():
    try:
        ports = serial.tools.list_ports.comports()
        print("Ports disponibles :")
        for i, p in enumerate(ports):
            print(f"{i}: {p.device} - {p.description}")

        idx = int(input("Choisir le port (index) : "))
        port = ports[idx].device

        ser = serial.Serial(
            port=port,
            baudrate=9600,
            parity='N',
            stopbits=1,
            timeout=1,
            write_timeout=1,
            rtscts=False,
            dsrdtr=False
        )

        print(f"Connexion ouverte sur {port}")
        i=0
        while (i<100):

            msg = "@01A\r".encode('ascii')  # trame à envoyer
            print(f"Envoi : {msg}")
            ser.write(msg)

            time.sleep(0.1)  # pause pour laisser le temps au message de revenir

            received = ser.read(len(msg))  # lire le même nombre d’octets qu’envoyé
            print(f"Reçu : {received}")

            if received == msg:
                print(" Loopback OK : trame reçue identique")
            else:
                print(" Trame différente ou rien reçu")
            i+=1

        ser.close()

    except Exception as e:
        print("Erreur :", e)