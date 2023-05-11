import os
import pyttsx3
import speech_recognition as sr
import sqlite3
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


firebase_sdk =credentials.Certificate('botreservas-386400-firebase-adminsdk-1nqww-9a3e7682a6.json')
firebase_admin.initialize_app(firebase_sdk,{'databaseURL': 'https://botreservas-386400-default-rtdb.firebaseio.com/'})

dni = '74707181'
ref = db.reference('Cliente/74707181/Reserva/Habitacion/401')
data = ref.get()
if data:
    print(f"¡Listo! {data['Nombre']}, tu reserva ha sido registrada para el {fechaIn} hasta el {FechaSal}, un total de {NumDias} días.")
else:
    print("No se encontraron datos para el DNI " + dni)
    
