import streamlit as st

from  Simulate_mdm.IADS_Simulate import encode_w2x_map, decode_w2x_fields


def display_trame_raw(trame):
    st.subheader("Trame brute ")

    char_line = ''.join(f"<span style='display:inline-block;width:18px;text-align:center;'>{c}</span>" for c in trame)
    index_line = ''.join(f"<span style='display:inline-block;width:18px;text-align:center;font-size:10px;color:gray;'>{i % 100}</span>" for i in range(1, len(trame)+1))
    st.markdown(f"""
    <div style="font-family: monospace; white-space: nowrap; overflow-x: auto; padding: 6px; border: 1px solid #ccc; border-radius: 5px;">
      {char_line}<br>{index_line}
    </div>
    """, unsafe_allow_html=True)

def build_encoding_table(trame):
    st.subheader("Table d'encodage")
    w2x_map = encode_w2x_map(trame)
    table = []
    adresse_num = 1
    i = 6  # Index de départ dans la trame

    while i < len(trame):
        pair = trame[i:i + 2]
        if len(pair) < 2:
            break
        if all(c in [' ', ',', '*'] for c in pair):
            i += 2
            continue
        adresse = f"W2X{adresse_num:02d}"
        pos_str = f"{i + 1}-{i + 2}"
        table.append({
            "Adresse": adresse,
            "Position (dans trame)": pos_str,
            "Caractères": pair,
            "valeur encodé": w2x_map.get(adresse),
        })
        i += 2
        adresse_num += 1


    st.dataframe(table, use_container_width=True)


def build_decoding_table(trame):
    st.subheader(" Table de décodage")
    w2x_map = encode_w2x_map(trame)
    decoded = decode_w2x_fields(w2x_map)
    x946_metadata = {
        'X9460001': {'addr': 'W2X01', 'name': 'W2X Date Year'},
        'X9460002': {'addr': 'W2X02', 'name': 'W2X Date Month'},
        'X9460003': {'addr': 'W2X03', 'name': 'W2X Date Day'},
        'X9460004': {'addr': 'W2X04', 'name': 'W2X Date Hour'},
        'X9460005': {'addr': 'W2X05, W2X06', 'name': 'W2X Date Minute'},
        'X9460006': {'addr': 'W2X07', 'name': 'W2X Date Second'},
        'X9460007': {'addr': 'W2X08, W2X09, W2X10', 'name': 'W2X Wind Speed'},
        'X9460008': {'addr': 'W2X11, W2X12', 'name': 'W2X Wind Direction'},
        'X9460009': {'addr': 'W2X13, W2X14, W2X15', 'name': 'W2X Temperature'},
        'X9460010': {'addr': 'W2X16, W2X17', 'name': 'W2X Relative Humidity'},
        'X9460011': {'addr': 'W2X18, W2X19, W2X20, W2X21', 'name': 'W2X Un-Corr Pressure'},
        'X9460012': {'addr': 'W2X22, W2X23, W2X24', 'name': 'W2X Battery Voltage'},
        'X9460013': {'addr': 'W2X25, W2X26, W2X27, W2X28', 'name': 'W2X Aspirated Temp'},
        'X9460014': {'addr': 'W2X29', 'name': 'W2X Temp Status'},
        'X9460015': {'addr': 'W2X30 (High)', 'name': 'W2X WSS Status'},
        'X9460016': {'addr': 'W2X30 (Low)', 'name': 'W2X GPS Status'},
        'X9460017': {'addr': 'W2X31', 'name': 'W2X LOG Status'},
        'X9460018_VAR1': {'addr': 'Checksum 1', 'name': 'W2X Checksum-Sum 1'},
        'X9460018_VAR2': {'addr': 'Checksum 2', 'name': 'W2X Checksum-Sum 2'},
        'X9460018_VAR3': {'addr': '—', 'name': 'Checksum Validity (1/0)'},
    }

    table = []
    for key, info in x946_metadata.items():
        value = decoded.get(key, "—")
        table.append({
            "Champ X946": key,
            "titre du paramètre ": info["name"],
            "Adresse W2X utilisée": info["addr"],
            "Valeur décodée": value
        })

    st.dataframe(table, use_container_width=True)


def main():
    trame = st.session_state.get("selected_trame", None)
    if trame is None:
        st.warning("Aucune trame sélectionnée.")
        st.stop()

    st.title(" Visualisation de la trame W2X")

    if "selected_trame" in st.session_state:
        trame = st.session_state.selected_trame
    else:
        # Valeur par défaut
        st.switch_page("pages/main.py")

    display_trame_raw(trame)

    build_encoding_table(trame)

    build_decoding_table(trame)

main()




