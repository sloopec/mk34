# Lokales Modell: Verschluesselte Parallels Ubuntu VM

## Uebersicht

Setup einer verschluesselten Ubuntu-VM in Parallels Desktop, die `supergemma4-26b-abliterated-multimodal-gguf-4bit` via llama.cpp bereitstellt. Die Kommunikation zwischen macOS-Host und VM erfolgt verschluesselt ueber TLS.

## Modell-Details

| Eigenschaft | Wert |
|-------------|------|
| Modell | supergemma4-26b-abliterated-multimodal-Q4_K_M.gguf |
| Vision-Projector | mmproj-supergemma4-26b-abliterated-multimodal-f16.gguf |
| Quelle | `huggingface.co/kof1467/supergemma4-26b-abliterated-multimodal-gguf-4bit` |
| Groesse (Disk) | ~17 GB (Text) + ~0.5 GB (mmproj) |
| RAM-Bedarf | ~20-24 GB (bei 8K-16K Kontext) |
| Architektur | Gemma4ForConditionalGeneration |
| Kontext | Bis 256K moeglich, empfohlen 8192-16384 Tokens fuer Speichereffizienz |

## Hardware-Voraussetzungen

- Mac mit mindestens 32 GB RAM (besser 64 GB)
- ~50 GB freier Speicherplatz fuer VM + Modell
- Parallels Desktop Pro oder Business Edition (fuer Verschluesselung und erhoehte RAM-Zuweisung)

---

## Schritt 1: Parallels Ubuntu VM erstellen

### 1.1 Ubuntu ISO herunterladen

1. Gehe zu `ubuntu.com/download/server`
2. Lade **Ubuntu Server 24.04 LTS** herunter (kein Desktop noetig, spart Ressourcen)

### 1.2 VM in Parallels anlegen

1. Oeffne Parallels Desktop
2. **Datei > Neu > Installieren von Image**
3. Waehle die Ubuntu Server ISO
4. Name: `mk34-local-model`
5. Speicherort: Standard oder eigenen waehlen

### 1.3 VM-Ressourcen konfigurieren (vor dem Start)

1. Rechtsklick auf VM > **Konfigurieren**
2. Tab **Hardware**:
   - **CPU & Speicher**:
     - Prozessoren: Mindestens 8 Kerne
     - Arbeitsspeicher: **28 GB** (Modell braucht ~20-24 GB + OS-Overhead)
   - **Festplatte**: Mindestens **60 GB** (Modell ~18 GB + Build-Tools + Puffer)
   - **Netzwerk**: Shared Network (Standard) - behalten
3. Tab **Sicherheit**:
   - Aktiviere nichts noch — Verschluesselung kommt nach der Installation

### 1.4 Ubuntu Server installieren

1. VM starten, Ubuntu-Installer folgen
2. Hostname: `mk34-llm`
3. Benutzername/Passwort waehlen (z.B. `mk34` / sicheres Passwort)
4. **OpenSSH Server installieren**: Ja (im Installer ankreuzen)
5. Installation abschliessen, VM neustarten

---

## Schritt 2: VM verschluesseln

### 2.1 Parallels VM-Verschluesselung aktivieren

**Wichtig:** Dies verschluesselt die gesamte VM-Disk-Datei auf dem Host.

1. VM herunterfahren (`sudo shutdown -h now` in der VM)
2. In Parallels: Rechtsklick auf VM > **Konfigurieren**
3. Tab **Sicherheit**
4. **Verschluesselung aktivieren** anklicken
5. **Passwort setzen** (starkes Passwort, separat notieren!)
   - Dieses Passwort wird bei jedem VM-Start abgefragt
6. Warten bis Verschluesselung abgeschlossen ist (kann bei 60 GB einige Minuten dauern)

### 2.2 Zusaetzlich: LUKS innerhalb der VM (Optional, doppelte Sicherheit)

Falls du auch innerhalb der VM verschluesseln moechtest (defense in depth):

Bei der Ubuntu-Installation haettest du "Encrypt the LVM group" waehlen koennen. Nachtraeglich ist dies aufwaendiger. Die Parallels-Verschluesselung allein ist fuer diesen Use-Case ausreichend.

