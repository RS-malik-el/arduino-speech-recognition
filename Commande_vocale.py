#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
	@AUTEUR: RACHEL SYSTEME
	DATE   : 11 MAI 2022
	
	Board : @ ARDUINO
	Ce programme consiste à allumer une série de deux lampes en utilisant 
	les commandes vocales. 
	NB:
		Avant d'exécuter le programme, rassurez - vous d'avoir installé au
		préalable tous les modules nécessaires au bon fonctionnement du
		programme.
		Téleverser la bibliothète Standard Firmata à l'arduino.
	Inconvénient : une fois que la connexion est établie et que vous 
		retiré la carte arduino, le programme fonctionne comme si la carte
		n'a jamais été retirée
"""
##########################################################################
import speech_recognition as sr
import pyaudio
import pygame
import serial
import wave
import os
##########################################################################
import pyfirmata as pf
##########################################################################

#-----------------------------COMMANDES-----------------------------------
_LAMPE_1_ON  = "ALLUME LA LAMPE 1"
_LAMPE_2_ON  = "ALLUME LA LAMPE 2"
_LAMPES_ON   = "ALLUME TOUTES LES LAMPES"
_LAMPE_1_OFF = "ÉTEINS LA LAMPE 1"
_LAMPE_2_OFF = "ÉTEINS LA LAMPE 2"
_LAMPES_OFF  = "ÉTEINS TOUTES LES LAMPES"
#------------------------REPONSES(fichiers audios)------------------------
_R_L1_ON 	= "son/L1_ON.mp3"
_R_L2_ON 	= "son/L2_ON.mp3"
_R_L1_OFF 	= "son/L1_OFF.mp3"
_R_L2_OFF 	= "son/L2_OFF.mp3"
_R_L_ON 	= "son/L_ON.mp3"
_R_L_OFF 	= "son/L_OFF.mp3"
_R_A_L1_ON 	= "son/A_L1_ON.mp3"
_R_A_L2_ON 	= "son/A_L2_ON.mp3"
_R_A_L1_OFF = "son/A_L1_OFF.mp3"
_R_A_L2_OFF = "son/A_L2_OFF.mp3"
_R_A_L_ON 	= "son/A_L_ON.mp3"
_R_A_L_OFF 	= "son/A_L_OFF.mp3"
_R_ERROR 	= "son/error.mp3"
#------------------------Variables du fichier audio----------------------
pygame.mixer.init()
chunk = 1024  			# Enregistrement en morceaux de 1024 échantillons
sample_format = pyaudio.paInt16  				# 16 bits par échantillon
channels = 2 	
fs = 44100  			# Enregistrement à 44100 échantillons par seconde
seconds = 3 			# Durée d'enregistrement
filename = "INPUT.wav" 	# Nom du fichier
Input_Text  = ""		# audio traduit en texte
#------------------------Variables de contrôle arduino----------------------
_PORT		= "COM5"# port utiliser pour connecté l'arduino
_PIN1		= 2 	# pin lampe 1 (digital pin sauf 0 et 1 "rx tx")
_PIN2		= 3		# pin lampe 1 (digital pin sauf 0 et 1 "rx tx")
_ON  		= True  #
_OFF 		= False #
etat_1 		= _OFF 	# état initial de la lampe 1
etat_2 		= _OFF	# état initial de la lampe 2
arduino 	= None 	# variable type arduino
led_1  		= None	# variable type arduino
led_2  		= None	# variable type arduino

##########################################################################
"""
	Permet d'initialiser l'arduino:
	VARIABLE:
		run : type bool, rôle: permet d'exécuter le programme principal si
			True
"""
def Init_Arduino():
	global run, arduino, led_1, led_2
	try:
	    arduino = pf.Arduino(_PORT)
	    led_1 = arduino.get_pin("d:{}:o".format(_PIN1))
	    led_2 =	arduino.get_pin("d:{}:o".format(_PIN2))
	    led_1.write(etat_1)
	    led_2.write(etat_2)
	    print("\n\nArduino connecté\n")
	    run = True
	except serial.serialutil.SerialException:
	    print("\n\nEchec connexion : port indiponible")
	    run = False
	except pf.pyfirmata.InvalidPinDefError:
	    print("""\n\nEchec connexion : pin non disponible\n
	    Ne pas utiliser les pins RX et TX""")
	    arduino.exit()
	    run = False

"""
	Permet d'allumer les lampes:
	Paramètres:
		etat1, etat2 : type bool, rôle : indique les états des lampes 
	Utiliser dans la fonction : TraitementCommande()
"""
def gestionLampes(etat1,etat2):
	global led_1, led_2
	led_1.write(etat1)
	led_2.write(etat2)

"""
	Permet de jouer le son en arrière plan
	Paramètre:
		file : type mp3, fichier à jouer
	Utiliser dans la fonction : TraitementCommande()
