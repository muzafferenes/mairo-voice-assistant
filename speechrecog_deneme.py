import speech_recognition

recognizer = speech_recognition.Recognizer()

while True:
    try:
        with speech_recognition.Microphone() as mic:
            recognizer.adjust_for_ambient_noise(mic, duration=0.2)
            print("Dinleniyor... Konuş!")
            audio = recognizer.listen(mic)

            # Basit Google tanıma
            text = recognizer.recognize_google(audio)
            text = text.lower()

            print(f"Tanındı: {text}")

    except speech_recognition.UnknownValueError:
        print("Anlamadım, tekrar dene.")
        continue
