import os
import subprocess
import re
import time
from datetime import datetime


def log_security_events(event):
    """Registra eventi di sicurezza in un file di log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("wifi_security.log", "a") as f:
        f.write(f"{timestamp}: {event}\n")


def get_connected_devices():
    """Lista dispositivi connessi tramite ARP"""
    try:
        print("Cerco dispositivi connessi...")
        devices = subprocess.check_output("arp -a", shell=True).decode()
        print("Dispositivi connessi:\n", devices)
    except Exception as e:
        print("Errore ricerca dispositivi:", e)


def change_wifi_password(ssid, new_password):
    """Aggiorna password WiFi"""
    print(f"Accedi al pannello admin del router per cambiare la password della rete: {ssid}")
    print(f"Imposta la password: {new_password}")


def block_device(mac_address):
    """Blocca dispositivo tramite MAC address"""
    try:
        print(f"Blocco dispositivo {mac_address}...")
        command = f"netsh wlan block allowmac={mac_address}"
        os.system(command)
        print(f"Dispositivo {mac_address} bloccato.")
    except Exception as e:
        print("Errore blocco dispositivo:", e)


def scan_network():
    """Scansiona rete con ping"""
    try:
        print("Scansione rete in corso...")
        base_ip = "192.168.1."
        active_hosts = []

        for i in range(1, 255):
            ip = base_ip + str(i)
            response = os.system(f"ping -c 1 -W 1 {ip} > /dev/null 2>&1")
            if response == 0:
                active_hosts.append(ip)
                print(f"Host attivo: {ip}")

        print(f"\nTotale host attivi: {len(active_hosts)}")
        log_security_events(f"Scansione completata - {len(active_hosts)} host")
    except Exception as e:
        print(f"Errore scansione: {e}")


def monitor_bandwidth(duration=60):
    """Monitora traffico di rete"""
    try:
        print(f"Monitoraggio traffico per {duration} secondi...")

        wifi_info = subprocess.check_output("networksetup -listallhardwareports", shell=True).decode()
        wifi_device = None
        for line in wifi_info.split('\n'):
            if 'Wi-Fi' in line:
                wifi_device = line.split()[-1]
                break

        if not wifi_device:
            print("Interfaccia Wi-Fi non trovata")
            return

        command = f"netstat -I {wifi_device} -w {duration}"
        result = subprocess.check_output(command, shell=True).decode()
        lines = result.split('\n')[1:-1]

        if len(lines) >= 2:
            start = lines[0].split()
            end = lines[-1].split()
            in_pkts = int(end[4]) - int(start[4])
            out_pkts = int(end[6]) - int(start[6])

            print(f"\nPacchetti in entrata: {in_pkts}/s")
            print(f"Pacchetti in uscita: {out_pkts}/s")

        log_security_events("Monitoraggio completato")
    except Exception as e:
        print(f"Errore monitoraggio: {e}")


def check_wifi_encryption():
    """Verifica crittografia WiFi"""
    try:
        # Ottieni info rete WiFi corrente
        wifi_info = subprocess.check_output("networksetup -getairportnetwork en0", shell=True).decode()

        # Ottieni dettagli sulla sicurezza
        command = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
        details = subprocess.check_output(command, shell=True).decode()

        # Analizza tipo di sicurezza
        if "WPA3" in details:
            print("Crittografia: WPA3 (Ottimale)")
        elif "WPA2" in details:
            print("Crittografia: WPA2 - Upgrade a WPA3 consigliato")
        elif "WPA" in details:
            print("ATTENZIONE: WPA - Sicurezza debole")
        elif "WEP" in details:
            print("ATTENZIONE: WEP - Sicurezza molto debole")
        else:
            print("ATTENZIONE: Rete aperta o crittografia non riconosciuta")

        log_security_events("Verifica crittografia completata")

    except Exception as e:
        print("Errore verifica crittografia:", e)


def scan_wifi_networks():
    try:
        print("Scansione reti WiFi...")
        # Modifica per macOS
        networks = subprocess.check_output("networksetup -listpreferredwirelessnetworks en0", shell=True).decode()

        print("\nReti WiFi trovate:")
        for line in networks.split('\n')[1:]:  # Salta l'intestazione
            if line.strip():
                print(f"SSID: {line.strip()}")

        log_security_events("Scansione WiFi completata")

    except Exception as e:
        print(f"Errore scansione WiFi: {e}")


def secure_wifi():
    """Menu principale"""
    print("Tool Sicurezza Wi-Fi v2.0\n")

    while True:
        print("\nOpzioni:")
        print("1. Scansiona dispositivi")
        print("2. Cambia password")
        print("3. Blocca dispositivo")
        print("4. Scansiona rete")
        print("5. Monitora banda")
        print("6. Verifica crittografia")
        print("7. Visualizza log")
        print("8. Scansiona reti WiFi")
        print("9. Esci")

        choice = input("\nScegli opzione (1-9): ")

        if choice == "1":
            get_connected_devices()
        elif choice == "2":
            ssid = input("SSID WiFi: ")
            new_password = input("Nuova password: ")
            change_wifi_password(ssid, new_password)
        elif choice == "3":
            mac = input("MAC address da bloccare: ")
            block_device(mac)
        elif choice == "4":
            scan_network()
        elif choice == "5":
            duration = int(input("Durata monitoraggio (secondi): "))
            monitor_bandwidth(duration)
        elif choice == "6":
            check_wifi_encryption()
        elif choice == "7":
            try:
                with open("wifi_security.log", "r") as f:
                    print(f.read())
            except:
                print("Nessun log trovato")
        elif choice == "8":
            scan_wifi_networks()
        elif choice == "9":
            print("Uscita...")
            break
        else:
            print("Opzione non valida")

        log_security_events(f"Operazione: {choice}")


if __name__ == "__main__":
    secure_wifi()