---

## Schritt 3: SSH mit TLS/Verschluesselung einrichten

Die Kommunikation zwischen Host (macOS) und VM soll verschluesselt sein. SSH ist bereits verschluesselt (AES-256). Wir richten key-based Auth ein und haerten die Verbindung.

### 3.1 IP-Adresse der VM ermitteln

In der VM:
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```
Notiere die IP (typisch: `10.211.55.x`)

### 3.2 SSH-Key auf dem Mac erstellen (falls nicht vorhanden)

```bash
# Auf dem Mac:
ssh-keygen -t ed25519 -C "mk34-vm" -f ~/.ssh/mk34_vm_ed25519
```
Kein Passwort noetig (oder mit Passphrase fuer extra Sicherheit).

### 3.3 SSH-Key auf die VM uebertragen

```bash
# Auf dem Mac:
ssh-copy-id -i ~/.ssh/mk34_vm_ed25519.pub mk34@10.211.55.X
```
(IP anpassen)

### 3.4 SSH-Config auf dem Mac anlegen

Datei `~/.ssh/config` ergaenzen:
```
Host mk34-vm
    HostName 10.211.55.X
    User mk34
    IdentityFile ~/.ssh/mk34_vm_ed25519
    StrictHostKeyChecking yes
    Port 22
```

Test:
```bash
ssh mk34-vm
```

### 3.5 SSH auf der VM haerten

In der VM (`/etc/ssh/sshd_config`):
```bash
sudo nano /etc/ssh/sshd_config
```

Aendern/ergaenzen:
```
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
MaxAuthTries 3
AllowUsers mk34
```

Dann:
```bash
sudo systemctl restart sshd
```

---

## Schritt 4: llama.cpp in der VM installieren

### 4.1 Build-Abhaengigkeiten installieren

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential cmake git curl wget
```

### 4.2 llama.cpp klonen und bauen

```bash
cd ~
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
```

**Hinweis:** Auf einer ARM-VM (Apple Silicon via Parallels) wird CPU-Inferenz genutzt. GPU-Passthrough ist in Parallels nicht verfuegbar. Die Geschwindigkeit ist trotzdem akzeptabel fuer Text-Generierung (~5-15 tok/s bei Q4_K_M auf 8 Kernen).

### 4.3 Binaries verifizieren

```bash
./build/bin/llama-cli --version
./build/bin/llama-server --version
```

---

## Schritt 5: Modell herunterladen

### 5.1 huggingface-hub CLI installieren

```bash
sudo apt install -y python3-pip
pip3 install huggingface-hub
```

### 5.2 Modell-Dateien laden

```bash
mkdir -p ~/models
cd ~/models

# Text-Modell (Q4_K_M, ~17 GB)
huggingface-cli download kof1467/supergemma4-26b-abliterated-multimodal-gguf-4bit \
  supergemma4-26b-abliterated-multimodal-Q4_K_M.gguf \
  --local-dir .

# Vision-Projector (fuer multimodale Nutzung)
huggingface-cli download kof1467/supergemma4-26b-abliterated-multimodal-gguf-4bit \
  mmproj-supergemma4-26b-abliterated-multimodal-f16.gguf \
  --local-dir .
```

### 5.3 Download verifizieren

```bash
ls -lh ~/models/
# Erwarte: ~17 GB fuer das Hauptmodell, ~0.5 GB fuer mmproj
```

---

## Schritt 6: llama-server als Dienst einrichten

### 6.1 Systemd Service erstellen

```bash
sudo nano /etc/systemd/system/llama-server.service
```

