import os
import pyttsx3
import speech_recognition as sr
import sqlite3
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


firebase_sdk =credentials.Certificate('botreservas-386400-firebase-adminsdk-1nqww-9a3e7682a6.json')
firebase_admin.initialize_app(firebase_sdk,{'databaseURL': 'https://botreservas-386400-default-rtdb.firebaseio.com/'})

ref =db.reference

conn = sqlite3.connect('hotel.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS rooms (name text, checkin_date text, checkout_date text)''')
c.execute('''CREATE TABLE IF NOT EXISTS restaurant (name text, reservation_date text, reservation_time text)''')


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

def update_reservation():
    speak("¿Cuál es tu nombre?")
    name = listen()
    speak("¿Cuál es la nueva fecha de entrada?")
    new_checkin_date = listen()
    speak("¿Cuál es la nueva fecha de salida?")
    new_checkout_date = listen()
    c.execute("UPDATE rooms SET checkin_date = ?, checkout_date = ? WHERE name = ?", (new_checkin_date, new_checkout_date, name))
    conn.commit()
    speak(f"¡Listo! Tu reserva ha sido actualizada para el {new_checkin_date} hasta el {new_checkout_date}.")
    
def reserve_room():
    speak("¿Cuál es tu nombre?")
    name = listen()
    if name == "":
        speak("No pude entender tu nombre. Intenta de nuevo.")
        return
    speak("¿Cuál es la fecha de entrada?")
    checkin_date = listen()
    if checkin_date == "":
        speak("No pude entender la fecha de entrada. Intenta de nuevo.")
        return
    speak("¿Cuál es la fecha de salida?")
    checkout_date = listen()
    if checkout_date == "":
        speak("No pude entender la fecha de salida. Intenta de nuevo.")
        return
    c.execute("INSERT INTO rooms VALUES (?, ?, ?)", (name, checkin_date, checkout_date))
    conn.commit()
    speak(f"¡Listo! Tu reserva ha sido registrada para el {checkin_date} hasta el {checkout_date}.")


def main():
    speak(f"Hola, soy {bot_name}, un chatbot creado por {bot_creator} y tengo {bot_age}. ¿En qué puedo ayudarte?, escoge una de las opciones de servicio")

    while True:
        speak("¿Qué tipo de servicio deseas? ¿Hotel o Restaurante?")
        service_type = listen().lower()

        if service_type == "hotel":
            speak("¿Qué acción deseas realizar? ¿Reserva, Información o Modificación de Reserva?")
            hotel_action = listen().lower()

            if hotel_action == "reserva":
                reserve_room()

            elif hotel_action == "información":
                speak("Nuestro hotel cuenta con habitaciones cómodas y un restaurante de primera clase. ¿Qué más te gustaría saber?")

            elif hotel_action == "modificación de reserva":
                update_reservation()

            else:
                speak("Lo siento, no entendí tu acción. Por favor intenta de nuevo.")

        elif service_type == "restaurante":
            speak("¿Qué acción deseas realizar? ¿Reserva, Información o Modificación de Reserva?")
            restaurant_action = listen().lower()

            if restaurant_action == "reserva":
                speak("¿Cuál es tu nombre?")
                name = listen()
                speak("¿Cuál es la fecha de la reserva?")
                reservation_date = listen()
                speak("¿A qué hora te gustaría reservar?")
                reservation_time = listen()
                c.execute("INSERT INTO restaurant VALUES (?, ?, ?)", (name, reservation_date, reservation_time))
                conn.commit()
                speak(f"¡Listo! Tu reserva ha sido registrada para el {reservation_date} a las {reservation_time}.")

            elif restaurant_action == "información":
                speak("Nuestro restaurante ofrece una variedad de platos deliciosos y una extensa lista de vinos. ¿Qué más te gustaría saber?")

            elif restaurant_action == "modificación de reserva":
                speak("Lo siento, actualmente no es posible modificar reservas en nuestro restaurante. ¿Te gustaría hacer una nueva reserva?")
                response = listen().lower()

                if response == "sí":
                    speak("¿Cuál es tu nombre?")
                    name = listen()
                    speak("¿Cuál es la fecha de la reserva?")
                    reservation_date = listen()
                    speak("¿A qué hora te gustaría reservar?")
                    reservation_time = listen()
                    c.execute("INSERT INTO restaurant VALUES (?, ?, ?)", (name, reservation_date, reservation_time))
                    conn.commit()
                    speak(f"¡Listo! Tu reserva ha sido registrada para el {reservation_date} a las {reservation_time}.")

                else:
                    speak("Entendido, ¿En qué más puedo ayudarte?")

            else:
                speak("Lo siento, no entendí tu acción. Por favor intenta de nuevo.")

        

        else:
            speak("Lo siento, no entendí tu servicio. Por favor intenta de nuevo.")


if __name__ == "__main__":
    main()
