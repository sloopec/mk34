# Gemini: Kosten, Kontingente und was deine bestehenden Abos wirklich bringen

Stand: 2026-08-21. Google baut Preise, Kontingente und Tarifnamen aktuell laufend um (Rebranding "Google One AI Premium" → "Google AI Pro"/"Google AI Ultra", neue Prepay/Postpay-Abrechnung seit März 2026). Vor einer finanziellen Entscheidung die Original-Links unten gegenchecken.

## TL;DR

**Weder dein Google-Workspace-Business-Standard-Abo noch dein privates Google-One/Google-AI-Pro-Abo geben dir automatisch mehr Kontingent für den `GEMINI_API_KEY`, den mk34 benutzt.** Das sind drei getrennte Produkte mit getrennter Abrechnung:

| Produkt | Wofür | Hilft das gegen den 20-Requests/Tag-Block in mk34? |
|---|---|---|
| Workspace Business Standard | Gemini-Assistent in Gmail/Docs/Sheets/Slides/Meet/Drive | **Nein** |
| Google One / Google AI Pro | Gemini-App (Chat), höhere Limits in der AI-Studio-**Oberfläche** | **Nein** — mit einer Ausnahme (siehe unten) |
| Gemini Developer API (`GEMINI_API_KEY`, das, was `mk34-book-agent` nutzt) | Pay-per-Token, eigenes Cloud-Billing-Konto | **Das ist der einzige Hebel** |

Die eine Ausnahme: Google AI Pro bringt dir **$10 Google-Cloud-Guthaben pro Monat**, das du — nach Aktivierung und mit eingerichtetem Cloud Billing — tatsächlich gegen Gemini-API-Nutzung verrechnen kannst (Abschnitt 4).

---

## 1. Ausgangslage: was bei mk34 passiert ist

