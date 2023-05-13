import math
import os
import pyttsx3
import speech_recognition as sr
import sqlite3
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import re
import datetime
import dateparser


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
    name = listen()
    speak("¿Cuál es la nueva fecha de entrada?")
    new_checkin_date = listen()
    speak("¿Cuál es la nueva fecha de salida?")
    new_checkout_date = listen()
    c.execute(
        "UPDATE rooms SET checkin_date = ?, checkout_date = ? WHERE name = ?",
        (new_checkin_date, new_checkout_date, name),
    )
    conn.commit()
    speak(
        f"¡Listo! Tu reserva ha sido actualizada para el {new_checkin_date} hasta el {new_checkout_date}."
    )

def calcular_num_habitaciones():
    # Preguntar por el número de personas
    speak("¿Cuántas personas van a hospedarse?")
    npersonas_str = listen()
    try:
        npersonas = int(npersonas_str)
    except ValueError:
        speak("No pude entender el número de personas. Intenta de nuevo.")
        return
    if npersonas < 1:
        speak("Debe haber al menos una persona para hacer una reserva.")
        return

    if npersonas <= 2:
        num_habitaciones = 1
    else:
        num_habitaciones = math.ceil(npersonas / 2)
        speak(f"Usted debe reservar {num_habitaciones} habitaciones.")


def reserve_room():
    speak("¿Cuál es tu DNI?")
    dni = listen()
    dni = re.sub(r"\s+", "", dni)  # eliminar espacios en blanco
    if dni == "":
        speak("No pude entender tu DNI. Intenta de nuevo.")
        return

    ref = db.reference('/Clientes/' + dni)
    data = ref.get()
    if data:
        print(data['Nombre'])
        speak("Bienvenido " + data['Nombre'])
        calcular_num_habitaciones()
        speak("¿Qué habitacion deseas reservar?")
        Habitacion = listen()
        if Habitacion == "":
            speak("No pude entender el numero de habitacion. Intenta de nuevo.")
            return
        speak("¿Cuál es la fecha de entrada? Por favor, indícame dia y luego mes")
        fecha_in_str = listen()
        fecha_in = dateparser.parse(fecha_in_str + "/2023", languages=['es'])
        if fecha_in is None:
            speak("No pude entender la fecha de entrada. Intenta de nuevo.")
            return
        fecha_in = fecha_in.replace(year=2023)
        fecha_in_str = fecha_in.strftime("%d/%m/%Y")
        speak("¿Cuál es la fecha de salida? Por favor, indícame dia y luego mes")
        fecha_out_str = listen()
        fecha_out = dateparser.parse(fecha_out_str + "/2023", languages=['es'])
        if fecha_out is None:
            speak("No pude entender la fecha de salida. Intenta de nuevo.")
            return
        fecha_out = fecha_out.replace(year=2023)
        fecha_out_str = fecha_out.strftime("%d/%m/%Y")
        num_dias = (fecha_out - fecha_in).days
        if num_dias < 1:
            speak("La fecha de salida debe ser después de la fecha de entrada. Intenta de nuevo.")
            return
        ref.child("Reserva").child("Hotel").update({
            "Habitacion": Habitacion,
            "FechaIn": fecha_in_str,
            "FechaSal": fecha_out_str,
            "NumDias": num_dias,
            
            }
        )
        print(
            f"¡Listo! {data['Nombre']}, tu reserva ha sido registrada para el {fecha_in_str} hasta el {fecha_out_str}, un total de {num_dias} días."
        )
        speak(
            f"¡Listo! {data['Nombre']}, tu reserva ha sido registrada para el {fecha_in_str} hasta el {fecha_out_str}, un total de {num_dias} días."
        )
    else:
        print("No se encontraron datos para el DNI " + dni)
        speak("Veo que eres un cliente nuevo")
        speak("¿Cuál es tu nombre?")
        name = listen()
        reserva_ref = db.reference("/Clientes/" + dni)
        reserva_ref.set({"Nombre": name})
        speak("Bienvenido " + name)
        calcular_num_habitaciones()
        speak("¿Qué habitacion deseas reservar?")
        Habitacion = listen()
        if Habitacion == "":
            speak("No pude entender el numero de habitacion. Intenta de nuevo.")
            return
        speak("¿Cuál es la fecha de entrada? Por favor, indícame dia y luego mes")
        fecha_in_str = listen()
        fecha_in = dateparser.parse(fecha_in_str + "/2023", languages=["es"])
        if fecha_in is None:
            speak("No pude entender la fecha de entrada. Intenta de nuevo.")
            return
        fecha_in = fecha_in.replace(year=2023)
        fecha_in_str = fecha_in.strftime("%d/%m/%Y")
        speak("¿Cuál es la fecha de salida? Por favor, indícame dia y luego mes")
        fecha_out_str = listen()
        fecha_out = dateparser.parse(fecha_out_str + "/2023", languages=["es"])
        if fecha_out is None:
            speak("No pude entender la fecha de salida. Intenta de nuevo.")
            return
        fecha_out = fecha_out.replace(year=2023)
        fecha_out_str = fecha_out.strftime("%d/%m/%Y")
        num_dias = (fecha_out - fecha_in).days
        if num_dias < 1:
            speak(
                "La fecha de salida debe ser después de la fecha de entrada. Intenta de nuevo."
            )
            return
        ref.child("Reserva").child("Hotel").update({
            "Habitacion": Habitacion,
            "FechaIn": fecha_in_str,
            "FechaSal": fecha_out_str,
            "NumDias": num_dias
        })
        print(f"¡Listo!" + name + ", tu reserva ha sido registrada para el"+ fecha_in_str +" hasta el "+ fecha_out_str +", un total de "+ num_dias +" días.")
        speak(f"¡Listo!" + name + ", tu reserva ha sido registrada para el"+ fecha_in_str +" hasta el "+ fecha_out_str +" un total de "+ num_dias +" días.")



