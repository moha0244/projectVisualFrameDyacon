def encode_w2x_map(trame):
    w2x_map = {}
    adresse_num = 1
    for i in range(6, len(trame), 2):
        pair = trame[i:i+2]
        if all(c in [' ', ',', "*"] for c in pair):
            continue
        adresse = f"W2X{adresse_num:02d}"
        valeur_hexa = ''.join(f"{ord(c):02X}" for c in pair)
        w2x_map[adresse] = valeur_hexa
        adresse_num += 1
    return w2x_map

def parse_hex(w2x_hex):
    val = int(w2x_hex, 16)
    return (val >> 8) & 0xFF, val & 0xFF

def get_val(w2x, address):
    return parse_hex(w2x[address])

def ascii_to_int(val):
    return val - 0x30

# --- Helpers pour conversion ASCII en int avec signes ---
def decode_ascii_number(vals, sign_char=None, divisor=1.0):
    sign = -1 if sign_char == 0x2D else 1
    return sign * sum(ascii_to_int(v) * (10 ** (len(list(enumerate(vals)))-i-1)) for i, v in (list(enumerate(vals)))) / divisor

# --- Fonctions pour chaque groupe logique ---
def decode_time(w2x):
    # Heures, minutes, secondes
    h = decode_ascii_number(get_val(w2x, 'W2X01'))
    m = decode_ascii_number([get_val(w2x, 'W2X05')[1], get_val(w2x, 'W2X06')[0]])
    s = decode_ascii_number(get_val(w2x, 'W2X07'))
    return h, m, s

def decode_wind(w2x):
    bytes_ = list(get_val(w2x, 'W2X08')) + [get_val(w2x, 'W2X09')[0], get_val(w2x, 'W2X10')[0]]
    return decode_ascii_number(bytes_, divisor=10.0)

def decode_wind_dir(w2x):
    _, b11 = get_val(w2x, 'W2X11')
    b12, b12b = get_val(w2x, 'W2X12')
    return decode_ascii_number([b11, b12, b12b])

def decode_temperature(w2x):
    b13, b13b = get_val(w2x, 'W2X13')
    b14, b14b = get_val(w2x, 'W2X14')
    _, b15 = get_val(w2x, 'W2X15')
    return decode_ascii_number([b13b, b14, b14b, b15], sign_char=b13, divisor=10.0)

def decode_aspirated_temp(w2x):
    _, b25 = get_val(w2x, 'W2X25')
    b26, b26b = get_val(w2x, 'W2X26')
    b27, _ = get_val(w2x, 'W2X27')
    b28, _ = get_val(w2x, 'W2X28')
    return decode_ascii_number([b26, b26b, b27, b28], sign_char=b25, divisor=10.0)

def decode_pressure(w2x):
    _, b18 = get_val(w2x, 'W2X18')
    b19, b19b = get_val(w2x, 'W2X19')
    _, b20 = get_val(w2x, 'W2X20')
    b21, _ = get_val(w2x, 'W2X21')
    return decode_ascii_number([b18, b19, b19b, b20, b21], divisor=100.0)

def get_checksum_sum_part1(w2x):
    return (
        1061
        + sum(parse_hex(w2x[f'W2X{i:02d}'])[0] + parse_hex(w2x[f'W2X{i:02d}'])[1] for i in range(1, 10))
        + parse_hex(w2x['W2X10'])[0] + parse_hex(w2x['W2X11'])[1]
        + sum(parse_hex(w2x[f'W2X{i:02d}'])[0] + parse_hex(w2x[f'W2X{i:02d}'])[1] for i in range(12, 16))
    )

def get_checksum_sum_part2(var1, w2x):
    return (
        var1
        + parse_hex(w2x['W2X16'])[0] + parse_hex(w2x['W2X16'])[1]
        + parse_hex(w2x['W2X17'])[0]
        + parse_hex(w2x['W2X18'])[1]
        + parse_hex(w2x['W2X19'])[0] + parse_hex(w2x['W2X19'])[1]
        + parse_hex(w2x['W2X20'])[0] + parse_hex(w2x['W2X20'])[1]
        + parse_hex(w2x['W2X21'])[0]
        + parse_hex(w2x['W2X22'])[1]
        + parse_hex(w2x['W2X23'])[0] + parse_hex(w2x['W2X23'])[1]
        + parse_hex(w2x['W2X24'])[0]
        + parse_hex(w2x['W2X25'])[1]
        + parse_hex(w2x['W2X26'])[0] + parse_hex(w2x['W2X26'])[1]
        + parse_hex(w2x['W2X27'])[0] + parse_hex(w2x['W2X27'])[1]
        + parse_hex(w2x['W2X28'])[0]
        + parse_hex(w2x['W2X29'])[1]
        + parse_hex(w2x['W2X30'])[0] + parse_hex(w2x['W2X30'])[1]
        + parse_hex(w2x['W2X31'])[0]
    )

def get_checksum_comparison(w2x):
    b1, b2 = parse_hex(w2x['W2X32'])
    b3, b4 = parse_hex(w2x['W2X33'])
    return ((ascii_to_int(b1) * 1000) + (ascii_to_int(b2) * 100) +
            (ascii_to_int(b3) * 10) + ascii_to_int(b4))


# --- Fonction principale simplifiée ---
def decode_w2x_fields(w2x):
    result = {
        'X9460001': decode_ascii_number(get_val(w2x, 'W2X01')),
        'X9460002': decode_ascii_number(get_val(w2x, 'W2X02')),
        'X9460003': decode_ascii_number(get_val(w2x, 'W2X03')),
        'X9460004': decode_ascii_number(get_val(w2x, 'W2X04')),
        'X9460005': decode_ascii_number([get_val(w2x, 'W2X05')[1], get_val(w2x, 'W2X06')[0]]),
        'X9460006': decode_ascii_number(get_val(w2x, 'W2X07')),
        'X9460007': decode_wind(w2x),
        'X9460008': decode_wind_dir(w2x),
        'X9460009': decode_temperature(w2x),
        'X9460010': decode_ascii_number([get_val(w2x, 'W2X16')[0],get_val(w2x, 'W2X16')[1]  ,get_val(w2x, 'W2X17')[0]]),
        'X9460011': decode_pressure(w2x),
        'X9460012': decode_ascii_number([get_val(w2x, 'W2X22')[1], get_val(w2x, 'W2X23')[0], get_val(w2x, 'W2X24')[0]], divisor=10.0),
        'X9460013': decode_aspirated_temp(w2x),
        'X9460014': float(ascii_to_int(get_val(w2x, 'W2X29')[1])),
        'X9460015': float(ascii_to_int(get_val(w2x, 'W2X30')[0])),
        'X9460016': float(ascii_to_int(get_val(w2x, 'W2X30')[1])),
        'X9460017': float(ascii_to_int(get_val(w2x, 'W2X31')[0])),
    }

    var1 = get_checksum_sum_part1(w2x)
    var2 = get_checksum_sum_part2(var1, w2x)

    var3 = 1 if get_checksum_comparison(w2x) == var2 else 0

    result['X9460018_VAR1'] = var1
    result['X9460018_VAR2'] = var2
    result['X9460018_VAR3'] = var3

    return result