Inhalt:
```ini
[Unit]
Description=llama.cpp Server fuer mk34
After=network.target

[Service]
Type=simple
User=mk34
WorkingDirectory=/home/mk34/llama.cpp
ExecStart=/home/mk34/llama.cpp/build/bin/llama-server \
  --model /home/mk34/models/supergemma4-26b-abliterated-multimodal-Q4_K_M.gguf \
  --mmproj /home/mk34/models/mmproj-supergemma4-26b-abliterated-multimodal-f16.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 16384 \
  --threads 8 \
  --n-predict 4096 \
  --parallel 1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 6.2 Service aktivieren und starten

```bash
sudo systemctl daemon-reload
sudo systemctl enable llama-server
sudo systemctl start llama-server
```

### 6.3 Status pruefen

```bash
sudo systemctl status llama-server
# Und nach ~30s (Modell-Ladezeit):
curl http://localhost:8080/health
```

---

## Schritt 7: TLS fuer den llama-server (verschluesselte API-Kommunikation)

SSH ist bereits verschluesselt, aber wenn mk34 direkt die HTTP-API der VM anspricht (ohne SSH-Tunnel), brauchen wir TLS.

### Option A: SSH-Tunnel (einfachste Loesung, empfohlen)

Auf dem Mac:
```bash
ssh -N -L 8080:localhost:8080 mk34-vm
```

Dann ist der Server auf dem Mac unter `http://localhost:8080` erreichbar — die gesamte Kommunikation laeuft verschluesselt durch den SSH-Tunnel.

Fuer dauerhaften Tunnel (als Hintergrundprozess):
```bash
ssh -f -N -L 8080:localhost:8080 mk34-vm
```

In `~/.ssh/config` ergaenzen fuer Komfort:
```
Host mk34-vm-tunnel
    HostName 10.211.55.X
    User mk34
    IdentityFile ~/.ssh/mk34_vm_ed25519
    LocalForward 8080 localhost:8080
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Dann nur noch: `ssh -f -N mk34-vm-tunnel`

### Option B: Selbstsigniertes TLS-Zertifikat (Alternative)

Falls du ohne SSH-Tunnel arbeiten willst:

```bash
# In der VM:
mkdir -p ~/certs
cd ~/certs

# Selbstsigniertes Zertifikat erstellen (1 Jahr gueltig)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=mk34-llm/O=mk34/C=DE" \
  -addext "subjectAltName=IP:10.211.55.X"
```

Dann `llama-server` mit TLS starten (ExecStart in der Service-Datei anpassen):
```
ExecStart=/home/mk34/llama.cpp/build/bin/llama-server \
  --model /home/mk34/models/supergemma4-26b-abliterated-multimodal-Q4_K_M.gguf \
  --mmproj /home/mk34/models/mmproj-supergemma4-26b-abliterated-multimodal-f16.gguf \
  --host 0.0.0.0 \
  --port 8443 \
  --ctx-size 16384 \
  --threads 8 \
  --n-predict 4096 \
  --parallel 1 \
  --ssl-cert-file /home/mk34/certs/cert.pem \
  --ssl-key-file /home/mk34/certs/key.pem
```

Zertifikat auf den Mac kopieren:
```bash
# Auf dem Mac:
scp mk34-vm:~/certs/cert.pem ~/.ssh/mk34_vm_cert.pem
```

---

## Schritt 8: Firewall in der VM konfigurieren

```bash
# In der VM:
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.211.55.0/24 to any port 22    # SSH nur vom Host-Netz
sudo ufw allow from 10.211.55.0/24 to any port 8080  # llama-server nur vom Host-Netz
sudo ufw enable
sudo ufw status
```

---

## Schritt 9: Integration in mk34 testen

### 9.1 Vom Mac aus testen (mit SSH-Tunnel aktiv)

```bash
# Tunnel starten
ssh -f -N mk34-vm-tunnel

# Health-Check
curl http://localhost:8080/health

# Testanfrage (OpenAI-kompatibles API-Format)
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "supergemma4",
    "messages": [
      {"role": "user", "content": "Schreibe einen kurzen Absatz ueber eine dunkle Gasse bei Nacht."}
    ],
    "max_tokens": 200,
    "temperature": 0.8
  }'
```

### 9.2 mk34 Model-Router Konfiguration

In `src/models/config.py` wird spaeter eingetragen:
```python
LOCAL_MODEL_ENDPOINT = "http://localhost:8080/v1"
LOCAL_MODEL_NAME = "supergemma4-26b-abliterated"
```

LiteLLM-Konfiguration:
```python
# litellm kann den lokalen Server als OpenAI-kompatiblen Endpoint ansprechen
model_config = {
    "model": "openai/supergemma4",
    "api_base": "http://localhost:8080/v1",
    "api_key": "not-needed"  # llama-server braucht keinen Key
}
```

---

## Schritt 10: Automatisierung (Convenience-Scripts)

### 10.1 VM starten + Tunnel oeffnen (ein Befehl)

Datei `~/Projects/mk34/scripts/start_local_model.sh`:
```bash
#!/bin/bash
set -e

