# 🚀 SillyTavern AiO (All-in-One) Installer

Dieses Repository bietet eine automatisierte Komplettlösung für die Installation von **SillyTavern**, **KoboldCPP** und **Silero TTS**. Mit nur einem Klick wird eine isolierte Umgebung eingerichtet, die alle Komponenten für ein lokales KI-Rollenspiel-Erlebnis vereint.

## ✨ Features

- **🎭 Full Suite**: Installiert das SillyTavern Frontend, das KoboldCPP Backend (für LLMs) und Silero (für Sprachausgabe).
- **🔒 Isolierte Umgebung**: Verwendet ein Python venv, um dein System sauber zu halten.
- **🤖 Smart Download**: Lädt automatisch die aktuellsten Versionen direkt von den offiziellen GitHub-Quellen herunter.
- **⚡ Einfachheit**: Kein manuelles Verschieben von Dateien oder kompliziertes Konfigurieren von Pfaden nötig.
- **🇷🇺 Silero TTS**: Integrierte Unterstützung für russische Sprachausgabe.

## 📋 Voraussetzungen

Bevor du startest, stelle sicher, dass folgende Software installiert ist:

- **Python 3.12** (muss unter `C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe` verfügbar sein)
- **Git** für Windows ([Download](https://git-scm.com/download/win))
- **curl** (ist standardmäßig in Windows 10/11 enthalten)

## 🛠️ Installation

### Schritt-für-Schritt

1. **Repository klonen oder herunterladen**
   ```bash
   git clone https://github.com/DEIN_BENUTZERNAME/SillyTavernAiO.git
   cd SillyTavernAiO/install
   ```

2. **Installer ausführen**
   
   Doppelklicke auf `install.bat` oder führe es über die Kommandozeile aus:
   ```cmd
   install.bat
   ```

3. **Warten bis der Prozess abgeschlossen ist**
   
   Das Skript übernimmt nun alles automatisch:
   - Erstellt eine virtuelle Python-Umgebung
   - Klont SillyTavern
   - Lädt KoboldCPP herunter
   - Installiert Silero TTS mit allen Abhängigkeiten

## 📁 Projektstruktur

Nach erfolgreicher Installation sieht deine Ordnerstruktur wie folgt aus:

```
SillyTavernAiO/
├── install/
│   ├── install.bat          # Haupt-Installer (Batch)
│   ├── install_script.py    # Installationsskript (Python)
│   └── venv/                # Virtuelle Python-Umgebung
├── SillyTavern/             # SillyTavern Frontend
├── koboldcpp/               # KoboldCPP Backend
│   └── koboldcpp.exe
└── silero_tts/              # Silero TTS Integration
    ├── silero_setup.py
    └── requirements.txt
```

## 🚀 Verwendung

### SillyTavern starten

```bash
cd SillyTavern
node server.js
```

Öffne dann deinen Browser und gehe zu `http://localhost:8000`

### KoboldCPP starten

```bash
cd koboldcpp
koboldcpp.exe --model DEIN_MODELLL_PFAD
```

### Silero TTS verwenden

Das Silero-Skript wurde im Ordner `silero_tts/` eingerichtet. Du kannst es direkt in SillyTavern integrieren oder separat nutzen:

```bash
cd silero_tts
venv\Scripts\activate
python silero_setup.py
```

## ⚙️ Konfiguration

### Python-Pfad anpassen

Falls sich Python bei dir an einem anderen Ort befindet, öffne `install.bat` und passe diese Zeile an:

```batch
SET PYTHON_EXE="C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe"
```

### Modell-Pfade konfigurieren

Nach der Installation musst du in SillyTavern die Pfade zu deinen Modellen und zu KoboldCPP konfigurieren. Dies geschieht über das SillyTavern Web-Interface unter **API Connections**.

## ❓ Troubleshooting

### "Python nicht gefunden"
- Stelle sicher, dass Python 3.12 installiert ist
- Überprüfe den Pfad in der `install.bat`

### "Git nicht gefunden"
- Installiere Git von [git-scm.com](https://git-scm.com/)
- Starte das Terminal neu nach der Installation

### "Zugriffsverweigerung"
- Führe `install.bat` als Administrator aus
- Stelle sicher, dass du Schreibrechte im Installationsverzeichnis hast

### Installation bricht ab
- Überprüfe deine Internetverbindung
- Manche Antivirenprogramme können den Download blockieren
- Prüfe die `install_script.py` auf detaillierte Fehlermeldungen

## 📝 Hinweise

- **Speicherplatz**: Stelle sicher, dass mindestens 5 GB freier Speicherplatz verfügbar sind
- **Internetverbindung**: Wird für den Download aller Komponenten benötigt
- **Erster Start**: Der erste Start kann einige Minuten dauern, abhängig von deiner Internetgeschwindigkeit

## 🤝 Contributing

Fehler gefunden oder Verbesserungen? Erstelle gerne einen Pull Request oder eröffne ein Issue!

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Die installierten Komponenten (SillyTavern, KoboldCPP, Silero) unterliegen ihren jeweiligen Lizenzen.

## 🔗 Nützliche Links

- [SillyTavern GitHub](https://github.com/SillyTavern/SillyTavern)
- [KoboldCPP GitHub](https://github.com/LostRuins/koboldcpp)
- [Silero TTS GitHub](https://github.com/snakers4/silero-models)
- [SillyTavern Dokumentation](https://docs.sillytavern.app/)

---

**Viel Spaß beim Erkunden deiner lokalen KI-Welt! 🎉**