"""
def ArriereVoix(file):
	try:
		pygame.mixer.music.load(file)	
		pygame.mixer.music.play()
				
	except pygame.error:
		print("fichier mp3 non trouvé")


# Permet d'enregistrer le son pendant quelque secondes"
def EnregistrementVocal():
	
	# Création d'une interface vers PortAudio
	p = pyaudio.PyAudio() 
	stream = p.open(format=sample_format,
		                channels=channels,
		                rate=fs,
		                frames_per_buffer=chunk,
		                input=True)

	# Initialise le tableau pour stocker les cadres
	frames = []  
	print("enregistrement encours.............\n")
	# Stocker les données en morceaux pendant le nombre de secondes requis
	for i in range(0, int(fs / chunk * seconds)):
		data = stream.read(chunk)
		frames.append(data)

	# Arrêter et fermer le flux
	stream.stop_stream()
	stream.close()
	# Ferme l'interface PortAudio
	p.terminate()

	# Enregistre les données enregistrées dans un fichier WAV
	wf = wave.open(filename, 'wb')
	wf.setnchannels(channels)
	wf.setsampwidth(p.get_sample_size(sample_format))
	wf.setframerate(fs)
	wf.writeframes(b''.join(frames))
	wf.close()

"""
	Permet de traduire l'audio en texte. Après traduction,
	le fichier audio est supprimé.
	Variable:
		Input_Text : type str, rôle : contient le texte traduit
"""
def TraitementVocal():
	global Input_Text, run

	# Déclaration de l'objet
	r = sr.Recognizer()
	try:
		# Ouverture du fichier
		with sr.AudioFile(filename) as source:
			# Ecoute les données (télécharge les données) 
			audio_data = r.record(source)
			# conversion de l'audio en texte
			Input_Text = r.recognize_google(audio_data,language="fr")
			Input_Text = Input_Text.upper()
		os.remove(filename) # Suppression du fichier 
	except sr.UnknownValueError:
		print(".....................................")
	except sr.RequestError:
		print("Vérifier votre connexion internet\n")
		run = False


"""
	Permet d'envoyer les instructions d'allumage ou non des lampes,
	Le son est joué en arrière-plan si une condition est vérifiée.
"""
def TraitementCommande():
	global etat_1, etat_2
	success = False	# Vérifie si la commande est correcte.

	if Input_Text == _LAMPE_1_ON : # lampe 1 on
		if etat_1 == _ON:
			ArriereVoix(_R_A_L1_ON)
		else:
			etat_1 = _ON
			ArriereVoix(_R_L1_ON)
		success = True

	if Input_Text == _LAMPE_2_ON : # lampe 2 on
		if etat_2 == _ON:
			ArriereVoix(_R_A_L2_ON)
		else:
			etat_2 = _ON
			ArriereVoix(_R_L2_ON)
		success = True

	if Input_Text == _LAMPE_1_OFF : # lampe 1 off
		if etat_1 == _OFF:
			ArriereVoix(_R_A_L1_OFF)
		else:
			etat_1 = _OFF
			ArriereVoix(_R_L1_OFF)
		success = True

	if Input_Text == _LAMPE_2_OFF : # lampe 2 off
		if etat_2 == _OFF:
			ArriereVoix(_R_A_L2_OFF)
		else:
			etat_2 = _OFF
			ArriereVoix(_R_L2_OFF)
		success = True

	if Input_Text == _LAMPES_ON : # lampe 1 et 2 on
		if etat_1 == _ON and etat_2 == _ON:
			ArriereVoix(_R_A_L_ON)
		else:
			etat_1 = _ON
			etat_2 = _ON
			ArriereVoix(_R_L_ON)
		success = True
	
	if Input_Text == _LAMPES_OFF : # lampe 1 et 2 off
		if etat_1 == _OFF and etat_2 == _OFF:
			ArriereVoix(_R_A_L_OFF)
		else:
			etat_1 = _OFF
			etat_2 = _OFF
			ArriereVoix(_R_L_OFF)
		success = True
			
	gestionLampes(etat1 = etat_1, etat2 = etat_2) # Mise à jour des sorties

	if not success and run:
		ArriereVoix(_R_ERROR)
##########################################################################
#............................PROGRAMME PRINCIPAL..........................
Init_Arduino()
if run:
	while True:
		print("taper \"stop\" pour arrêter le programme")
		saisie = input("taper \"ok rs\" pour démarrer l'enregistrement :\n")
		saisie = saisie.strip()
			
		if saisie == "ok rs":
			EnregistrementVocal()
			TraitementVocal()
			TraitementCommande()
			print(Input_Text,"\n")
			Input_Text = ""

		if saisie == "stop":
			gestionLampes(_OFF, _OFF)
			print("\nFIN DE PROGRAMME")
			arduino.exit()
			break
			
		if not run:
			arduino.exit()
			break