def main():
    speak(
        f"Hola, soy {bot_name}, un chatbot creado por {bot_creator} y tengo {bot_age}. ¿En qué puedo ayudarte?, escoge una de las opciones de servicio"
    )

    while True:
        speak("¿Qué tipo de servicio deseas? ¿Hotel o Restaurante?")
        service_type = listen().lower()

        if service_type == "hotel":
            speak(
                "¿Qué acción deseas realizar? ¿Reserva, Información o Modificación de Reserva?"
            )
            hotel_action = listen().lower()

            if hotel_action == "reserva":
                reserve_room()

            elif hotel_action == "información":
                speak(
                    "Nuestro hotel cuenta con habitaciones cómodas y un restaurante de primera clase. ¿Qué más te gustaría saber?"
                )

            elif hotel_action == "modificación de reserva":
                update_reservation()

            else:
                speak("Lo siento, no entendí tu acción. Por favor intenta de nuevo.")

        elif service_type == "restaurante":
            speak(
                "¿Qué acción deseas realizar? ¿Reserva, Información o Modificación de Reserva?"
            )
            restaurant_action = listen().lower()

            if restaurant_action == "reserva":
                speak("¿Cuál es tu nombre?")
                name = listen()
                speak("¿Cuál es la fecha de la reserva?")
                reservation_date = listen()
                speak("¿A qué hora te gustaría reservar?")
                reservation_time = listen()
                c.execute(
                    "INSERT INTO restaurant VALUES (?, ?, ?)",
                    (name, reservation_date, reservation_time),
                )
                conn.commit()
                speak(
                    f"¡Listo! Tu reserva ha sido registrada para el {reservation_date} a las {reservation_time}."
                )

            elif restaurant_action == "información":
                speak(
                    "Nuestro restaurante ofrece una variedad de platos deliciosos y una extensa lista de vinos. ¿Qué más te gustaría saber?"
                )

            elif restaurant_action == "modificación de reserva":
                speak(
                    "Lo siento, actualmente no es posible modificar reservas en nuestro restaurante. ¿Te gustaría hacer una nueva reserva?"
                )
                response = listen().lower()

                if response == "sí":
                    speak("¿Cuál es tu nombre?")
                    name = listen()
                    speak("¿Cuál es la fecha de la reserva?")
                    reservation_date = listen()
                    speak("¿A qué hora te gustaría reservar?")
                    reservation_time = listen()
                    c.execute(
                        "INSERT INTO restaurant VALUES (?, ?, ?)",
                        (name, reservation_date, reservation_time),
                    )
                    conn.commit()
                    speak(
                        f"¡Listo! Tu reserva ha sido registrada para el {reservation_date} a las {reservation_time}."
                    )

                else:
                    speak("Entendido, ¿En qué más puedo ayudarte?")

            else:
                speak("Lo siento, no entendí tu acción. Por favor intenta de nuevo.")

        else:
            speak("Lo siento, no entendí tu servicio. Por favor intenta de nuevo.")


if __name__ == "__main__":
    main()
