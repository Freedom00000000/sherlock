# Sherlock OSINT Dashboard

En webbaseret OSINT-app med mørkt tema, der kombinerer:

- **Sherlock** — søg efter brugernavn på 476+ sociale medier
- **Cheater Detector** — tjek dating- og NSFW-sider specifikt
- **Deep OSINT** — GitHub profil, Gravatar, e-mail breach (HIBP), DNS og WHOIS

## Kom i gang

### Windows
Dobbeltklik på `run.bat`  
eller fra terminal:
```
cd osint_app
pip install flask sherlock-project
python app.py
```

### Linux / macOS / Kali
```bash
cd osint_app
chmod +x run.sh && ./run.sh
```

Åbner automatisk `http://localhost:5000` i browseren.

## Funktioner

| Funktion | Beskrivelse |
|---|---|
| Username Search (All) | Søger alle 476+ Sherlock-sites |
| Cheater Detector | Søger 29 dating/NSFW/sociale sider |
| Egne sites | Vælg præcis hvilke sites der søges |
| NSFW-filter | Til/fra for voksensider |
| Live output | Se resultater strømmende ind |
| Resultattabel | Sorteret liste med links |
| Export CSV/TXT | Download fund som fil |
| Deep OSINT | GitHub, Gravatar, HIBP, DNS, WHOIS |

## Krav

- Python 3.10+
- `pip install flask sherlock-project`
