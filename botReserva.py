import math
import os
import pyttsx3
import speech_recognition as sr
import sqlite3
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import re
from google.cloud import dialogflow_v2 as dialogflow
import datetime
import dateparser
import random

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "prueba-agente-dnpf-c3237e543e4f.json"
firebase_sdk = credentials.Certificate(
    "botreservas-386400-firebase-adminsdk-1nqww-9a3e7682a6.json"
)
firebase_admin.initialize_app(
    firebase_sdk,
    {"databaseURL": "https://botreservas-386400-default-rtdb.firebaseio.com/"},
)

ref = db.reference

conn = sqlite3.connect("hotel.db")
c = conn.cursor()
c.execute(
    """CREATE TABLE IF NOT EXISTS rooms (name text, checkin_date text, checkout_date text)"""
)
c.execute(
    """CREATE TABLE IF NOT EXISTS restaurant (name text, reservation_date text, reservation_time text)"""
)


bot_name = "Jarvis"
bot_age = "1 año"
bot_creator = "Hotel UPAO"

engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()


def listen():
    r = sr.Recognizer()
    text = ""
    while not text:
        with sr.Microphone() as source:
            print("Di algo...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language="es-ES")
                print("Escuché: ", text)
            except Exception as e:
                print("No pude entenderte. Intenta de nuevo.")
                speak("No pude entenderte. Intenta de nuevo.")
    return text


def convertir_fecha(fecha_hablada):
    fecha = dateparser.parse(fecha_hablada)
    if fecha:
        fecha_str = fecha.strftime("%d/%m/%Y")
        return fecha_str
    else:
        return None


def check_availability(Habitacion, fecha_in, fecha_out):
    ref = db.reference("/Reservas")
    reservas = ref.order_by_child("Habitacion").equal_to(Habitacion).get()
    for reserva_id, reserva in reservas.items():
        fecha_in_reserva = dateparser.parse(reserva["FechaIn"], languages=["es"]).date()
        fecha_out_reserva = dateparser.parse(
            reserva["FechaSal"], languages=["es"]
        ).date()
        if (
            fecha_in_reserva <= fecha_in <= fecha_out_reserva
            or fecha_in_reserva <= fecha_out <= fecha_out_reserva
        ):
            return False
    return True


def update_reservation():
    speak("¿Cuál es tu nombre?")
    print("¿Cuál es tu nombre?")
    name = listen()
    speak("¿Cuál es la nueva fecha de entrada?")
    print("¿Cuál es la nueva fecha de entrada?")
    new_checkin_date = listen()
    speak("¿Cuál es la nueva fecha de salida?")
    print("¿Cuál es la nueva fecha de salida?")
    new_checkout_date = listen()
    c.execute(
        "UPDATE rooms SET checkin_date = ?, checkout_date = ? WHERE name = ?",
        (new_checkin_date, new_checkout_date, name),
    )
    conn.commit()
    speak(f"¡Listo! Tu reserva ha sido actualizada para el {new_checkin_date} hasta el {new_checkout_date}.")
    print(f"¡Listo! Tu reserva ha sido actualizada para el {new_checkin_date} hasta el {new_checkout_date}.")

def calcular_num_habitaciones(dni):
    # Preguntar por el número de personas
    speak("¿Cuántas personas van a hospedarse?")
    print("¿Cuántas personas van a hospedarse?")
    npersonas_str = listen()

    # Usar un bucle while para validar el número de personas
    while True:
        try:
            npersonas = int(npersonas_str)
            # Salir del bucle si el número es positivo
            if npersonas > 0:
                break
            # Si no, pedir otro número
            else:
                speak("Debe haber al menos una persona para hacer una reserva. Intenta de nuevo.")
                print("Debe haber al menos una persona para hacer una reserva. Intenta de nuevo.")
                npersonas_str = listen()
        # Si ocurre un error al convertir el número, pedir otro número
        except ValueError:
            speak("No pude entender el número de personas. Intenta de nuevo.")
            print("No pude entender el número de personas. Intenta de nuevo.")
            npersonas_str = listen()

    # El resto del código sigue igual
    if npersonas <= 2:
        num_habitaciones = 1
        habitaciones_disponibles = [101, 102, 103, 104, 105, 201, 202, 203, 204, 205]
    else:
        num_habitaciones = math.ceil(npersonas / 2)
        habitaciones_disponibles = [101, 102, 103, 104, 105, 201, 202, 203, 204, 205]

    # Verificar que haya suficientes habitaciones disponibles
    if len(habitaciones_disponibles) < num_habitaciones:
        speak("Lo sentimos, no hay suficientes habitaciones disponibles.")
        print("Lo sentimos, no hay suficientes habitaciones disponibles.")
        return

    # Verificar si hay suficientes habitaciones consecutivas
    consecutivas_disponibles = False
    for i in range(len(habitaciones_disponibles) - num_habitaciones + 1):
        consecutivas = True
        for j in range(num_habitaciones):
            if habitaciones_disponibles[i+j] != habitaciones_disponibles[i] + j:
                consecutivas = False
                break
        if consecutivas:
            consecutivas_disponibles = True
            break

    # Si no hay suficientes habitaciones consecutivas, mostrar un mensaje de error
    if not consecutivas_disponibles:
        speak("Lo sentimos, no hay suficientes habitaciones consecutivas disponibles.")
        print("Lo sentimos, no hay suficientes habitaciones consecutivas disponibles.")
        return

    # Seleccionar habitaciones consecutivas al azar
    indice_inicio = random.randint(0, len(habitaciones_disponibles) - num_habitaciones)
    habitaciones_asignadas = habitaciones_disponibles[indice_inicio:indice_inicio + num_habitaciones]

    # Convertir la lista en una cadena separada por comas
    habitaciones_str = ", ".join(str(h) for h in habitaciones_asignadas)

    # Informar al usuario las habitaciones asignadas
    speak(f"A usted le corresponde reservar {num_habitaciones} habitaciones.")
    print(f"A usted le corresponde reservar {num_habitaciones} habitaciones.")
    speak(f"Se le han asignado las siguientes habitaciones: {habitaciones_str}.")
    print(f"Se le han asignado las siguientes habitaciones: {habitaciones_str}.")

    # Actualizar la base de datos con las habitaciones asignadas
    db.reference('/Clientes/' + dni).child("Reserva").child("Hotel").update({
        "Habitacion": habitaciones_str,
    })

    return num_habitaciones

def reserve_room():
    precio_habitacion = 40
    speak("¿Cuál es tu DNI?")
    print("¿Cuál es tu DNI?")
    dni = listen()
    dni = re.sub(r"\s+", "", dni) # eliminar espacios en blanco
    if dni == "":
        speak("No pude entender tu DNI. Intenta de nuevo.")
        print("No pude entender tu DNI. Intenta de nuevo.")
        return
    ref = db.reference('/Clientes/' + dni)
    data = ref.get()
    if data:
        print(data['Nombre'])
        speak("Bienvenido " + data['Nombre'])
        print("Bienvenido " + data['Nombre'])
        num_habitaciones = calcular_num_habitaciones(dni)
        speak("¿Cuál es la fecha de entrada? Por favor, indícame dia y luego mes")
        print("¿Cuál es la fecha de entrada? Por favor, indícame dia y luego mes")
        fecha_in_str = listen()
        fecha_in = dateparser.parse(fecha_in_str + "/2023", languages=['es'])
        if fecha_in is None:
            speak("No pude entender la fecha de entrada. Intenta de nuevo.")
            print("No pude entender la fecha de entrada. Intenta de nuevo.")
            return
        fecha_in = fecha_in.replace(year=2023)
        fecha_in_str = fecha_in.strftime("%d/%m/%Y")

    
        valid_date = False 
        while not valid_date:
            speak("¿Cuál es la fecha de salida? Por favor, indícame dia y luego mes")
            print("¿Cuál es la fecha de salida? Por favor, indícame dia y luego mes")
            fecha_out_str = listen()
            fecha_out = dateparser.parse(fecha_out_str + "/2023", languages=['es'])
            if fecha_out is None:
                speak("No pude entender la fecha de salida. Intenta de nuevo.")
                print("No pude entender la fecha de salida. Intenta de nuevo.")
                continue 
            fecha_out = fecha_out.replace(year=2023)
            fecha_out_str = fecha_out.strftime("%d/%m/%Y")
            num_dias = (fecha_out - fecha_in).days
            if num_dias < 1:
                speak("La fecha de salida debe ser después de la fecha de entrada. Intenta de nuevo.")
                print("La fecha de salida debe ser después de la fecha de entrada. Intenta de nuevo.")
                continue 
            else:
                valid_date = True 

        precio_total = num_dias * num_habitaciones * precio_habitacion

        ref.child("Reserva").child("Hotel").update({
        "FechaIn": fecha_in_str,
        "FechaSal": fecha_out_str,
        "NumDias": num_dias,
        "PrecioTotal": precio_total,

        })

        print(f"¡Listo! {data['Nombre']}, tu reserva ha sido registrada para el {fecha_in_str} hasta el {fecha_out_str}, un total de {num_dias} días. El precio total es {precio_total}.")
        speak(f"¡Listo! {data['Nombre']}, tu reserva ha sido registrada para el {fecha_in_str} hasta el {fecha_out_str}, un total de {num_dias} días. El precio total es {precio_total}.")


    else:
        print("No se encontraron datos para el DNI " + dni)
        speak("No se encontraron datos para el DNI " + dni)
        print("Veo que eres un cliente nuevo")
        speak("Veo que eres un cliente nuevo")
        print("¿Cuál es tu nombre?")
        speak("¿Cuál es tu nombre?")
        name = listen()
        reserva_ref = db.reference("/Clientes/" + dni)
        reserva_ref.set({"Nombre": name})
        speak("Bienvenido " + name)
        print("Bienvenido " + name)
        num_habitaciones = calcular_num_habitaciones(dni)
        speak("¿Cuál es la fecha de entrada? Por favor, indícame dia y luego mes")
        print("¿Cuál es la fecha de entrada? Por favor, indícame dia y luego mes")
        fecha_in_str = listen()
        fecha_in = dateparser.parse(fecha_in_str + "/2023", languages=['es'])
        if fecha_in is None:
            speak("No pude entender la fecha de entrada. Intenta de nuevo.")
            print("No pude entender la fecha de entrada. Intenta de nuevo.")
            return
        fecha_in = fecha_in.replace(year=2023)
        fecha_in_str = fecha_in.strftime("%d/%m/%Y")

        
        valid_date = False 
        while not valid_date: 
            speak("¿Cuál es la fecha de salida? Por favor, indícame dia y luego mes")
            print("¿Cuál es la fecha de salida? Por favor, indícame dia y luego mes")
            fecha_out_str = listen()
            fecha_out = dateparser.parse(fecha_out_str + "/2023", languages=['es'])
            if fecha_out is None:
                speak("No pude entender la fecha de salida. Intenta de nuevo.")
                print("No pude entender la fecha de salida. Intenta de nuevo.")
                continue 
            fecha_out = fecha_out.replace(year=2023)
            fecha_out_str = fecha_out.strftime("%d/%m/%Y")
            num_dias = (fecha_out - fecha_in).days
            if num_dias < 1:
                speak("La fecha de salida debe ser después de la fecha de entrada. Intenta de nuevo.")
                print("La fecha de salida debe ser después de la fecha de entrada. Intenta de nuevo.")
                continue 
            else:
                valid_date = True 

        precio_total = num_dias * num_habitaciones * precio_habitacion
        ref.child("Reserva").child("Hotel").update({
        "FechaIn": fecha_in_str,
        "FechaSal": fecha_out_str,
        "NumDias": num_dias,
        "PrecioTotal": precio_total,
        })
        print(f"¡Listo!" + name + ", tu reserva ha sido registrada para el"+ fecha_in_str +" hasta el "+ fecha_out_str +", un total de "+ str(num_dias) +" días. El precio total es "+ str(precio_total) +".")
        speak(f"¡Listo!" + name + ", tu reserva ha sido registrada para el"+ fecha_in_str +" hasta el "+ fecha_out_str +" un total de "+ str(num_dias) +" días. El precio total es "+ str(precio_total) +".")

def cancel_hotel_reservation():
    speak("Por favor, proporciona el número de identificación del cliente.")
    print("Por favor, proporciona el número de identificación del cliente.")
    dni = listen()
    dni = re.sub(r"\s+", "", dni)  # eliminar espacios en blanco

    if dni == "":
        speak("No pude entender el número de dni. Intenta de nuevo.")
        print("No pude entender el número de dni. Intenta de nuevo.")
        return

    ref = db.reference('/Clientes/' + dni)
    data = ref.get()

    if not data or 'Reserva' not in data:
        print("No se encontró una reserva para este cliente.")
        speak("No se encontró una reserva para este cliente.")
        return

    reservation = data['Reserva']
    fecha_in_str = reservation['Hotel']['FechaIn']
    fecha_out_str = reservation['Hotel']['FechaSal']

    ref.child("Reserva").delete()

    print(f"La reserva para el cliente {data['Nombre']} desde {fecha_in_str} hasta {fecha_out_str} ha sido cancelada.")
    speak(f"La reserva para el cliente {data['Nombre']} desde {fecha_in_str} hasta {fecha_out_str} ha sido cancelada.")


def calcular_num_mesas():
    # Crear referencia al nodo "Reserva/Restaurante"
    ref = db.reference('Reserva/Restaurante')

    # Preguntar por el número de personas
    speak("¿Cuántas personas van a asistir?")
    print("¿Cuántas personas van a asistir?")
    npersonasm_str = listen()
    try:
        npersonasm = int(npersonasm_str)
    except ValueError:
        speak("No pude entender el número de personas. Intenta de nuevo.")
        print("No pude entender el número de personas. Intenta de nuevo.")
        return
    if npersonasm < 1:
        speak("Debe haber al menos una persona para hacer una reserva.")
        print("Debe haber al menos una persona para hacer una reserva.")
        return
    if npersonasm <= 4:
        num_mesas = 1
        speak("Se te ha reservado una mesa.")
        print("Se te ha reservado una mesa.")
    else:
        num_mesas = math.ceil(npersonasm / 4)
        speak(f"A usted se le han reservado {num_mesas} mesas.")
        print(f"A usted se le han reservado {num_mesas} mesas.")
    
    ref.update({
        "Cantidad Mesas": num_mesas,
    })

    return num_mesas


def reserve_mesa():
    speak("¿Cuál es tu DNI?")
    print("¿Cuál es tu DNI?")
    dni = listen()
    dni = re.sub(r"\s+", "", dni) # eliminar espacios en blanco
    if dni == "":
        speak("No pude entender tu DNI. Intenta de nuevo.")
        print("No pude entender tu DNI. Intenta de nuevo.")
        return
    ref = db.reference('/Clientes/' + dni)
    data = ref.get()
    if data:
        print(data['Nombre'])
        speak("Bienvenido " + data['Nombre'])
        print("Bienvenido " + data['Nombre'])
        num_mesas = calcular_num_mesas()
        speak("¿Cuál es la fecha de reserva de mesa? Por favor, indícame dia y luego mes")
        print("¿Cuál es la fecha de reserva de mesa? Por favor, indícame dia y luego mes")
        fecha_in_m_str = listen()
        fecha_in_m = dateparser.parse(fecha_in_m_str + "/2023", languages=['es'])
        if fecha_in_m is None:
            speak("No pude entender la fecha de reserva. Intenta de nuevo.")
            print("No pude entender la fecha de reserva. Intenta de nuevo.")
            return
        fecha_in_m = fecha_in_m.replace(year=2023)
        fecha_in_m_str = fecha_in_m.strftime("%d/%m/%Y")
        
        ref.child("Reserva").child("Restaurante").update({
            "ReservaMesa": fecha_in_m_str,
        })
        
        print(f"¡Listo! {data['Nombre']}, tu reserva ha sido registrada para el {fecha_in_m_str}, un total de {num_mesas} mesas.")
        speak(f"¡Listo! {data['Nombre']}, tu reserva ha sido registrada para el {fecha_in_m_str}, un total de {num_mesas} mesas.")

    else:
        print("No se encontraron datos para el DNI " + dni)
        speak("No se encontraron datos para el DNI " + dni)
        print("Veo que eres un cliente nuevo")
        speak("Veo que eres un cliente nuevo")
        print("¿Cuál es tu nombre?")
        speak("¿Cuál es tu nombre?")
        name = listen()
        reserva_ref = db.reference("/Clientes/" + dni)
        reserva_ref.set({"Nombre": name})
        speak("Bienvenido " + name)
        print("Bienvenido " + name)
        num_mesas = calcular_num_mesas()
        speak("¿Cuál es la fecha de reserva de mesa? Por favor, indícame dia y luego mes")
        print("¿Cuál es la fecha de reserva de mesa? Por favor, indícame dia y luego mes")
        fecha_in_m_str = listen()
        fecha_in_m = dateparser.parse(fecha_in_m_str + "/2023", languages=['es'])
        if fecha_in_m is None:
            speak("No pude entender la fecha de reserva. Intenta de nuevo.")
            return
        fecha_in_m = fecha_in_m.replace(year=2023)
        fecha_in_m_str = fecha_in_m.strftime("%d/%m/%Y")
        
        ref.child("Reserva").child("Restaurante").update({
            "ReservaMesa": fecha_in_m_str,
        })
        print(f"¡Listo! " + name + ", tu reserva ha sido registrada para el "+ fecha_in_m_str +", un total de "+ str(num_mesas) +" mesas.")
        speak(f"¡Listo! " + name + ", tu reserva ha sido registrada para el "+ fecha_in_m_str +", un total de "+ str(num_mesas) +" mesas.")

def modificar_reserva_restaurant():
    speak("¿Cuál es tu DNI?")
    print("¿Cuál es tu DNI?")
    dni = listen()
    dni = re.sub(r"\s+", "", dni) # eliminar espacios en blanco
    if dni == "":
        speak("No pude entender tu DNI. Intenta de nuevo.")
        print("No pude entender tu DNI. Intenta de nuevo.")
        return
    ref = db.reference('/Clientes/' + dni)
    data = ref.get()
    if data:
        print(data['Nombre'])
        speak("Bienvenido " + data['Nombre'] + "veo que usted tiene una reserva para el " + data['Reserva']['Restaurante']['ReservaMesa'] + "un total de " + str(data['Reserva']['Restaurante']['CantidadMesas']) + "mesas")
        print("Bienvenido " + data['Nombre'] + "veo que usted tiene una reserva para el " + data['Reserva']['Restaurante']['ReservaMesa'] + "un total de " + str(data['Reserva']['Restaurante']['CantidadMesas']) + "mesas")
        speak("Procederemos a hacer su nueva reserva")
        print("Procederemos a hacer su nueva reserva")
        num_mesas = calcular_num_mesas()
        speak("¿Cuál es la fecha de reserva de mesa? Por favor, indícame dia y luego mes")
        print("¿Cuál es la fecha de reserva de mesa? Por favor, indícame dia y luego mes")
        fecha_in_m_str = listen()
        fecha_in_m = dateparser.parse(fecha_in_m_str + "/2023", languages=['es'])
        if fecha_in_m is None:
            speak("No pude entender la fecha de reserva. Intenta de nuevo.")
            print("No pude entender la fecha de reserva. Intenta de nuevo.")
            return
        fecha_in_m = fecha_in_m.replace(year=2023)
        fecha_in_m_str = fecha_in_m.strftime("%d/%m/%Y")

        ref.child("Reserva").child("Restaurante").update({
            "ReservaMesa": fecha_in_m_str,
            "CantidadMesas" : num_mesas,
        })

        print(f"¡Listo! {data['Nombre']}, tu reserva ha sido modificada para el {fecha_in_m_str}, un total de {num_mesas} mesas.")
        speak(f"¡Listo! {data['Nombre']}, tu reserva ha sido modificada para el {fecha_in_m_str}, un total de {num_mesas} mesas.")

    else:
        print("No se encontraron datos para el DNI " + dni)
        speak("No se encontraron datos para el DNI " + dni)
        print("Entonces no tienes reservas a este DNI")
        speak("Entonces no tienes reservas a este DNI")
        print("¿Desea realizar una reserva?")
        speak("¿Desea realizar una reserva?")
        respuesta = listen()
        if respuesta == "si":
            modificar_reserva_restaurant()
        else:
            return
        
def cancelar_reserva_mesa():
    speak("¿Cuál es tu DNI?")
    print("¿Cuál es tu DNI?")
    dni = listen()
    dni = re.sub(r"\s+", "", dni) # eliminar espacios en blanco
    if dni == "":
        speak("No pude entender tu DNI. Intenta de nuevo.")
        print("No pude entender tu DNI. Intenta de nuevo.")
        return
    ref = db.reference('/Clientes/' + dni)
    data = ref.get()
    if data and 'Reserva' in data:
        reserva_data = data['Reserva']
        if 'Restaurante' in reserva_data:
            rest_data = reserva_data['Restaurante']
            if 'ReservaMesa' in rest_data:
                fecha_reserva = rest_data['ReservaMesa']
                speak(f"Tu reserva para el {fecha_reserva} ha sido cancelada.")
                print(f"Tu reserva para el {fecha_reserva} ha sido cancelada.")
                ref.child("Reserva").child("Restaurante").update({
                    "ReservaMesa": None,
                })
                return
    speak("No se encontró una reserva activa para el DNI " + dni)
    print("No se encontró una reserva activa para el DNI " + dni)


def hotel_service():
    speak("¿Qué acción deseas realizar? ¿Reserva, Información, Modificación o Cancelacion de Reserva?")
    print("¿Qué acción deseas realizar? ¿Reserva, Información, Modificación o Cancelacion de Reserva?")
    hotel_action = listen().lower()

    if hotel_action == "reserva":
        reserve_room()

    elif hotel_action == "información":
        speak("Nuestro hotel cuenta con habitaciones cómodas y un restaurante de primera clase. ¿Qué más te gustaría saber?")

    elif hotel_action == "modificación de reserva":
        update_reservation()

    elif hotel_action == "cancelación de reserva":
        cancel_hotel_reservation()

    else:
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path('prueba-agente-dnpf', '111280437199364536029')
        text_input = dialogflow.types.TextInput(text=hotel_action, language_code="es")
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session, query_input=query_input)
        fulfillment_text = response.query_result.fulfillment_text
        print("Respuesta de Dialogflow: {}".format(response.query_result.fulfillment_text))
        speak(fulfillment_text)
    
