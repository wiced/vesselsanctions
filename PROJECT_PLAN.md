# Projektiplaan – Insure Consult: laevade sanktsioonikontroll

**Versioon:** 1.0 (22.10.2026)  
**Tellija:** Insure Consult  
**Lahenduse kavandatav eluiga:** ligikaudu 1–3 aastat, võimalik hilisem asendamine partneri süsteemiga  
**Tehnoloogiad:** GitHub Actions, GitHub Pages, Python, Excel Power Query, SharePoint, Power Automate, olemasolev Nicepage  
**Põhimõte:** väike ülalpidamiskulu, olemasolevate tööprotsesside säilitamine, kliendi võime allikate kaardistusi kohendada.

## 1. Eesmärk ja lähteseis

Praeguses Excelis on ~1800 laevaga Insure Consulti tööregister, mida kasutatakse laeva vanuse määramiseks ja kindlustuspreemia arvutamisel. Sanktsioonikontroll toimub IMO numbri järgi: EU/DMA, OFAC SDN, UK. Nicepage'i praegune skript sisaldab koodi sisse kirjutatud eraldi IMO nimekirja ning ei uuene koos Exceliga. Üksiku laeva lisamine kliendi tööregistrisse peab jääma lihtsaks; aastas lisandub ~40–50 laeva.

Eesmärk on üks kontrollitud avalik sanktsioonide andmestik, mida saavad kasutada nii Excel kui ka Nicepage, ilma et Insure Consulti privaatne laevaregister või deklaratsioonid peaksid avalikku GitHubi liikuma. Tulevikus lisandub privaatsete kontrollitõendite PDF SharePointi.

## 2. Süsteemi piirid ja arhitektuur

```text
DMA EU vessel designations ─┐
OFAC SDN public CSV ────────┼──▶ GitHub Actions / Python (1× ööpäevas, käsitsi käivitatav)
UK Sanctions List CSV ─────┘                   │
                                               ▼
                                 Normaliseerimine IMO numbri järgi
                                 + kõikide allikate valideerimine
                                               │
                                        ainult edukal juhul
                                               ▼
                          GitHub Pages: vessels.csv, vessels.json, status.json
                                    │                       │
                                    ▼                       ▼
                           Excel Power Query          Nicepage (sisselogitud)
                                    │
                                    ▼
                         Igakuised veoste deklaratsioonid
                                    │
                                    ▼
                       Power Automate → SharePoint PDF
```

- **Avalikud andmed:** ametlikest sanktsiooninimekirjadest võetud IMO-d, laevade nimed, allika viited, võimalikud sanktsiooniprogrammid ja nimekirjakuupäevad.
- **Privaatsed andmed:** Insure Consulti enda laevaregister, lisapreemia loogika, klientide veoste nimekirjad, kontrollide PDF-id ning kasutajakontod jäävad Microsoft 365 keskkonda.
- **Ametlikud allikad:** EU osa võetakse DMA lehe Russia/Belarus määruse 833/2014 Annex XLII tabelist (senise Exceli analoog). DMA lehel olev DPRK nimekiri ei ole MVP-s vaikimisi kaasa haaratud. OFAC ainult SDN, UK UK Sanctions List.
- **Väärtuse tähendus:** `VASTE LEITUD` või `VASTET EI LEITUD KONTROLLITUD NIMEKIRJADEST`; mitte tehingu seaduslikkuse otsus.

## 3. Etapid, tööd, vastuvõtutingimused

| # | Etapp ja töö | Valmiskriteerium | Hinnanguline maht* |
|---|---|---|---:|
| 1 | GitHub repo, Actions, Pages, esmane kood ja konfiguratsioon | `main` sisaldab täielikku lähtekoodi; Actionsi testid rohelised; Pages avaldab ainult pärast 3 allika korrektset importi | 5–9 h |
| 2 | EU, OFAC, UK parserite tegelike sisendite kontroll, negatiivsete juhtude testid | Iga allika IMO-d võrreldud käsitsi ametliku nimekirjaga; veerujärjestuse muutuse test; tühjade importide blokeerimine | 7–14 h |
| 3 | Exceli sanktsioonikontroll ja laevaregistri ühendused | Power Query loeb Pages CSV-d; laevaregistri säilimine; ükski valem ei eelda teise töövihiku avatuna hoidmist | 6–12 h |
| 4 | Nicepage'i skripti ümbertegemine | Veeb kasutab sama JSON-i; näitab EU/OFAC/UK tulemusi ja andmevärskust; vea korral ei ütle ekslikult „ei ole sanktsioneeritud” | 4–8 h |
| 5 | Igakuiste deklaratsioonide masskontroll ja PDF-i salvestus SharePointi | Dokumendil IMO, laev, kontrolliaeg, kontrollitud nimekirjade kuupäevad, tulemus; piiratud ligipääs | 8–16 h |
| 6 | Üleandmine, veateavitused, haldusjuhend, vastuvõtutest | Kliendi töötaja oskab URL-i/veeru vastendust muuta; veateavitused jõuavad määratud isikuni | 3–6 h |
| | **Kokku** | | **33–65 h** |

\* Arhitektuuriline esialgne töömahu hinnang, mitte siduv pakkumine. Täpsustub pärast igakuise deklaratsiooni Exceli ning Nicepage'i majutuse/autentimise kontrolli. Esialgne GitHubi tehniline projekt valmistatakse käesolevas etapis ette; kuluhinnang hõlmab ka reaalset kasutuselevõttu ja testimist.

## 4. Etapp 1 – kohese käivitamise ülesanded

