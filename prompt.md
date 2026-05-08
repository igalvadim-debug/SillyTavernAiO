# SillyTavern AiO - Installations- und Start-Skripte

## Aufgabe
Erstelle ein vollständiges, robustes Installationssystem für eine "SillyTavern All-in-One" (AiO) Umgebung unter Windows. Das System muss drei Hauptkomponenten automatisiert installieren, konfigurieren und starten: **Silero TTS**, **SillyTavern** und **KoboldCPP**.

## Anforderungen an die Skripte

### 1. `install.bat` (Haupt-Installer)
- **Python-Pfad:** Muss explizit den Python-Interpreter von `C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe` verwenden. Kein Vertrauen auf PATH oder System-Python.
- **Virtuelle Umgebung:** Erstellt ein virtuelles Environment (`venv`) im Installationsverzeichnis.
- **Ausführung:** Ruft `install_script.py` innerhalb des aktivierten venv auf.
- **Robustheit:** Enthält `pause`-Befehle bei Fehlern, damit der Benutzer Fehlermeldungen lesen kann.

### 2. `install_script.py` (Python-Installationslogik)
Dieses Skript übernimmt die eigentliche Installation der Komponenten:
- **Silero TTS:**
    - Erstellt den Ordner `D:\SillyTavernAiO\SileroTTS\models`.
    - **Modell-Logik:** Prüft, ob das russische Modell `v5_5_ru.pt` bereits im Modelle-Ordner liegt. Falls nein, lädt es automatisch herunter.
    - **Server-Erstellung:** Generiert eine `silero_api_server.py`, die dieses lokale Modell (`v5_5_ru.pt`) zwingend verwendet (mit Fallback nur wenn nötig) und einen Flask-Server auf Port **5002** bereitstellt.
    - Installiert benötigte Python-Pakete (`torch`, `torchaudio`, `flask`).
- **SillyTavern:**
    - Klont das SillyTavern-Repository nach `D:\SillyTavernAiO\SillyTavern`.
    - Führt `npm install` aus, um Abhängigkeiten zu installieren.
- **KoboldCPP:**
    - Lädt die neueste Version von `koboldcpp.exe` von GitHub Releases herunter.
    - Speichert es in `D:\SillyTavernAiO\KoboldCPP`.
    - Erstellt den Ordner `D:\SillyTavernAiO\KoboldCPP\models` (falls nicht vorhanden).

### 3. `start_all.bat` (The Orchestrator)
Dies ist das zentrale Startskript, das alle Dienste koordiniert:
- **Vorbereitung:** Aktiviert das virtuelle Environment.
- **Schritt 1: Silero TTS starten**
    - Startet den generierten `silero_api_server.py` im Hintergrund (via `start` Befehl).
    - Port: **5002**.
- **Schritt 2: KoboldCPP Logik**
    - Scannt den Ordner `D:\SillyTavernAiO\KoboldCPP\models` nach `.gguf` Dateien.
    - **Interaktion:** Zeigt eine nummerierte Liste der gefundenen Modelle im CMD-Fenster an.
    - Fordert den Benutzer auf, eine Nummer auszuwählen.
    - Startet `koboldcpp.exe --model [AusgewählteDatei] --port 5001` basierend auf der Auswahl.
- **Schritt 3: SillyTavern starten**
    - **Priorität:** Prüft, ob `D:\SillyTavernAiO\SillyTavern\Start.bat` existiert. Wenn ja, führe diese aus (`call Start.bat`).
    - **Fallback:** Falls keine `Start.bat` existiert, starte manuell über `node server.js`.
    - Port: Standard (meist 8000).
- **Schritt 4: Integration & Konfiguration**
    - Das Skript muss sicherstellen, dass SillyTavern korrekt konfiguri ist.
    - Bearbeitet automatisch die `config.yaml` (oder `settings.json` falls zutreffend) in SillyTavern.
    - Setzt den KoboldAI Endpoint auf `http://127.0.0.1:5001`.
    - Setzt den Silero TTS Endpoint auf `http://127.0.0.1:5002`.
- **Robustheit:** Alle Schritte müssen mit `pause` abgesichert sein, damit Fehlermeldungen sichtbar bleiben.

## Technische Details & Pfade
- **Basispfad:** `D:\SillyTavernAiO\`
- **Python:** `C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe`
- **Silero Modell:** `v5_5_ru.pt` (Russisch)
- **Ports:**
    - KoboldCPP: 5001
    - Silero TTS: 5002
    - SillyTavern: 8000 (Standard)

## Ziel
Der Benutzer soll nur `install.bat` einmalig ausführen müssen und danach täglich `start_all.bat`. Das System soll selbstständig Modelle verwalten, Server starten und die Konfigurationen so setzen, dass SillyTavern sofort mit KoboldCPP und Silero TTS kommunizieren kann.
