from dotenv import load_dotenv
import os, threading, time, json, sys, pytz
import HomeControl_Variables as hcv
from w1thermsensor import W1ThermSensor, Sensor
from pyowm import OWM
from datetime import timedelta, datetime

# kell még átírni ide:
# - az inverter kiolvasást
# - a modbus kiolvasást (töltésvezérlők, shuntok, 220v mérők)
# - a tuya eszközök kiolvasását
# - a fűtés szabályozó logikát (házra, medencére)
# - a napelem előrejelzést solcasttól
# - a tuya eszközök vezérlését a szabályozó logikából

def trace_calls(frame, event, arg):
    if event == 'return':
        #print(f"\nFunction: {frame.f_code.co_name}")
        #print("Local Variables:")
        for name, value in frame.f_globals.items():
            # ha a változó a hcv.valami formában van, akkor kiírjuk
            if name in dir(hcv):  # Ha a változó neve az hcv modulban is megtalálható
                print(f"{name}: {value}")
            # Minden változót kiírunk, függetlenül attól, hogy mi az értéke
            #print(f"{name}: {value}")
    return trace_calls

def set_thread_trace():
    sys.settrace(trace_calls)

load_dotenv()

def timestamp_convert_to_seconds(time_str):
    try:
        if time_str is None:
             return None
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    except (ValueError, AttributeError):
        return None

def create_timestamp():
    current_time = time.localtime()
    timestamp = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}"
    return timestamp

def readout_wire1_data(Sensor_name):
    try:
        sensor_data_temp = W1ThermSensor(sensor_type=Sensor.DS18B20, sensor_id=Sensor_name)
        sensor_data = sensor_data_temp.get_temperature()
    except:
        sensor_data = None
        hcv.sensor_error += 1
    return sensor_data

def read_wire1_sensors():
#    threading.current_thread().name = "Wire1_SensorReaderThread"
    # Itt is érvényesítjük a trace-t az adott szálra
#    set_thread_trace()
    while True:
        # A szenzorok beolvasása az .env fájlból
        wire1_sensors = os.getenv("WIRE1_SENSORS")
        if wire1_sensors:
            sensor_dict = json.loads(wire1_sensors)
        else:
            print("No sensors found in the environment variables.")
            break
        # Minden szenzorhoz olvassuk ki az adatokat
        for sensor_name, sensor_id in sensor_dict.items():
            sensor_temp = readout_wire1_data(sensor_id)
            setattr(hcv, f'wire1_{sensor_name.lower()}_temp', sensor_temp)
                # ha a hcv-ben nincs ilyen attribútum, akkor hozzáadjuk
                # ha van belerjuk az értéket
        hcv.wire1_update_time = create_timestamp() 
        wire1_update_time_sec = timestamp_convert_to_seconds(hcv.wire1_update_time)
        #print(hcv.wire1_update_time, wire1_update_time_sec)
        time.sleep(1)

def write_to_cli():
    # a .env fileban megadott szenzornevekbl a hcv-ben tárolt értékeket kiírja a konzolra
    # a hcv-ben tárolt értékeket kiírja a konzolra
    # a következő formátumban, sorba egymás után függetlenül attól mennyi szenzor van
    # | szenzor neve: értéke | szenzor neve: értéke ...
#    threading.current_thread().name = "CLI_write_thread"
    # Itt is érvényesítjük a trace-t az adott szálra
#    set_thread_trace()
    def write_to_cli_wire1_sensor_data():
        wire1_sensors = os.getenv("WIRE1_SENSORS")
        if wire1_sensors:
            sensor_dict = json.loads(wire1_sensors)
        else:
            print("No sensors found in the environment variables.")
            return
        sensor_data = ""
        for sensor_name in sensor_dict.keys():
            if getattr(hcv, f'wire1_{sensor_name.lower()}_temp') is not None:
                sensor_data += f"| {sensor_name}: {getattr(hcv, f'wire1_{sensor_name.lower()}_temp'):0.1f} " # 2 tizedes pontossággal
            else:
                sensor_data += f"| {sensor_name}: None "
        print(sensor_data)

    def write_to_cli_owm_data():
        print(f"OWM | temp: {hcv.owm_temperature} | hum: {hcv.owm_humidity} | icon: {hcv.owm_weather_icon} | id: {hcv.owm_weather_id} | stat: {hcv.owm_detailedstatus}")
        #print(f"OWM | sunr_utc/local/hm: {hcv.owm_sunrise_utc}/{hcv.owm_sunrise_local}/{hcv.owm_sunrise_hm} | suns_utc/local/hm: {hcv.owm_sunset_utc}/{hcv.owm_sunset_local}/{hcv.owm_sunset_hm}")
        if hcv.owm_daylight_duration != None:
            hours = hcv.owm_daylight_duration.seconds // 3600
            minutes = (hcv.owm_daylight_duration.seconds % 3600) // 60
            #print(hours, minutes)
        else: hours, minutes = None, None
        print(f"OWM_sunrise_hm: {hcv.owm_sunrise_hm} | OWM_sunset_hm: {hcv.owm_sunset_hm} | daylight_duration: {hours}:{minutes}")
        print(f"OWM | cloud: {hcv.owm_cloud_now} | rain: {hcv.owm_rain_now} | bad_hour: {hcv.owm_bad_hour}")
        print(hcv.loging)

    while True:
        print("--------------------------------------------")
        write_to_cli_wire1_sensor_data()
        write_to_cli_owm_data()
        time.sleep(1)  