- [x] Määrata MVP andmeskeem ja allikad.
- [x] Kirjutada Python impordimootor ja allikate kaardistused `config/sources.json`.
- [x] Luua igapäevase ja käsitsi käivitatava Actionsi töövoo definitsioon.
- [x] Luua GitHub Pagesi staatiline leht, JSON ja CSV avaldamise mehhanism.
- [x] Lisada offline ühiktestid ja rikkis allikate blokeerimise loogika.
- [ ] Luua uus avalik repositoorium kliendi omanduses (vajalik sobiv GitHubi ühendus/õigus).
- [ ] Laadida failid repositooriumi ja aktiveerida Settings → Pages → GitHub Actions.
- [ ] Käivitada esimene reaalne import ja kontrollida EU/OFAC/UK väljundi õigsust.
- [ ] Kinnitada testitud andmete avaldamine ja töövoo vastutaja.

## 5. Kvaliteedinõuded

1. Iga andmeallikas tagastab vähemalt seadistatud miinimumarvu laevakirjeid; puuduvad kohustuslikud IMO/name väljad põhjustavad vea. Kui eelmisest versioonist kaob ebaharilikult suur osa kirjetest, import peatatakse.
2. Mitte ühtki uut CSV/JSON versiooni ei avaldata, kui kas või üks allikas vigane on. Pagesis jääb viimati edukalt avaldatud versioon, mis vananedes tähistatakse eraldi.
3. JSON ja CSV sisaldavad kõiki sama IMO kohta leitud loendeid; ühe nimekirja positiivne vaste ei peida teist.
4. IMO-d käsitletakse tekstina (7 numbrit). Nimed on informatiivsed; põhivõti on IMO.
5. Iga versiooni juures on impordi UTC ajatempel, allikapõhised ajatemplid, kirjekogused ning lähtesisendi SHA-256 räsi.
6. Kõik avaldatavad failid sisaldavad ainult avalikke sanktsiooniandmeid, mitte klientide töödeldud deklaratsioone.
7. Nicepage'i autentimist ega sisemist kindlustuse arvutusloogikat ei kirjutata GitHub Pagesi.
8. Exceli kasutaja saab vajadusel kontrolli uuendada käsitsi; katkist või vananenud allikat ei kuvata kui `No Sanctions`.

## 6. Põhiriskid ja maandamine

| Risk | Mõju | Maandamine |
|---|---|---|
| Ametliku CSV/HTML kuju muutub | Import ebaõnnestub või kaob laevu | Konfiguratsioonis muudetavad veeruvastendused, ühiktestid, kirjekoguste kontroll, veateavitus |
| GitHub Actionsi ajastus viibib / töö seiskub | Andmed aeguvad | `status.json` värskuse kontroll ja manuaalkäivitus; Actionsi veateavitused |
| Osa allikaid tagastab 403/429 | Import jääb tegemata | Viimane korrektne versioon alles, proovida ametlikku alternatiivset allalaadimisaadressi |
| Nicepage'i ligipääsukaitse ei kata kontrollilehte | Teenus ei ole kliendi soovitud ligipääsupiiranguga | Kontrollida majutus- ja autentimislahendust eraldi; Pages ise on avalik |
| Konfidentsiaalsed andmed satuvad Githubi | Andmeleke | Eristada avalikud sanktsioonid ja privaatne register; hoiduda kliendifailide commit'ist |
| Igakuiste deklaratsioonide Exceli viiteid ei saa lihtsalt parandada | Lisaarenduse vajadus | Enne töömahukinnitust analüüsida konkreetset faili |
| Kliendil puudub GitHubi kasutushaldus | Hooldus sõltub tarnijast | Repo kliendi omanduses, vähemalt kaks admini, kirjalik hooldusjuhend |

## 7. Ülalpidamiskulu

GitHub Actionsi avaliku repo tavalised hosted-runner'i minutid ning GitHub Pages võivad jääda GitHub Free paketi piirides tasuta kasutatavaks. Kuna veebis avaldamise tingimuseks on avalik repo, ei tohi sinna panna konfidentsiaalseid andmeid. Olemasoleva Microsoft 365 litsentsi raames Power Automate'i tööde sobivus tuleb eraldi üle kontrollida; Premium-ühendused võivad lisada kulu. Hooldus- ja arendajatöö ei ole tasuta jooksutamise hinnangu sees.

## 8. Vastutused ja lahtised otsused

- **Insure Consult:** repo omanik/ligipääsud, töövoo kontrollijuht, sanktsioonikontrollide ärilised vastuvõtutestid, Nicepage'i ligipääs, igakuise deklaratsiooni Exceli näidis, PDF-i aruande soovitud vorm.
- **Arendaja:** impordiparserid, Actions/Pages ülesseadmine, Excel/Nicepage ühendamine, tehniline testimine ja juhend.
- **Vajavad kinnitamist:** kas PDF tehakse ühe deklaratsiooni kohta või iga laeva kohta; Nicepage'i majutaja ja autentimisviis; soovitud veateavituse saaja; kas EU/DMA RU Annex XLII ulatus on senise Exceliga identne; repo kontoomanik.

## 9. Üleandmiskriteeriumid

Klient suudab veebis kontrollida IMO-d, Excelis teha seni kasutatud kontrolli ja lisapreemia arvutusi, salvestada kontrolli tõenduseks PDF-i ning muuta lihtsaid CSV veeruvastendusi. Tehniline vastuvõtt eeldab **päris allikate** vastu edukalt läbinud teste. Kuni selleni on tarkvara kasutuselevõtu eelses olekus.
