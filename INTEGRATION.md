# Insure Consult – Exceli ja Nicepage'i ühendamine

**Seis 22.10.2026:** GitHub Actions ja Pages avaldasid EU, OFAC SDN ning UK IMO-põhised sanktsiooniandmed. See ei tähenda, et kliendi tegelik Excel või Nicepage leht oleks juba muudetud. Need asuvad väljaspool avalikku GitHubi repositooriumi.

## Andmete URL-id

- Olek: https://wiced.github.io/vesselsanctions/data/status.json
- JSON: https://wiced.github.io/vesselsanctions/data/vessels.json
- CSV: https://wiced.github.io/vesselsanctions/data/vessels.csv

URL-id on avalikud ja neis ei tohi olla kliendi laevaregistrit ega ärisaladusi.

## Nicepage'i vana staatilise nimekirja asendamine

Varem kasutatud HTML-koodis on muutuja g_vellel ja funktsioon validateValue. Need põhinevad käsitsi kopeeritud loendil.

1. Ava Nicepage'i juurdepääsukaitsega IMO kontrollilehe muutmine.
2. Eemalda kogu senine g_vellel skript, validateValue funktsioon ja vana IMO vorm. Ära hoia vana ja uut kontrolli korraga!
3. Kopeeri kogu examples/nicepage-embed.html sisu Nicepage'i HTML Code elementi. Kood sisaldab ise vormi ning tekste; vana input id=imo ei ole eraldi vaja.
4. Avalda leht. Kontrolli, et kasutaja peab lehele pääsemiseks ikka sisse logima. JavaScript ei ole autentimisvahend.
5. Testi lehel tegelikus hostidomeenis status.json ja vessels.json päringuid, HTTP vastuseid ning CORS-i brauseri Network vaates.
6. Positiivsed näited: 9179842 ANGARA (EU/OFAC/UK), 9179854 ADLER (OFAC), 9402263 ASTERAS (UK).
7. 1234568 on vigase kontrollnumbriga näide ning ei tohi anda negatiivset sanktsioonivastet.
8. Ühenduse katkemisel peab kasutaja saama veateate, mitte kinnituse, et sanktsioone ei leitud. Värskelt laetud viieminutiline vahemälu võib ajutiselt jääda kasutatavaks.

**Oluline:** vaste puudumine kontrollitud IMO-nimekirjadest EI tähenda, et laev või tehing on sanktsioonide mõttes lubatud.

## Excel – kontrollitud algfaili struktuur (22.10.2026)

Kliendi üles laaditud algse Exceli lehed: **Vessel List**, **sdn**, **UK-Sanctions-List**, **EU Sanctioned Vessels**. Peamine Excel Table on **Vessel_List**, IMO on veerg **Vessel IMO No**. Olemasolevates **J:L** veergudes on vanad XLOOKUP-id, mis tagastavad sageli "No Sanctions" ka siis, kui allikad on aegunud. UK lähteleht on 57 614 rea pikkune; originaali sees on olemas kolme vana Power Query ühenduse metaandmed. Algset faili ei kirjutatud üle.

**Uued päringud:**
- [examples/Sanktsioonid.pq](examples/Sanktsioonid.pq): GitHub Pagesi JSON, allikate ja värskuse valideerimine, üks rida IMO kohta; väljundveerud IMO, EU, OFAC, UK, Allikad, AndmedSeisugaUTC.
- [examples/LaevadeKontroll.pq](examples/LaevadeKontroll.pq): loeb kliendi privaatset tabelit **Vessel_List**, kontrollib IMO kontrollnumbrit, ühendab allikavasted ja säilitab algsed laevaandmed; vana J:L tulemused vahetatakse uue päringu väljundis välja.
- [examples/SanktsiooniVasted.pq](examples/SanktsiooniVasted.pq): alternatiivne pikem vastete loend detailandmetega.

**Kasutuselevõtu sammud (Windows Excel Desktop):**
1. Hoia originaalfailist varukoopia ning ava see Excelis.
2. Data → Get Data → From Other Sources → Blank Query → Advanced Editor; kleebi `Sanktsioonid.pq` sisu. Nimeta päring **Sanktsioonid** ning vali veebiühenduse jaoks **Anonymous**.
3. Loo teise Blank Query kaudu **LaevadeKontroll**, kleebi `LaevadeKontroll.pq` ja kontrolli, et see viitab olemasolevale **Vessel_List** tabelile.
4. **Load To → Table → New worksheet**. Ära laadi tulemust vana Vessel List töölehe peale, kuna Power Query ei tohi kirjutada oma sisendtabelisse ega rikkuda ettevõtte arvutusvalemeid.
5. Kontrolli uuel lehel 1718 registrikirje olemasolu (sealhulgas korduvad IMO numbrid), 38 sanktsioonivastega rida ja 7 vigase IMO-ga rida vastavalt 22.10.2026 kontrollseisule. Hilisem ametlik andmestik võib arve muuta.
6. Data → Refresh All; Queries & Connections vaates peavad mõlemad uued päringud edukalt lõpetama. Kui vanad päringud **sdn**, **UK-Sanctions-List** ja **Table 1** põhjustavad Refresh All probleeme, lülita nende Properties alt **Include in Refresh All** välja alles pärast uue kontrolli toimimise kinnitamist.
7. Kuna nurjunud Power Query võib jätta tabelisse vana edukalt loetud tulemuse, jälgi alati **AndmedSeisugaUTC** veergu ja päringute viimast värskendust. Aegunud andmestikku ei tohi tõlgendada negatiivseks sanktsioonikontrolliks.
8. Pärast edukat testimist saab vana kolme lähteandmete lehe eemaldamise ja vanade J:L valemite asendamise eraldi planeerida. Ära tee seda enne, kui kindlustuse hinnastus ja sõltuvad valemid on kontrollitud.

Väljundid: **VASTE LEITUD**, **VASTET EI LEITUD KONTROLLITUD LOENDITEST**, **KONTROLLIMATA – VIGANE IMO**. Vaste puudumine ei kinnita tehingu lubatavust.

## Piirangud ja üleandmine

- Kliendi Excel, laevaregister, deklaratsioonid ja kindlustuse hinnastus jäävad Microsoft 365 privaatsetesse failidesse, mitte GitHub Pagesi.
- Allikad hõlmavad EU/DMA Venemaa/Valgevene Annex XLII laevu, OFAC SDN laevakirjeid ja UK Sanctions List laevu. Muud programmid, laeva omanikud ja tegelikud kasusaajad vajavad eraldi kontrolli.
- Enne tootmiskasutust tuleb päris Windows Exceli failis kontrollida Power Query, olemasolevate valemite säilimist ja veebis CORS ning autentimist.
- Käesolevad näidised ei saa automaatselt muuta kliendi päris Excelit ega Nicepage'i ilma vastava faili/saidihalduseta.