def align_sunrise_sunset_local():
    #itt történik a napfelkelte és napnyugta időpontjának igazítása az adott hónapnak megfelelően
    #az itt igazított időpont később fontos lesz a fűtés szabályoknál
    #ez alapján fog gazdálkodni a nappali és éjszakai akkumlátorral majd
    current_month = str(datetime.now().month)  # A hónapot stringként használjuk a dictionary kulcsához
    OWM_timedelta = os.getenv("OWM_timedelta")
    timedelta_dict = json.loads(OWM_timedelta)
    if current_month in timedelta_dict:
        sunrise_offset_str, sunset_offset_str = timedelta_dict[current_month]
        before_timedelta_sunrise = hcv.owm_sunrise_local.strftime('%H:%M')
        before_timedelta_sunset = hcv.owm_sunset_local.strftime('%H:%M')
        sunrise_offset = float(sunrise_offset_str) * 60  # Órából percekre alakítjuk
        sunset_offset = float(sunset_offset_str) * 60  # Órából percekre alakítjuk
        # A napkelte és napnyugta igazítása
        hcv.owm_sunrise_local += timedelta(minutes=sunrise_offset)
        hcv.owm_sunset_local -= timedelta(minutes=abs(sunset_offset))  # Biztosítjuk, hogy a sunset_offset pozitív legyen
        if sunrise_offset != 0 or sunset_offset != 0:
            hcv.loging = f" OLD: {before_timedelta_sunrise} / {before_timedelta_sunset} modified_with: {sunrise_offset_str} / {sunset_offset_str} timedelta "
        else:
            hcv.loging = " no timedelta "
    else:
        hcv.loging = " no data for this month "

def get_owm_weather():
# lekéri az időjárás adatokat a netről a lakásom koordinátáira 2 percenként
        try:
            OWM_api = os.getenv("OWM_api")
            hcv.owm_last_query = datetime.now().isoformat()    
            #weather_last_query = datetime.now().isoformat()
            hcv.owm_data = OWM(OWM_api)
            manager = hcv.owm_data.weather_manager()
            OWM_location = os.getenv("OWM_location")
            observation = manager.weather_at_place(OWM_location)
            owm_weather = observation.weather #ignore
            hcv.owm_temperature = owm_weather.temperature('celsius')['temp']
            hcv.owm_humidity = owm_weather.humidity
            hcv.owm_weather_id = owm_weather.weather_code
            hcv.owm_weather_icon = owm_weather.weather_icon_name
            hcv.owm_detailedstatus = owm_weather.detailed_status
            hcv.owm_cloud_now = owm_weather.clouds
            hcv.owm_rain_now = owm_weather.rain if owm_weather.rain != {} else 0 # Ha nincs eső, akkor 0, ha van akkor az érték
            # eldől hogy napelem szempontból milyen óra van
            if hcv.owm_rain_now > 0 or hcv.owm_cloud_now > 50:
                hcv.owm_bad_hour = True
            else:
                hcv.owm_bad_hour = False
            #utc = pytz.utc
            OWM_timezone = os.getenv("OWM_timezone")
            local_tz = pytz.timezone(OWM_timezone)
            hcv.owm_sunrise_utc = datetime.fromisoformat(owm_weather.sunrise_time(timeformat='iso'))
            hcv.owm_sunset_utc = datetime.fromisoformat(owm_weather.sunset_time(timeformat='iso'))
            # Konvertálás helyi időzónába
            hcv.owm_sunrise_local = hcv.owm_sunrise_utc.astimezone(local_tz)
            hcv.owm_sunset_local = hcv.owm_sunset_utc.astimezone(local_tz)
            # Módosítás az adott hónapoknak megfelelően
            align_sunrise_sunset_local()
            # Formázás csak órára és percre
            hcv.owm_sunrise_hm = hcv.owm_sunrise_local.strftime('%H:%M')
            hcv.owm_sunset_hm = hcv.owm_sunset_local.strftime('%H:%M')
            sunrise = datetime.strptime(hcv.owm_sunrise_hm, '%H:%M')
            sunset = datetime.strptime(hcv.owm_sunset_hm, '%H:%M')
            hcv.owm_daylight_duration = sunset - sunrise
            hcv.owm_update_time = create_timestamp()
        except:
            pass
        time.sleep(120)

if __name__ == '__main__':
    read_wire1_thread = threading.Thread(target=read_wire1_sensors) 
    get_owm_weather_thread = threading.Thread(target=get_owm_weather)
    print_to_cli_thread = threading.Thread(target=write_to_cli)   

    read_wire1_thread.start()
    get_owm_weather_thread.start()
    print_to_cli_thread.start()

    read_wire1_thread.join()
    get_owm_weather_thread.join()
    print_to_cli_thread.join()
