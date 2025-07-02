def get_status_temp(temp):
    if temp == -999.0:
        return 'X'  # Échec lecture
    if temp > 60.0:
        return 'H'  # Trop chaud
    if temp < -50.0:
        return 'L'  # Trop froid
    return 'S'      # Standard


def get_status_wss(temp, wind_speed, pressure, humidity, battery):
    if any(v == -999.0 for v in [temp, wind_speed, pressure, humidity, battery]):
        return '2'  # Lecture échouée
    if (
        temp < -50 or temp > 60 or
        wind_speed < 0 or wind_speed > 150 or
        pressure < 800 or pressure > 1200 or
        humidity < 0 or humidity > 100 or
        battery < 9.0 or battery > 16.0
    ):
        return '1'  # Valeur incohérente
    return '0'      # OK


def get_status_gps(gps_hour, gps_minute, gps_second, gps_location_valid):
    if gps_hour == -1 or gps_minute == -1 or gps_second == -1:
        return '2'  # Horloge non disponible
    if not gps_location_valid:
        return '1'  # Coordonnées GPS invalides
    return '0'


def round_value(value, width, decimals=0):
    if isinstance(value, float):
        value = abs(value)
        formatted = f"{value:.{decimals}f}"
    else:
        formatted = str(value)
    return formatted.zfill(width + (1 if decimals > 0 else 0))


def format_date(year, month, day):
    return f"{year % 100}{round_value(month, 2)}{round_value(day, 2)}"

def format_time(hour, minute, second):
    return f"{round_value(hour, 2)}:{round_value(minute, 2)}:{round_value(second, 2)}"

def format_wind(wind_speed, wind_dir):
    return f"{round_value(wind_speed, 4, 1)}, {round_value(wind_dir, 3)}"

def format_temperature(temp):
    sign = "+" if temp >= 0 else "-"
    return f"{sign}{round_value(abs(temp), 4, 1)}"

def format_humidity(humidity):
    return round_value(humidity, 3)

def conversion_pressure(pressure_mbar):
    return 0.02953 * pressure_mbar

def format_pressure(pressure):
    return round_value(conversion_pressure(pressure), 5, 2)

def format_battery(battery):
    return round_value(battery, 3, 1)

def compute_status(temp_code='A', wss_code='0', gps_code='1', log_code='0'):
    return f"{temp_code}{wss_code}{gps_code}{log_code}"

def calculate_checksum(frame):
    #for c in frame[0:76]:
     #   print("normal" + (c))
      #  print((ord(c)))
    return str(sum(ord(c) for c in frame[6:77]))