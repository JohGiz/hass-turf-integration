# 🏃 Turf Game Integration för Home Assistant

En anpassad integration (Custom Component) för att hämta statistik och information från det platsbaserade mobilspelet [Turf](https://turfgame.com/) in i Home Assistant.

## ✨ Funktioner

Just nu stöder integrationen följande:
- **Zoner:** Visar hur många zoner en specifik spelare "äger" just nu.
- **Poäng per timme:** Visar hur många poäng per timme spelaren får just nu.
- **Senaste zonerna:** Visar namnet på den allra senast skapade zonen. I sensorns attribut sparas en lista med de senaste zonerna och i vilken region de ligger.

*💡 Tips: Du kan lägga till integrationen flera gånger i Home Assistant för att följa flera olika spelare samtidigt! Varje spelare får sina egna sensorer för zoner och poäng per timme, medan listan för senaste zonerna delas.*

*(Fler sensorer kan komma att läggas till i framtida uppdateringar.)*

## 📥 Installation via HACS (Rekommenderas)

Det enklaste sättet att installera denna integration är via [HACS](https://hacs.xyz/):

1. Öppna HACS i din Home Assistant.
2. Klicka på de tre prickarna i övre högra hörnet och välj **Custom repositories**.
3. Klistra in URL:en till detta GitHub-repo och välj kategorin **Integration**.
4. Sök efter "Turf Game" i HACS och klicka på **Ladda ner** (Download).
5. **Starta om Home Assistant**.

## ⚙️ Konfiguration

När Home Assistant har startat om gör du följande för att lägga till din sensor:

1. Gå till **Inställningar** -> **Enheter och tjänster** i Home Assistant.
2. Klicka på knappen **+ Lägg till integration**.
3. Sök efter **Turf Game Integration** och klicka på den.
4. Fyll i det **Turf-användarnamn** du vill hämta data för.
5. Klart! Sensorn kommer nu att hämta ny data från Turf var 5:e minut.

## 📊 Visa senaste zonerna på en Dashboard

För att visa en snygg lista med de senast skapade zonerna på din Home Assistant-dashboard kan du använda ett inbyggt **Markdown-kort**.

1. Gå till din dashboard och klicka på **Redigera översikt**.
2. Klicka på **Lägg till kort** och välj **Markdown**.
3. Klistra in följande kod under fliken för kodredigering:

```yaml
type: markdown
title: 🌟 Senaste Turf-zonerna
content: |-
  {% for zone in state_attr('sensor.turf_latest_created_zones', 'new_zones')[:10] %}
  * **{{ zone.name }}** ({{ zone.region }}) - *för {{ relative_time(as_datetime(zone.dateCreated)) }} sedan*
  {% endfor %}
```
*(Tipset ovan visar de 10 senaste zonerna, men du kan ändra siffran om du vill se fler eller färre).*

## 🐞 Felsökning

* **Ogiltigt användarnamn**: Kontrollera att spelarnamnet är rättstavat och existerar i Turf.

---

*Koden har till stor del tagits fram med hjälp av Gemini AI.*