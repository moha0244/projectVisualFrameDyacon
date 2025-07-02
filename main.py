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
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode





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


def input_number(name, key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.number_input(name, value=st.session_state[key], key=key)

def input_text(name, key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.text_input(name, value=st.session_state[key], key=key)

def saisie_manuelle():
    col1, col2 = st.columns(2)
    with col1:
        year = input_number("L'année", "year", datetime.now().year)
        month = input_number("Le mois", "month", datetime.now().month)
        day = input_number("Le jour", "day", datetime.now().day)
        windSpeed = input_number("Vitesse du vent", "windSpeed", 12.3)
        temperature = input_number("Température", "temperature", 23.7)
        pressure = input_number("Pression (mbar)", "pressure", 1013.25)
        battery = input_number("Batterie (V)", "battery", 11.9)

    with col2:
        hour = input_number("L'heure", "hour", datetime.now().hour)
        minute = input_number("La minute", "minute", datetime.now().minute)
        second = input_number("La seconde", "second", datetime.now().second)
        windDir = input_number("Direction du vent", "windDir", 80)
        humidity = input_number("Humidité (%)", "humidity", 41)
        statusLog = input_text("Code statut log", "statusLog", "0")


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
        r"^W2X,\s{2}"  # W2X, avec 2 espaces
        r"\d{6},\s"  # Date YYMMDD
        r"\d{2}:\d{2}:\d{2},\s"  # Heure HH:MM:SS
        r"\d{3}\.\d,\s"  # Vitesse vent 001.8
        r"\d{3},\s"  # Direction 080
        r"[+-]\d{3}\.\d,\s"  # Température +023.7
        r"\d{3},\s"  # Humidité 041
        r"\d{3}\.\d{2},\s"  # Pression 028.61
        r"\d{2}\.\d,\s"  # Batterie 11.9
        r"[+-]\d{3}\.\d,\s"  # Temp. aspirée +023.6
        r"[A-Z0-9]{4},\s?"  # Statuts A010,
        r"\*\d+$"  # Checksum *3347
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
        if st.button("Charger le fichier texte") and texte :
            lignes = [line.strip() for line in texte.split("\n") if line.strip()]


    if lignes:
        trames_valides, erreurs = valider_trames_w2x(lignes)

        if erreurs:
            st.error("Trames mal formatées :")
            for ligne, contenu in erreurs:
                st.error(f"Ligne {ligne} : {contenu}")
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
        st.subheader("Importer/coller un fichier texte contenant des trames W2X")
        trames = charger_ou_coller_trames()

    if trames:
        st.session_state.trames = trames

    if st.session_state.trames:
        st.subheader("Trames générées ou chargées")

        df = pd.DataFrame({
            "Index": list(range(len(st.session_state.trames))),
            "Trame": st.session_state.trames
        })

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection("single")  # une seule ligne sélectionnable
        grid_options = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            theme="streamlit",
            height=300
        )

        selected_rows = grid_response['selected_rows']

        print(selected_rows)

        if selected_rows is not None and len(selected_rows) > 0:
            selected_trame = selected_rows.iloc[0]['Trame']
            st.session_state.selected_trame = selected_trame
            st.switch_page("pages/frameinfo.py")



# Appel principal
GUI()
