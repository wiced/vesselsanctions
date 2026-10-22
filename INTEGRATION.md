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

## Excel – Power Query

Failid: examples/SanktsiooniVasted.pq ja examples/LaevadeKontroll.pq.

1. Ava kliendi PRIVAATNE Excel: Data → Get Data → From Other Sources → Blank Query → Advanced Editor. Kopeeri esimese PQ-faili kogu M-kood, nimeta päring SanktsiooniVasted.
2. Veebiühenduse autentimiseks kasuta Anonymous, sest GitHub Pagesi sanktsiooniandmestik on avalik.
3. Veendu, et IMO on tekstiväli. Esimese päringu väljundis on IMO, Laev, Allikas, Programm, Viide, NimekirjaKuupaev ja AndmedSeisugaUTC.
4. Teises, kliendi laevade võrdluse päringus eeldatakse kohaliku Exceli Table nimega Laevad ja selle veergu IMO (tekst). Kui see tabel on olemas, kopeeri teise PQ-faili M-kood uude tühja päringusse ja nimeta see LaevadeKontroll.
5. Väljund säilitab kliendi enda laevaregistri veerud ja lisab SanctionSources, SanctionEntries, SanctionScreening ja SanctionsDataAtUTC.
6. Laadi ühendatud tulemus eraldi lehele. Ära kirjuta olemasolevate kindlustuspreemia valemite peale. Vajadusel ühenda vana arvutuslehe kõrvalveerud IMO järgi, näiteks XLOOKUP abil.
7. Tee Data → Refresh All. Kontrolli Queries & Connections, et mõlemad päringud õnnestusid. Nurjunud uuenduse korral võib Excel kuvada vanemat laetud andmestikku; seda ei tohi kasutada värske kontrollina.

Väljundid:
- VASTE LEITUD – vähemalt üks IMO-vastavus sanktsiooniallikas.
- VASTET EI LEITUD KONTROLLITUD NIMEKIRJADEST – mitte tehingu lubatavuse kinnitamine.
- KONTROLLIMATA – vigane IMO – sisend vajab parandamist.
- Power Query värskuse/versiooni viga – kontroll pole valmis, ära käsitle puuduvat vastet negatiivse tulemusena.

## Piirangud ja üleandmine

- Kliendi Excel, laevaregister, deklaratsioonid ja kindlustuse hinnastus jäävad Microsoft 365 privaatsetesse failidesse, mitte GitHub Pagesi.
- Allikad hõlmavad EU/DMA Venemaa/Valgevene Annex XLII laevu, OFAC SDN laevakirjeid ja UK Sanctions List laevu. Muud programmid, laeva omanikud ja tegelikud kasusaajad vajavad eraldi kontrolli.
- Enne tootmiskasutust tuleb päris Windows Exceli failis kontrollida Power Query, olemasolevate valemite säilimist ja veebis CORS ning autentimist.
- Käesolevad näidised ei saa automaatselt muuta kliendi päris Excelit ega Nicepage'i ilma vastava faili/saidihalduseta.