Der `GEMINI_API_KEY` in `mk34-book-agent/.env` läuft aktuell im **Free Tier** der Gemini API. Der Free Tier hat pro Modell ein Tageslimit — für `gemini-3.7-flash` waren das die beobachteten **20 Requests/Tag** (Fehlermeldung: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`). Sobald das ausgeschöpft ist, blockt die API mit HTTP 429, unabhängig davon, wie viel du sonst bei Google zahlst.

Um darüber hinauszukommen, muss auf dem **Google-Cloud-Projekt, das zu diesem API-Key gehört**, Cloud Billing aktiviert werden (→ Abschnitt 5, „Tier 1"). Das ist unabhängig von Workspace oder Google One.

---

## 2. Warum Workspace/Google One nicht automatisch helfen

Google trennt strikt zwischen:
- **Konsum-Oberflächen** (Gemini in Workspace-Apps, die Gemini-Chat-App, AI Studio als Web-UI) — bezahlt über dein Abo, Kontingent gilt nur innerhalb dieser Oberfläche.
- **Der Gemini Developer API** (das, was du per Code/API-Key ansprichst, z. B. über den ADK-Router in `mk34-book-agent/app/models/router.py`) — komplett separat abgerechnet über ein Google-Cloud-Billing-Konto, pay-per-Token.

Google selbst formuliert es so: *„Google AI plan benefits for developer usage apply only within the Google AI Studio web interface"* — API-Zugriff mit eigenem Key wird „billed and managed separately".

---

## 3. Google Workspace Business Standard

**Was enthalten ist:**
- Gemini-Assistent direkt in Gmail, Docs, Sheets, Slides, Meet und Drive, ohne separates Zubuchen (der frühere Zusatz-Tarif „Gemini Business/Enterprise" für ~$20–30/Nutzer/Monat wurde 2025 abgeschafft und in die Grundpreise eingepreist)
- NotebookLM
- Aktueller Richtpreis: ca. **$14/Nutzer/Monat** bei Jahresbindung (ca. $16.80 bei monatlicher Zahlung) — exakter, aktueller Preis für dein Land/deine Domain: [workspace.google.com/pricing](https://workspace.google.com/pricing.html)

**Limits:** Google veröffentlicht für Business Standard keine festen, öffentlichen Tageskontingente (kein „X Prompts/Tag" in der Doku) — es gibt aber ein „Fair Use"-Verhalten: rechenintensive Funktionen (z. B. Video-/Audio-Generierung) werden bei starker Nutzung gedrosselt. Wer mehr braucht, kann das Add-on **„AI Expanded Access"** dazubuchen (ca. $20/Nutzer/Monat, Jahresbindung, seit März 2026 verfügbar) — das hebt aber nur Limits **innerhalb der Workspace-Apps**, nicht die Developer-API.

**Für mk34 relevant:** **Nichts davon.** Kein Vertex-AI-Guthaben, kein Gemini-API-Kontingent, keine Cloud-Credits sind in Business Standard enthalten. Dieses Abo betrifft ausschließlich die Büro-Anwendungen, nicht euren Coding-Agenten.

---

## 4. Google One / Google AI Pro (dein privates Abo)

Namens-Hinweis: Das frühere „Google One AI Premium" heißt inzwischen **„Google AI Pro"** (Google One selbst bleibt der Speicherplatz-/Familientarif-Rahmen, die KI-Funktionen sind als eigene Stufen „AI Pro"/„AI Ultra" ausgegliedert).

**Google AI Pro (Richtpreis $19.99/Monat, lokale Preise können abweichen — [one.google.com](https://one.google.com) prüfen):**
- Höhere Limits im Gemini-Chat/der Gemini-App
- Zugriff auf Nano Banana (Bildgenerierung), Veo, höhere NotebookLM-Limits, 2 TB Speicher
- Höhere Limits **in der AI-Studio-Web-Oberfläche** (nicht der API)
- **Gemini Code Assist**: höhere Kontingente für KI-Coding-Unterstützung in der IDE (separates Produkt, nicht der Gemini-API-Key selbst)
- **$10 Google-Cloud-Guthaben pro Monat** über eine „Google Developer Program Premium"-Mitgliedschaft, die in Google AI Pro automatisch enthalten ist

**Google AI Ultra (Richtpreis $249.99/Monat):** analog, aber $100 Cloud-Guthaben/Monat statt $10. Bei diesem Preis lohnt sich Ultra nicht *nur* wegen des API-Guthabens — die Differenz zu Pro ($230/Monat mehr) übersteigt bei weitem, was ein Projekt wie mk34 realistisch an API-Kosten verbraucht.

**Der praktisch relevante Teil — das $10-Cloud-Guthaben:**
1. Muss im Google-Developer-Program-Portal ([developers.google.com/program](https://developers.google.com/program)) aktiviert werden — es wird nicht automatisch verrechnet.
2. Gilt laut Google offiziell für „Vertex AI, Cloud Run, und Gemini API (über AI Studio oder Vertex AI)" — deckt also genau die Art Nutzung ab, die `mk34-book-agent` erzeugt.
3. Voraussetzung: Ein aktives Cloud-Billing-/Prepay-Konto auf dem Projekt muss eingerichtet sein (das ist derselbe Schritt, der auch für Tier 1 nötig ist, siehe unten). Ist das eingerichtet, wird das Guthaben **zuerst** verbraucht, bevor eigenes Prepay-Geld angerechnet wird.
4. Läuft monatlich neu auf — bei geringer Entwicklungsnutzung (wie aktuell bei mk34: Unit-Tests ohne Live-Calls, gelegentliche Eval-Läufe) dürfte es einen Großteil oder die gesamten API-Kosten des Projekts abdecken.

---

## 5. Reines API-Billing: die Tier-Struktur (unabhängig von jedem Abo)

Das ist der Weg, der den 20/Tag-Block tatsächlich auflöst — mit oder ohne Google AI Pro/Ultra:

| Tier | Voraussetzung | Monatliches Ausgaben-Limit | Zusätzliches Rolling-Window-Spend-Limit |
|---|---|---|---|
| Free | aktives Projekt, kein Billing nötig | — | — |
| **Tier 1** | Cloud-Billing-Konto verknüpft | $250 | $10 / 10-Minuten-Fenster |
| Tier 2 | $100+ ausgegeben, 3 Tage seit erster erfolgreicher Zahlung | $2.000 | $50 / 10-Minuten-Fenster |
| Tier 3 | $1.000+ ausgegeben, 30 Tage seit erster Zahlung | $20.000–$100.000+ | $200 / 10-Minuten-Fenster |

Tier-1-Freischaltung ist praktisch sofort (typisch <10 Minuten) nach Verknüpfen eines Billing-Kontos.

**Wichtiger Vorbehalt:** Die genauen Requests-pro-Minute/Tag-Zahlen (RPM/TPM/RPD) für die konkret in mk34 verwendeten Modelle (`gemini-3.1-pro-preview`, `gemini-3.7-flash`, `gemini-3.5-flash-lite`) veröffentlicht Google nicht mehr als statische Tabelle in der Doku — die Seite verweist auf das personalisierte, projektgebundene Dashboard: **[aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit)**. Als grobe Größenordnung aus der *vorherigen* Modellgeneration (Gemini 2.5, Stand Januar 2026, nicht direkt auf 3.x übertragbar): Free Tier bewegt sich bei Flash-Modellen im Bereich von ca. 10–15 RPM / 250–1.000 RPD, Tier 1 im Bereich von ca. 150–300 RPM / 1.000–1.500 RPD. Für die tatsächlichen aktuellen Werte eures Projekts bitte das Dashboard direkt prüfen — die Zahlen ändern sich pro Generation.

Neu seit März 2026: **Prepay** (Guthaben vorab kaufen, min. $10, max. $5.000, verfällt nach 12 Monaten) vs. **Postpay** (klassische monatliche Cloud-Rechnung). Neue Konten starten standardmäßig mit Prepay.

### Klarstellung: „$250 Ausgaben-Limit" ist eine Obergrenze, keine Pflicht

Das war oben missverständlich formuliert. Die Zahlen in der Tabelle sind **Deckel (Caps)**, keine Mindestausgaben:

- Um **Tier 1** freizuschalten, musst du **nichts ausgeben** — es reicht, ein Cloud-Billing-Konto mit dem Projekt zu verknüpfen (Zahlungsmittel hinterlegen). Das Limit von $250/Monat ist danach einfach die Obergrenze, bis zu der Google dich in diesem Tier abrechnet, bevor du in Tier 2 rutschst.
- Tier 2/3 schaltet sich frei, **nachdem** du kumulativ tatsächlich $100 bzw. $1.000 ausgegeben hast (plus Wartezeit) — das ist also eine Folge realer Nutzung, kein Ziel, das du aktiv ansteuern musst.
- Das **$10-Cloud-Guthaben** aus Google AI Pro hat mit dieser Tabelle nichts zu tun. Es ist unabhängig davon, welches Ausgaben-Tier dein Projekt gerade hat — du bekommst es einfach jeden Monat gutgeschrieben, sobald der Developer-Program-Vorteil aktiviert ist und ein Billing-Konto existiert.

**„Wie muss ich das Guthaben ausgeben?"** — gar nicht aktiv. Es ist ein Kontostand auf deinem Cloud-Billing-Konto, der bei jeder abrechenbaren Nutzung (Gemini-API-Calls über AI Studio/Vertex AI, Vertex AI, Cloud Run) automatisch **zuerst** verrechnet wird, bevor eigenes Prepay-Guthaben oder deine Kreditkarte belastet werden. Du musst also nur: (a) Billing einrichten, (b) den Developer-Program-Vorteil einmalig aktivieren — den Rest bucht Google automatisch gegen deine mk34-API-Aufrufe.

---

## 6. Schritt-für-Schritt: Tier 1 einrichten (Billing aktivieren)

1. **[aistudio.google.com](https://aistudio.google.com)** öffnen, einloggen.
2. Im linken Menü **Dashboard → Projects** öffnen.
3. Zwei Wege, je nachdem was du willst:
   - **Neues Projekt von AI Studio anlegen lassen** — passiert automatisch, wenn du noch keins hast/den Standard-Weg nimmst.
   - **Bestehendes GCP-Projekt verwenden** (deine Erinnerung stimmt, die Option gibt es weiterhin): Button **„Import projects"** klicken → das gewünschte Google-Cloud-Projekt aus der Liste suchen/auswählen → **„Import"**. Sinnvoll, falls du z. B. schon ein GCP-Projekt hast, in dem der Developer-Program-Vorteil oder anderes Guthaben liegt.
4. Auf der **API-Keys-Seite** (oder in der Projects-Tabelle) findest du dein Projekt mit der Spalte **„Billing Tier"** — Free Tier steht dort standardmäßig.
5. In der Zeile deines Projekts auf **„Set up billing"** klicken.
6. Ein **Cloud-Billing-Konto** auswählen (falls schon vorhanden) oder neu anlegen: Zahlungsmittel + Kontaktdaten hinterlegen.
7. Abrechnungsmodell wählen: **Prepay** (Mindestbetrag i. d. R. $10 vorab) oder **Postpay** (klassische monatliche Rechnung) — je nachdem, was dir angeboten wird.
8. Setup abschließen — Umstellung auf **Tier 1** ist danach normalerweise **sofort bis wenige Minuten** wirksam.
9. Falls Google AI Pro aktiv ist: zusätzlich einmalig unter **[developers.google.com/program](https://developers.google.com/program)** den Premium-Vorteil aktivieren, damit das $10-Cloud-Guthaben ab dem nächsten Monat automatisch auf **dasselbe** Billing-Konto/Projekt gebucht wird, das du gerade eingerichtet hast.
10. **Prüfen:** Zurück in AI Studio sollte die Projekt-Zeile jetzt „Tier 1" statt „Free" zeigen. Unter **[aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit)** siehst du die aktualisierten (höheren) Limits für genau dieses Projekt.
11. Für mk34 konkret: Der `GEMINI_API_KEY` in `mk34-book-agent/.env` muss zu **diesem** Projekt gehören — falls der Key aus einem anderen (noch Free-Tier-)Projekt stammt, entweder dort ebenfalls Billing einrichten oder einen neuen Key im jetzt hochgestuften Projekt erzeugen und in `.env` eintragen.

Falls beim Erstellen eines Keys im importierten Projekt die Meldung „You do not have permission to create a key in this project" erscheint: dir fehlt die IAM-Berechtigung (z. B. Editor-Rolle) auf diesem GCP-Projekt — ein Admin des Projekts/der Organisation muss sie dir zuteilen.

---

## 7. Token-Preise der in mk34 konfigurierten Modelle

Aus dem Model-Router (`app/models/router.py`, Entscheidung E6/E7):

| Modell (Rolle in mk34) | Input (Standard) | Output (Standard) | Context Caching | Batch (−50 %) |
|---|---|---|---|---|
| `gemini-3.1-pro-preview` (heavy: Plot/Character/Editor/Style, Scene-Start) | $2,00 / 1M (≤200k Kontext) · $4,00 / 1M (>200k) | $12,00 / 1M (≤200k) · $18,00 / 1M (>200k) | $0,20–$0,40 / 1M + $4,50 / 1M/Std. Speicher | $1,00–$2,00 / 1M Input, $6,00–$9,00 / 1M Output |
| `gemini-3.7-flash` (fast: Orchestrator/Continuity/Research) | $0,75 / 1M (bis 31.12.2026, danach $1,50) | $3,75 / 1M (bis 31.12.2026, danach $7,50) | $0,075 / 1M genutzt + $0,50 / 1M/Std. Speicher | 50 % Rabatt auf Standard |
| `gemini-3.5-flash-lite` (Classifier) | $0,30 / 1M | $2,50 / 1M | — | $0,15 / 1M Input, $1,25 / 1M Output |

Zum Vergleich: Ein einzelner Eval-Lauf mit ein paar Dutzend kurzen Prompts kostet im Cent-Bereich — das monatliche $10-Cloud-Guthaben aus Google AI Pro (Abschnitt 4) dürfte die aktuelle Entwicklungsphase von mk34 komplett abdecken.

---

## 8. Praktische Einordnung für mk34

1. Weder Workspace Business Standard noch der Kern von Google AI Pro lösen den 20/Tag-Free-Tier-Block.
2. Der einzige Weg: **Cloud Billing auf dem Projekt hinter `GEMINI_API_KEY` aktivieren** (→ Tier 1, Abschnitt 5). Das ist unabhängig von allen Abos.
3. Falls das Google-AI-Pro-Abo aktiv ist: **vor** oder **direkt bei** diesem Billing-Setup den Google-Developer-Program-Premium-Vorteil aktivieren ([developers.google.com/program](https://developers.google.com/program)) — dann wird das monatliche $10-Cloud-Guthaben automatisch zuerst gegen die mk34-API-Kosten verrechnet, bevor eigenes Geld verbraucht wird.
4. Bei der aktuellen, sehr geringen Nutzung (Unit-Tests ohne Live-Calls, gelegentliche `agents-cli eval run`-Läufe) ist mit realen Kosten im niedrigen einstelligen Dollarbereich pro Monat zu rechnen — das $10-Guthaben dürfte reichen, bis das Projekt in Plan 3/4 (Szenen-Generierung, größere Eval-Suiten) spürbar mehr Volumen erzeugt.

---

## Quellen (abgerufen 2026-08-21)

- [ai.google.dev/gemini-api/docs/google-ai-plans](https://ai.google.dev/gemini-api/docs/google-ai-plans) — Trennung Abo-Oberfläche vs. API
- [ai.google.dev/gemini-api/docs/billing](https://ai.google.dev/gemini-api/docs/billing) — Tier-Voraussetzungen, Prepay/Postpay
- [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) — Token-Preise
- [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) — Tier-Struktur, Verweis auf personalisiertes Dashboard
- [aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit) — aktuelle, projektgebundene Live-Limits (Login nötig)
- [support.google.com/googleone/answer/14534406](https://support.google.com/googleone/answer/14534406?hl=en) — Google-AI-Pro-Leistungen, inkl. $10-Cloud-Guthaben
- [blog.google/innovation-and-ai/technology/developers-tools/gdp-premium-ai-pro-ultra](https://blog.google/innovation-and-ai/technology/developers-tools/gdp-premium-ai-pro-ultra/) — Developer-Program-Premium-Bündelung, $10 (Pro) / $100 (Ultra) Cloud-Guthaben, Verwendungszweck
- [workspace.google.com/pricing](https://workspace.google.com/pricing.html) — aktuelle Workspace-Preise für dein Land
- Third-Party-Zusammenfassungen (für Größenordnungs-Referenz der 2.5-Generation, nicht autoritativ): aifreeapi.com, standardcompute.com
