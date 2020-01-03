## API en Python para obtener datos del Servicio Meteorológico Nacional (SMN) argentino

Permite obtener los datos del tiempo, a partir de los datos provistos por el [SMN](https://www.smn.gob.ar/descarga-de-datos "Descarga de datos"). 
#### API  
 - **tiempo_actual_json()**: Provee el estado actual del tiempo en formato JSON  
 - **pronostico_json()**: Devuelve el pronostico del tiempo a 5 días para todas las localidades en formato JSON
 - **tiempo_en_localidad()**: Provee el estado actual del tiempo para una determinada localidad. Devuelve un diccionario con los datos obtenidos.  
 - **pronostico_en_localidad()**: Provee el pronostico del tiempo a 5 días en la localidad deseada. Devuelve un diccionario con los resultados obtenidos.  
 - **pronostico_localidad_json()**: Provee el pronostico del tiempo a 5 días en la localidad indicada. Devuelve los resultados en formato JSON.  

------  
Inspirado en el código de [fmartin92](https://github.com/fmartin92/smn-api)