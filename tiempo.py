import requests
import zipfile
import io
from datetime import datetime as dt
import json

"""
--------------------------------------------------------
                        CONSTANTES
--------------------------------------------------------
"""
URL_DESCARGA = 'https://ssl.smn.gob.ar/dpd/zipopendata.php?dato='
PARAM_TIEMPO = 'tiepre'
PARAM_PRONOSTICO = 'pron5d'
TEXT_ENCODING = 'latin-1'

NO_TERMICA = "No se calcula"
DIR_VARIABLE = "Variable"
LOCALIDAD = "localidad"
FECHA = "fecha"
DESCRIPCION = "desc"
VISIBILIDAD = "visibilidad"
TEMP = "temp"
TERMICA = "termica"
HUMEDAD = "humedad"
VIENTO = "viento"
PRESION = "presion"
VIENTO_DIR = "viento_dir"
VIENTO_VEL = "viento_vel"
PRECIP = "precip"
MESES_A_INGLES = {"Enero":"January",
                  "Febrero":"February",
                  "Marzo":"March",
                  "Abril":"April",
                  "Mayo":"May",
                  "Junio":"June",
                  "Julio":"July",
                  "Agosto":"August",
                  "Septiembre":"September",
                  "Octubre":"October",
                  "Noviembre":"November",
                  "Diciembre":"December",
                  }
MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

ERROR_FECHA_INVALIDA = "La fecha ingresada {}/{}/{} no se encuentra en el pronostico"
"""
--------------------------------------------------------
            CLASES Y FUNCIONES AUXILIARES
--------------------------------------------------------
"""
class JSONEncoderPronosticos(json.JSONEncoder):
    """Codificador de JSON preparado para codificar los objetos del pronostico """
    def default(self, o):
        if isinstance(o, PronosticoLocalidad):
            return o.serializar()
        return json.JSONEncoder.default(self, o)

class PronosticoLocalidad():
    """
    Representa el pronostico del tiempo para una localidad determinada.
    Permite tener el pronostico para distintas horas y distintos dias.
    """
    def __init__(self):
        self.pronosticos = {}
    def agregar_pronostico(self, fecha, hora, temp, viento_dir, viento_vel, precip):
        """
        Agrega el pronostico del tiempo para una fecha y horario determinado 
        Si ya se tiene un pronostico para esa fecha y horario se sobreescribe.
        """
        pron = {}
        pron[TEMP] = float(temp)
        pron[VIENTO_DIR] = int(viento_dir)
        pron[VIENTO_VEL] = float(viento_vel)
        pron[PRECIP] = float(precip)

        dia, mes, anio = fecha.split("/")
        fecha_dt = dt(day = int(dia), month = MESES.index(mes)+1, year= int(anio))
        hora = hora[:-3]
        d = self.pronosticos.get(fecha_dt, {})
        d[hora] = pron
        self.pronosticos[fecha_dt] = d
    def __str__(self):
        """ devuelve una representacion del pronostico imprimible """
        return str(self.pronosticos)
    def obtener_pronostico(self, dia, mes, anio):
        fecha = dt(day = int(dia), month=int(mes), year = int(anio))
        if fecha not in self.pronosticos:
            raise ValueError(ERROR_FECHA_INVALIDA.format(dia, mes, anio))
        return self.pronosticos[fecha]
    def serializar(self):
        """ Devuelve una representacion del estado actual del objeto PronosticoLocalidad"""
        rep = {}
        for k, v in self.pronosticos.items():
            rep[k.strftime("%d-%m-%Y")] = v
        return rep


def descargar_datos(param):
    """Descarga los datos desde la pagina oficial del servicio meteorologico
    nacional ( https://smn.gob.ar ). Luego descomprime el archivo, lo abre y 
    lo devuelve. 
    ATENCION: hay que cerrar el archivo luego de utilizarlo.
    
    """
    r = requests.get(URL_DESCARGA + param)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    nombre = z.namelist()[0]
    archivo = io.TextIOWrapper(z.open(nombre), TEXT_ENCODING)
    return archivo


def transformar_unidad(n, unidad_inicio, unidad_destino):
    """
    Hace el cambio de unidad  de 'n' desde la unidad de inicio a la unidad destino y lo devuelve
    """        
    unidades = ["mm", "cm", "dm", "mts", "dam", "hm", "km"]
    if unidad_inicio == unidad_destino: return n
    if unidad_inicio not in unidades or unidad_destino not in unidades:
        raise ValueError("No se reconoce la unidad")
    indice_inicio = unidades.index(unidad_inicio) #3
    indice_destino = unidades.index(unidad_destino) #6
    return (10**(indice_destino-indice_inicio)) * n



def obtener_visibilidad_km(visibilidad):
    """
    Verifica si la visibilidad esta presentada en una unidad menor a km
    lo convierte a km y lo devuelve.
    Caso visto en el documento: "Menor a 100mts"
    """
    visibilidad_n = 0
    visibilidad_unidad = ""
    spliteado = visibilidad.split(' ')
    i = 0
    while not visibilidad[i].isdigit():
        i += 1
    aux = []
    while visibilidad[i].isdigit() or visibilidad[i] == ".":
        aux.append(visibilidad[i])
        i += 1
    visibilidad_n = float(''.join(aux))
    while i < len(visibilidad):
        char_act = visibilidad[i]
        i += 1
        if char_act == " ": continue
        visibilidad_unidad += char_act
    return transformar_unidad(visibilidad_n, visibilidad_unidad, "km")