def restaurant_service():
    speak("¿Qué acción deseas realizar? ¿Reserva, Información , Modificación, Cancelacion de Reserva o visualizar carta del restaurante ?")
    print("¿Qué acción deseas realizar? ¿Reserva, Información , Modificación, Cancelacion de Reserva o visualizar carta del restaurante ?")
    restaurant_action = listen().lower()

    if restaurant_action == "reserva":
        reserve_mesa()

    elif restaurant_action == "información":
        speak("Nuestro restaurante ofrece una variedad de platos deliciosos y una extensa lista de vinos. ¿Te gustaria saber nuestros platillos o Qué más te gustaría saber?")

    elif restaurant_action == "modificación de reserva":
        modificar_reserva_restaurant()

    elif restaurant_action == "cancelación de reserva":
        cancelar_reserva_mesa()

    else:
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path('prueba-agente-dnpf', '111280437199364536029')
        text_input = dialogflow.types.TextInput(text=restaurant_action, language_code="es")
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session, query_input=query_input)
        fulfillment_text = response.query_result.fulfillment_text
        print("Respuesta de Dialogflow: {}".format(response.query_result.fulfillment_text))
        speak(fulfillment_text)
    
def handle_service():
    speak("¿Qué tipo de servicio deseas? ¿Hotel o Restaurante?")
    print("¿Qué tipo de servicio deseas? ¿Hotel o Restaurante?")
    service_type = listen().lower()
    if service_type == "hotel":
        hotel_service()

    elif service_type == "restaurante":
        restaurant_service()
    
def main():
    speak( f"Hola, soy {bot_name}, un chatbot creado por {bot_creator} y tengo {bot_age}.")
    print( f"Hola, soy {bot_name}, un chatbot creado por {bot_creator} y tengo {bot_age}.")

    while True:
        speak("¿En que puedo ayudarte?")
        print("¿En que puedo ayudarte?")
        user_input = listen().lower()
        
        if user_input == "servicio":
            handle_service()

        else:
            session_client = dialogflow.SessionsClient()
            session = session_client.session_path('prueba-agente-dnpf', '111280437199364536029')
            text_input = dialogflow.types.TextInput(text=user_input, language_code="es")
            query_input = dialogflow.types.QueryInput(text=text_input)
            response = session_client.detect_intent(session=session, query_input=query_input)
            fulfillment_text = response.query_result.fulfillment_text
            print("Respuesta de Dialogflow: {}".format(response.query_result.fulfillment_text))
            speak(fulfillment_text)
            if response.query_result.action == "input.farewell": 
                break
            elif response.query_result.action == "input.servicio": 
                handle_service()
            elif response.query_result.action == "input.hotel": 
                hotel_service()
            elif response.query_result.action == "input.restaurant": 
                restaurant_service()


if __name__ == "__main__":
    main()
