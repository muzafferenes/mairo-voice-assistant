import sys
import os
import json
import datetime
import sqlite3
import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QEvent
from resemblyzer import VoiceEncoder, preprocess_wav
from PyQt5.QtCore import QTimer
import sounddevice as sd



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("mairo.ui", self)

        # Hover info kutusu
        self.labelInfo.installEventFilter(self)
        self.sesKaytInfo.setVisible(False)

        # Veritabanı bağlantısı
        self.conn = sqlite3.connect("users.db")
        self.cursor = self.conn.cursor()

        # Buton eventleri
        self.sesTainmaButton.clicked.connect(self.ses_tanit)
        self.KayitlarInfo.clicked.connect(self.kayitlari_goster)
        self.baslatButton.clicked.connect(self.baslat)

        self.setStyleSheet("""
            QMainWindow {
                background-image: url(mairoArkaPlan.jpg);
                background-repeat: no-repeat;
                background-position: center;
            }
            """)
        self.resize(450, 550)
        self.setFixedSize(450, 550)

        self.pcButton.setCheckable(True)
        self.mairoButton.setCheckable(True)

        self.label.setFixedSize(30, 30)
        self.label.setStyleSheet("""
        QLabel {
            background-color: red;
            border-radius: 15px;
        }
        """)
        self.recTimer = QTimer()
        self.recTimer.timeout.connect(self.toggle_rec_indicator)
        self.recVisible = False

        devices = sd.query_devices()
        self.mic_devices = []

        # Önce tüm input cihazlarını ekle
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                text = f"{i}: {d['name']}"
                self.comboMic.addItem(text)
                self.mic_devices.append(i)

        # Eğer hiç input cihazı yoksa uyar
        if not self.mic_devices:
            QMessageBox.critical(self, "Hata",
                                 "Hiç mikrofon bulunamadı! Bilgisayarınıza mikrofon bağlı mı kontrol edin.")

    def toggle_rec_indicator(self):
        if self.recVisible:
            # Sönük durum (gri)
            self.lblRec.setStyleSheet("""
                QLabel {
                    background-color: rgba(150, 150, 150, 0.3);
                    border-radius: 15px;
                    min-width: 30px;
                    min-height: 30px;
                    max-width: 30px;
                    max-height: 30px;
                }
            """)
        else:
            # Yanık durum (kırmızı)
            self.lblRec.setStyleSheet("""
                QLabel {
                    background-color: red;
                    border-radius: 15px;
                    min-width: 30px;
                    min-height: 30px;
                    max-width: 30px;
                    max-height: 30px;
                }
            """)
        self.recVisible = not self.recVisible

    def eventFilter(self, obj, event):
        if obj == self.labelInfo:
            if event.type() == QEvent.Enter:
                self.sesKaytInfo.setVisible(True)
            elif event.type() == QEvent.Leave:
                self.sesKaytInfo.setVisible(False)
        return super().eventFilter(obj, event)

    def baslat(self):
        # Aktif trigger kelimeleri topla
        triggers = []
        if self.pcButton.isChecked():
            triggers.append("hey bilgisayar")
        if self.mairoButton.isChecked():
            triggers.append("hey mairo")

        if not triggers:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir trigger kelime seçin.")
            return

        # JSON dosyasına kaydet
        with open("trigger_config.json", "w", encoding="utf-8") as f:
            json.dump({"trigger_words": triggers}, f, ensure_ascii=False, indent=2)

        QMessageBox.information(self, "Bilgi", "Trigger kelimeler kaydedildi.\nArka plan dinleme başlatılacak.")

        # Şimdilik sadece arayüzü kapatıyoruz
        self.close()

    def ses_tanit(self):
        # Kullanıcı ismini al
        user_name = self.lineEdit.text().strip()
        if not user_name:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir isim girin.")
            return

        # ComboBox'tan seçili mikrofon indexini al
        selected_index = self.comboMic.currentIndex()
        device_id = self.mic_devices[selected_index]

        selected_index = self.comboMic.currentIndex()
        if selected_index < 0 or selected_index >= len(self.mic_devices):
            QMessageBox.critical(self, "Hata", "Geçerli bir mikrofon seçimi yapmalısınız.")
            return


        # Ses kaydı
        import sounddevice as sd
        from scipy.io.wavfile import write

        fs = 16000
        seconds = 15

        QMessageBox.information(self, "Bilgi", "Kayıt başlıyor. 15 saniye boyunca konuşun.")
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, device=device_id)
        sd.wait()

        # Klasör yoksa oluştur
        if not os.path.exists("embeddings"):
            os.makedirs("embeddings")

        # WAV dosyası kaydet
        wav_path = f"embeddings/{user_name}.wav"
        write(wav_path, fs, recording)

        # Embedding çıkar
        wav = preprocess_wav(wav_path)
        encoder = VoiceEncoder()
        embedding = encoder.embed_utterance(wav)

        # Embedding dosyası kaydet
        embedding_path = f"embeddings/{user_name}.npy"
        np.save(embedding_path, embedding)

        # Veritabanına kaydet
        self.cursor.execute("""
            INSERT INTO users (name, embedding_path, created_at)
            VALUES (?, ?, ?)
        """, (user_name, embedding_path, datetime.datetime.now()))
        self.conn.commit()

        QMessageBox.information(self, "Başarılı", f"{user_name} kullanıcısı kaydedildi.")


    def kayitlari_goster(self):
        # Veritabanından kullanıcıları çek
        self.cursor.execute("SELECT name, created_at FROM users")
        records = self.cursor.fetchall()

        # Eğer hiç kayıt yoksa
        if not records:
            QMessageBox.information(self, "Bilgi", "Hiç kullanıcı kaydı bulunamadı.")
            return

        # Kullanıcı listesini metin olarak hazırla
        text = ""
        for r in records:
            text += f"{r[0]} - {r[1]}\n"

        # Mesaj kutusunda göster
        QMessageBox.information(self, "Kayıtlı Kullanıcılar", text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
