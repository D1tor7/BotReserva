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

engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "prueba-agente-dnpf-c3237e543e4f.json"
firebase_sdk =credentials.Certificate('botreservas-386400-firebase-adminsdk-1nqww-9a3e7682a6.json')
firebase_admin.initialize_app(firebase_sdk,{'databaseURL': 'https://botreservas-386400-default-rtdb.firebaseio.com/'})


conn = sqlite3.connect('pruebadialog.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS example_table (date text, value real)''')
now = datetime.datetime.now().isoformat()
c.execute("INSERT INTO example_table VALUES (?, ?)", (now, math.pi))
conn.commit()
conn.close()

dni = '74707181'
ref = db.reference('Cliente/74707181/Reserva/Habitacion/401')
data = ref.get()

engine = pyttsx3.init()
engine.say("Hola mundo!")
engine.runAndWait()

r = sr.Recognizer()
with sr.Microphone() as source:
    print("Di algo:")
    audio = r.listen(source)

try:
    text = r.recognize_google(audio, language='es-ES')
    print("Dijiste: " + text)
except sr.UnknownValueError:
    print("No se pudo entender el audio")
except sr.RequestError as e:
    print("No se pudo obtener resultados; {0}".format(e))

session_client = dialogflow.SessionsClient()
session = session_client.session_path('prueba-agente-dnpf', '111280437199364536029')
text_input = dialogflow.types.TextInput(text=text, language_code="es")
query_input = dialogflow.types.QueryInput(text=text_input)
response = session_client.detect_intent(session=session, query_input=query_input)
fulfillment_text = response.query_result.fulfillment_text
print("Respuesta de Dialogflow: {}".format(response.query_result.fulfillment_text))
speak(fulfillment_text)
