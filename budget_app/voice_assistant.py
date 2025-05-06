# voice_assistant.py

import speech_recognition as sr
import pyttsx3

# Initialize speech engine
engine = pyttsx3.init()

# Function to speak out a given text
def speak(text):
    """
    Use text-to-speech to speak the given text.
    """
    engine.say(text)
    engine.runAndWait()

# Function to capture voice input and convert to text
def get_voice_command():
    """
    Capture voice from the microphone and return as text.
    
    Returns:
        str: Recognized speech text or None if not understood
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            # Try to recognize the speech
            command = recognizer.recognize_google(audio)
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I could not understand that.")
            return None
        except sr.RequestError:
            speak("Speech service is unavailable.")
            return None
