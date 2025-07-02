import serial
import serial.tools.list_ports
import time

def receive_from_serial():
    ports = serial.tools.list_ports.comports()
    print("Ports disponibles :")
    for i, p in enumerate(ports):
        print(f"{i}: {p.device} - {p.description}")

    idx = int(input("Choisir le port pour la réception (index) : "))
    port = ports[idx].device

    ser = serial.Serial(port=port, baudrate=9600, parity='N', stopbits=1, bytesize=8, timeout=1)
    print(f"Ouverture du port de réception {port}...")

    try:
        while True:

            line = ser.readline()
            if line:
                print(f"Echo reçu : {line}")
            else:
                print("echo not working")

            data = ser.read(100)  # Lis jusqu'à 100 octets
            if data:
                print("Reçu :", data)
                print("Reçu (hexa) :", [hex(b) for b in data])
            else:
                print("rien reçu")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Arrêt manuel.")
    finally:
        ser.close()

receive_from_serial()