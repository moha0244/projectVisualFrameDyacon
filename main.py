import re

import streamlit as st
import pandas as pd
from datetime import datetime
from Simulate_mdm.formatage_trame import (
    format_date, format_time, format_wind, format_temperature,
    format_humidity, format_pressure, format_battery,
    compute_status, calculate_checksum,
    get_status_temp, get_status_wss, get_status_gps
)

def build_trame(horloge, meteo, storage):
    frame = "W2X,  "
    frame += format_date(horloge['year'], horloge['month'], horloge['day']) + ", "
    frame += format_time(horloge['hour'], horloge['minute'], horloge['second']) + ", "
    frame += format_wind(meteo['windSpeed'], meteo['windDir']) + ", "
    frame += format_temperature(meteo['temperature']) + ", "
    frame += format_humidity(meteo['humidity']) + ", "
    frame += format_pressure(meteo['pressure']) + ", "
    frame += format_battery(meteo['battery']) + ", "
    frame += format_temperature(meteo['temperature']) + ", "
    frame += compute_status(meteo['statusTemp'], meteo['statusWss'], horloge['statusGPS'], storage['statusLog']) + ", "
    return f"{frame}*{calculate_checksum(frame)}"


def saisie_manuelle():
    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("L'année", value=datetime.now().year)
        month = st.number_input("Le mois", value=datetime.now().month)
        day = st.number_input("Le jour", value=datetime.now().day)
        windSpeed = st.number_input("Vitesse du vent", value=12.3)
        temperature = st.number_input("Température", value=23.7)
        pressure = st.number_input("Pression (mbar)", value=1013.25)
        battery = st.number_input("Batterie (V)", value=11.9)
    with col2:
        hour = st.number_input("L'heure", value=datetime.now().hour)
        minute = st.number_input("La minute", value=datetime.now().minute)
        second = st.number_input("La seconde", value=datetime.now().second)
        windDir = st.number_input("Direction du vent", value=80)
        humidity = st.number_input("Humidité (%)", value=41)
        statusLog = st.text_input("Code statut log", value="0")

    horloge = {
        'year': year, 'month': month, 'day': day,
        'hour': hour, 'minute': minute, 'second': second,
        'statusGPS': get_status_gps(hour, minute, second, True)
    }
    meteo = {
        'windSpeed': windSpeed, 'windDir': windDir,
        'temperature': temperature, 'humidity': humidity,
        'pressure': pressure, 'battery': battery,
        'statusTemp': get_status_temp(temperature),
        'statusWss': get_status_wss(temperature, windSpeed, pressure, humidity, battery)
    }
    storage = {'statusLog': statusLog}

    return [build_trame(horloge, meteo, storage)]

def charger_csv():
    trames = []
    uploaded_csv = st.file_uploader("Importer un CSV", type=["csv"])
    if uploaded_csv:
        df = pd.read_csv(uploaded_csv)
        st.dataframe(df)
        for _, row in df.iterrows():
            now = datetime.now()
            horloge = {
                'year': 2000, 'month': now.month, 'day': now.day,
                'hour': now.hour, 'minute': now.minute, 'second': now.second,
                'statusGPS': '0'
            }
            meteo = {
                'windSpeed': row['windSpeed'], 'windDir': row['windDir'],
                'temperature': row['temperature'], 'humidity': row['humidity'],
                'pressure': row['pressure'], 'battery': row['battery'],
                'statusTemp': row.get('statusTemp', '0'),
                'statusWss': row.get('statusWss', '1'),
            }
            storage = {'statusLog': '0'}
            trames.append(build_trame(horloge, meteo, storage))
    return trames


def valider_trames_w2x(lines):
    """
    Valide les trames en utilisant une expression régulière stricte.
    Retourne les trames valides et les erreurs.
    """
    w2x_pattern = re.compile(
        r"^W2X,\s{2}\d{6},\s\d{2}:\d{2}:\d{2},\s\d{3}\.\d,\s\d{3},\s[+-]\d{4}\.\d,\s\d{3},\s\d{2}\.\d{2},\s\d{3}\.\d,\s[+-]\d{4}\.\d,\s[A-Z0-9]{4},\s?\*\d+$"
    )

    trames_valides = []
    erreurs = []

    for i, line in enumerate(lines):
        if w2x_pattern.match(line):
            trames_valides.append(line)
        else:
            erreurs.append((i + 1, line))

    return trames_valides, erreurs

def charger_ou_coller_trames():
    mode = st.radio("Méthode d'entrée :", ["Charger un fichier .txt", "Coller manuellement les trames"])

    lignes = []

    if mode == "Charger un fichier .txt":
        uploaded_txt = st.file_uploader("Importer un fichier texte", type=["txt"])
        if uploaded_txt:
            lignes = [line.decode('utf-8').strip() for line in uploaded_txt.readlines() if line.strip()]
    else:
        texte = st.text_area("Collez ici une ou plusieurs trames W2X (une par ligne)", height=200)
        if texte:
            lignes = [line.strip() for line in texte.split("\n") if line.strip()]

    if lignes:
        trames_valides, erreurs = valider_trames_w2x(lignes)

        if erreurs:
            st.error("Trames mal formatées :")
            for ligne, contenu in erreurs:
                st.code(f"Ligne {ligne} : {contenu}")
            return []

        st.success(f"{len(trames_valides)} trames valides chargées.")
        return trames_valides

    return []



def GUI():
    st.title("Générateur / Chargeur de trames W2X")

    option = st.radio("Choisissez une méthode :", ["Saisie manuelle", "Charger un fichier CSV", "Charger un fichier TXT avec trames"])
    trames = []

    if option == "Saisie manuelle":
        st.subheader("Entrée manuelle des données")
        trames = saisie_manuelle()

    elif option == "Charger un fichier CSV":
        st.subheader("Charger un fichier CSV contenant les colonnes météo")
        trames = charger_csv()

    elif option == "Charger un fichier TXT avec trames":
        st.subheader("Importer un fichier texte contenant des trames W2X")
        trames = charger_ou_coller_trames()

    if trames:
        st.subheader("Trames générées ou chargées")
        df = pd.DataFrame({"Index": list(range(len(trames))), "Trame": trames})
        st.dataframe(df, use_container_width=True)

        index = st.number_input("Choisir une trame à visualiser :", min_value=0, max_value=len(trames)-1, step=1)
        if st.button("Visualiser la trame sélectionnée"):
            st.session_state.selected_trame = trames[index]
            st.switch_page("pages/frameinfo.py")

# Appel principal
GUI()