echo "Starte mk34-local-model VM..."
prlctl start mk34-local-model 2>/dev/null || true

echo "Warte auf SSH-Bereitschaft..."
until ssh -o ConnectTimeout=2 mk34-vm "echo ready" 2>/dev/null; do
    sleep 2
done

echo "Oeffne SSH-Tunnel..."
ssh -f -N mk34-vm-tunnel

echo "Warte auf llama-server..."
until curl -s http://localhost:8080/health | grep -q "ok"; do
    sleep 3
done

echo "Lokales Modell bereit: http://localhost:8080"
```

### 10.2 Alles stoppen

Datei `~/Projects/mk34/scripts/stop_local_model.sh`:
```bash
#!/bin/bash
echo "Stoppe SSH-Tunnel..."
pkill -f "ssh.*mk34-vm-tunnel" 2>/dev/null || true

echo "Fahre VM herunter..."
prlctl stop mk34-local-model --graceful

echo "Lokales Modell gestoppt."
```

---

## Zusammenfassung: Manuelle Schritte Checkliste

1. [ ] Ubuntu Server 24.04 ISO herunterladen
2. [ ] Parallels VM erstellen (8 Kerne, 28 GB RAM, 60 GB Disk)
3. [ ] Ubuntu Server installieren (mit OpenSSH)
4. [ ] VM herunterfahren und Parallels-Verschluesselung aktivieren
5. [ ] SSH-Key erstellen und auf VM uebertragen
6. [ ] SSH haerten (Password-Auth deaktivieren)
7. [ ] llama.cpp in der VM bauen
8. [ ] Modell von HuggingFace herunterladen (~17.5 GB)
9. [ ] llama-server als systemd-Service einrichten
10. [ ] SSH-Tunnel oder TLS-Zertifikat konfigurieren
11. [ ] Firewall (ufw) aktivieren
12. [ ] Vom Mac aus testen (curl)
13. [ ] Convenience-Scripts anlegen

## Sicherheitsarchitektur

```
┌─────────────────────────────────────────────────────────────┐
│  macOS Host                                                   │
│                                                               │
│  mk34 CLI ──► localhost:8080 ──► SSH-Tunnel (AES-256-GCM)   │
│                                       │                       │
└───────────────────────────────────────┼───────────────────────┘
                                        │ verschluesselt
┌───────────────────────────────────────┼───────────────────────┐
│  Parallels VM (AES-256 verschluesselt)│                       │
│                                       ▼                       │
│  UFW Firewall ──► llama-server:8080 (nur lokales Netz)       │
│                       │                                       │
│                       ▼                                       │
│  supergemma4-26b-Q4_K_M.gguf                                 │
│  (nur auf verschluesselter VM-Disk)                           │
└───────────────────────────────────────────────────────────────┘
```

Drei Verschluesselungsschichten:
1. **Parallels VM-Disk**: AES-256 (Modell-Dateien at-rest geschuetzt)
2. **SSH-Tunnel**: AES-256-GCM (Kommunikation in-transit geschuetzt)
3. **UFW Firewall**: Nur Host-Subnetz darf auf Port 8080 zugreifen

## Erwartete Performance

| Metrik | Geschaetzter Wert |
|--------|-------------------|
| Modell-Ladezeit | 20-40 Sekunden |
| Prompt-Verarbeitung | 30-80 tok/s (CPU, ARM) |
| Text-Generierung | 5-15 tok/s (CPU, ARM) |
| Typische Szene (1000 Woerter) | 2-5 Minuten |

Die Geschwindigkeit ist fuer den Szenen-Schreib-Workflow ausreichend, da die Ergebnisse ohnehin vom Editor-Agent (Opus) nachbearbeitet werden.
