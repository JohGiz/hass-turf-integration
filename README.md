# 🏃 Turf Game Integration för Home Assistant

En anpassad integration (Custom Component) för att hämta statistik och information från det platsbaserade mobilspelet [Turf](https://turfgame.com/) in i Home Assistant.

## ✨ Funktioner

Just nu stöder integrationen följande:
- **Zoner:** Visar hur många zoner en specifik spelare "äger" just nu.
- **Poäng per timme:** Visar hur många poäng per timme spelaren får just nu.
- **Senaste zonerna:** Visar namnet på den allra senast skapade zonen. I sensorns attribut sparas en lista med de senaste zonerna och i vilken region de ligger.
- **Zonägare:** Visar vem som för tillfället äger en specifik zon. Du väljer själv vilka zoner du vill bevaka – en sensor skapas automatiskt per zon. Sensorn har även attributen `latitude`, `longitude` och `owned_by_player` (sant/falskt beroende på om den konfigurerade spelaren äger zonen just nu).

*💡 Tips: Du kan lägga till flera spelare genom att skapa fler konfigurationer ("entries") under integrationen i Home Assistant! Varje spelare får sina egna sensorer för zoner och poäng per timme, medan listan för senaste zonerna delas.*

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

## 🎯 Bevakade zoner

Du kan välja vilka specifika Turf-zoner du vill hålla koll på. För varje zon skapas en sensor som visar vem som äger den, och om det är du.

### Ställ in bevakade zoner vid installation

I installationssteget finns ett valfritt fält **Bevakade zoner** där du kan ange en kommaseparerad lista med zonnamn, t.ex.:

```
ZoneAlpha, ZoneBeta, MinFavoritzon
```

*Zonnamnen måste stämma exakt (inklusive versaler) med hur de heter i Turf.*

### Ändra bevakade zoner utan att installera om

Du kan när som helst lägga till eller ta bort bevakade zoner utan att behöva ta bort och lägga till integrationen på nytt:

1. Gå till **Inställningar** -> **Enheter och tjänster** i Home Assistant.
2. Hitta **Turf Game Integration** och klicka på **Konfigurera**.
3. Uppdatera listan med bevakade zoner och klicka på **Skicka**.
4. Integrationen startar om automatiskt och sensorerna uppdateras direkt.

### Sensorernas namn

Varje bevakad zon får en sensor med namnet `Turf Zone <zonnamn>`, t.ex. `sensor.turf_zone_zonealpha`. Sensorns värde är namnet på den nuvarande ägaren, eller `Ingen ägare` om zonen saknar ägare.

## 🔔 Automatisera notis när någon tar din zon

Med attributet `owned_by_player` kan du låta Home Assistant skicka en push-notis direkt när någon tar en av dina bevakade zoner.

1. Gå till **Inställningar** -> **Automatiseringar och scener** och skapa en ny automatisering.
2. Klicka på de tre prickarna uppe till höger och välj **Redigera i YAML**.
3. Klistra in följande kod (byt ut `sensor.turf_zone_minzon` mot din egen sensors id och `notify.mobile_app_din_telefon` mot ditt enhets-id för notiser):

```yaml
alias: "Turf: Någon tog min zon"
description: "Skickar en notis när en bevakad zon byter ägare bort från mig."
mode: single

trigger:
  - platform: state
    entity_id: sensor.turf_zone_minzon
    attribute: owned_by_player
    from: true
    to: false
action:
  - service: notify.mobile_app_din_telefon
    data:
      title: "😱 Någon tog din zon!"
      message: "{{ state_attr('sensor.turf_zone_minzon', 'zone_name') }} ägs nu av {{ states('sensor.turf_zone_minzon') }}!"
```

## 📊 Visa senaste zonerna på en Dashboard

För att visa en snygg lista med de senast skapade zonerna på din Home Assistant-dashboard kan du använda ett inbyggt **Markdown-kort**.

1. Gå till din dashboard och klicka på **Redigera översikt**.
2. Klicka på **Lägg till kort** och välj **Markdown**.
3. Klistra in följande kod under fliken för kodredigering:

```yaml
type: markdown
title: 🌟 Senaste Turf-zonerna
content: |-
  {% set new_zones = state_attr('sensor.turf_latest_created_zones', 'new_zones') %}
  {% if new_zones %}
    {% for zone in new_zones[:10] %}
    * **{{ zone.name }}** ({{ zone.region }}) - *för {{ relative_time(as_datetime(zone.dateCreated)) }} sedan*
    {% endfor %}
  {% else %}
    *Laddar data från Turf...*
  {% endif %}
```
*(Tipset ovan visar de 10 senaste zonerna, men du kan ändra siffran om du vill se fler eller färre).*

## 🤖 Automatisera notiser för nya zoner

Du kan låta Home Assistant skicka en push-notis till din mobil så fort en ny zon skapas i din region (t.ex. "Stockholm" eller "Skåne").

1. Gå till Inställningar -> Automatiseringar och scener och skapa en ny automatisering. 
2. Klicka på de tre prickarna uppe till höger och välj Redigera i YAML. 
3. Klistra in följande kod (glöm inte att byta ut `Stockholm` mot din egen region och `notify.mobile_app_din_telefon` mot ditt eget enhets-id för notiser): 

```yaml 
alias: "Turf: Ny zon skapad i min region"
description: "Skickar en notis när en ny Turf-zon skapas i en specifik region." 
mode: single 

trigger:
  - platform: state
    entity_id: sensor.turf_latest_created_zones 
condition:
  - condition: template
    value_template: "{{ states('sensor.turf_latest_created_zones') not in ['unknown', 'unavailable'] and state_attr('sensor.turf_latest_created_zones', 'new_zones') and state_attr('sensor.turf_latest_created_zones', 'new_zones')[0].region == 'Stockholm' }}"
action:
  - service: notify.mobile_app_din_telefon
    data:
      title: "🌟 Ny Turf-zon!"
      message: "Zonen {{ states('sensor.turf_latest_created_zones') }} har precis skapats i din region!"

```

## 🐞 Felsökning

* **Ogiltigt användarnamn**: Kontrollera att spelarnamnet är rättstavat och existerar i Turf.

---

*Koden har till stor del tagits fram med hjälp av Gemini AI.*
