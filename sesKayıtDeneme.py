import sounddevice as sd
import soundfile as sf

fs = 16000
seconds = 5

print("Mikrofon listele:")
print(sd.query_devices())

device_index = int(input("Kullanmak istediğin mikrofonun index numarasını yaz: "))

print("Kayıt başlıyor...")
recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, device=device_index)
sd.wait()
sf.write("test_record.wav", recording, fs)
print("Kayıt tamam! 'test_record.wav' dosyasını dinleyebilirsin.")