def parsear_linea_tiempo_presente(linea):
    d = {}
    print(linea)
    localidad, fecha, hora, descripcion, visibilidad, temperatura, termica, humedad, viento, presion = linea.strip('/').split(';')
    viento_sep = viento.split()
    if len(viento_sep) == 1: 
        viento_dir = viento_sep[0]
        viento_vel = 0
    elif len(viento_sep) == 2:
        viento_dir, viento_vel = viento_sep
    else:
        #Si tiene direcciones variables
        #Caso visto en el documento: "Direcciones variables  3"
        viento_dir = DIR_VARIABLE
        viento_vel = viento_sep[-1]

    dia, mes, anio = fecha.split("-")
    #Check
    d[FECHA] = dt.strptime(f"{dia}-{MESES_A_INGLES[mes]}-{anio} {hora}", '%d-%B-%Y %H:%M')
    d[DESCRIPCION] = descripcion

    d[VISIBILIDAD] = obtener_visibilidad_km(visibilidad)
    d[TEMP] = float(temperatura)
    if termica == NO_TERMICA or not termica:
        d[TERMICA] = None
    else:
        d[TERMICA] = float(termica)
    d[HUMEDAD] = float(humedad.strip())
    d[VIENTO] = (viento_dir, float(viento_vel))

    presion = presion.strip(" /\n") 
    if presion.isdigit():
        d[PRESION] = float(presion)
    else:
        d[PRESION] = None

    return localidad.strip().lower(), d

def parsear_linea_pronostico(linea):
    """Parsea una linea del pronostico. Esta se supone que tiene el formato:
      Fecha                   Temp(°C)   Viento(dir|km/h)   Precipitacion(mm)
      31/DIC/2019 00Hs.        23.4       102 |   9         0.4 
    Devuelve una tupla con la forma: (fecha, hora, temp, viento_dir, viento_vel, precip)
    """
    spliteado = linea.split()
    spliteado.remove('|')
    return spliteado

def buscar_primer_caracter(linea):
    for c in linea:
        if c != " ":
            return c


def tiempo_actual():
    """
    Descarga los datos del tiempo actual para todas las localidades,
    las parsea a un diccionario y las devuelve.
    """
    archivo = descargar_datos(PARAM_TIEMPO)
    tiempo = {}
    for linea in archivo:
        localidad, datos = parsear_linea_tiempo_presente(linea)
        tiempo[localidad] = datos
        
    archivo.close()
    return tiempo

def pronostico():
    """
    Descarga los datos del pronostico del tiempo a 5 dias para todas 
    las localidades, los parsea y guarda en un diccionario y los devuelve.
    """
    archivo = descargar_datos(PARAM_PRONOSTICO)

    pronosticos = {}
    linea_ant = None
    linea_ant_primero = ""
    localidad = ""
    for linea in archivo:
        primero = buscar_primer_caracter(linea)
        if primero == '=' and linea_ant_primero.isalpha():
            #Aca las localidades se guardan en mayuscula y con _ como separador
            localidad = linea_ant.strip(' \n') 

        if primero.isdigit():
            if localidad in pronosticos:
                pronosticos[localidad].agregar_pronostico(*parsear_linea_pronostico(linea))
            else:
                pron = PronosticoLocalidad()
                pron.agregar_pronostico(*parsear_linea_pronostico(linea))
                pronosticos[localidad] = pron

        linea_ant = linea
        linea_ant_primero = primero

    archivo.close()
    return pronosticos

"""
--------------------------------------------------------
                        API
--------------------------------------------------------
"""
def tiempo_actual_json():
    """Provee el estado actual del tiempo en formato JSON """
    tiempo = tiempo_actual()
    return json.dump(tiempo, indent = '\t')

def tiempo_en_localidad(localidad):
    """Provee el estado actual del tiempo para una determinada 
    localidad.
    Devuelve un diccionario con los datos obtenidos. """
    return tiempo_actual()[localidad.lower().strip(" ")]

def pronostico_en_localidad(localidad):
    """Provee el pronostico del tiempo a 5 días en la localidad 
    deseada. Devuelve un diccionario con los resultados obtenidos. """
    datos_pronostico = pronostico()
    return datos_pronostico[localidad.upper().replace(" ", "_")]

def pronostico_json():
    """Devuelve el pronostico del tiempo a 5 días para todas las 
    localidades en formato JSON"""
    datos_pronostico = pronostico()
    return json.dump(datos_pronostico, cls = JSONEncoderPronosticos, indent = '\t')

def pronostico_localidad_json(localidad):
    """Provee el pronostico del tiempo a 5 días en la localidad indicada.
    Devuelve los resultados en formato JSON. """
    datos_pronostico = pronostico_en_localidad(localidad)
    return json.dumps(datos_pronostico, cls = JSONEncoderPronosticos, indent = '\t')
