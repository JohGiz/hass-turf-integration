# 🏃 Turf Game Integration för Home Assistant

En anpassad integration (Custom Component) för att hämta statistik och information från det platsbaserade mobilspelet [Turf](https://turfgame.com/) in i Home Assistant.

## ✨ Funktioner

Just nu stöder integrationen följande:
- **Zoner:** Visar hur många zoner en specifik spelare "äger" just nu.
- **Poäng per timme:** Visar hur många poäng per timme spelaren får just nu.
- **Rank/Titel:** Visar spelarens aktuella rank/titel (t.ex. *Turf Grandmaster*) baserat på totala karriärpoäng. Sensorn har även attributen `rank_level` (nivå 0–60) och `total_points`.
- **Placering:** Visar spelarens aktuella globala placering i den pågående spelomgången.
- **Senaste zonerna:** Visar namnet på den allra senast skapade zonen. I sensorns attribut sparas en lista med de senaste zonerna och i vilken region de ligger.
- **Bevakade regioner:** En sensor per konto som visar senast skapade zon i kontots bevakade regioner. Attributet `new_zones` innehåller alla matchande zoner från flödet, `watched_regions` visar vilka regioner som bevakas.
- **Bevakade areor:** Samma som ovan men filtrerat på area istället för region.
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

## 🗺️ Bevakade regioner och areor

Du kan låta integrationen bevaka nya zoner i valda regioner och/eller areor. Varje konto får egna sensorer — en för regioner och en för areor — vilket gör det möjligt att skicka personliga notiser per konto.

### Ställ in vid installation

I installationssteget finns två valfria fält:

- **Bevaka nya zoner i regioner** – kommaseparerad lista med regionnamn, t.ex. `Stockholm, Västra Götaland`
- **Bevaka nya zoner i areor** – kommaseparerad lista med areanamn, t.ex. `Stockholms kommun, Göteborgs kommun`

### Ändra utan att installera om

1. Gå till **Inställningar** → **Enheter och tjänster** i Home Assistant.
2. Hitta **Turf Game Integration** och klicka på **Konfigurera**.
3. Uppdatera listorna och klicka på **Skicka**. Integrationen startar om automatiskt.

### Sensorernas namn

Varje konfigurerad spelare får egna sensorer, namngivna efter Turf-användarnamnet:

| Sensor            | Entity ID                                                  |
|-------------------|------------------------------------------------------------|
| Bevakade regioner | `sensor.turf_latest_zones_in_watched_regions_användarnamn` |
| Bevakade areor    | `sensor.turf_latest_zones_in_watched_areas_användarnamn`   |

Sensorns värde är namnet på den senast skapade zonen i någon av spelarens bevakade regioner/areor. Attributet `new_zones` innehåller alla matchande zoner från det aktuella flödet, och `watched_regions`/`watched_areas` visar vilka som bevakas.

---

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
    * **{{ zone.name }}** ({{ zone.area }}{% if zone.area %}, {% endif %}{{ zone.region }}) - *för {{ relative_time(as_datetime(zone.dateCreated)) }} sedan*
    {% endfor %}
  {% else %}
    *Laddar data från Turf...*
  {% endif %}
```
*(Tipset ovan visar de 10 senaste zonerna, men du kan ändra siffran om du vill se fler eller färre).*

## 📊 Visa spelarstatistik på en Dashboard

För att visa spelarens aktuella statistik (inklusive rank, placering, zoner och poäng) kan du lägga till ett **Entitetskort** eller ett **Markdown-kort** på din dashboard:

### Alternativ 1: Entitetskort (Lista)
Det här kortet visar spelarens värden i en ren lista. Ersätt `användarnamn` med det konfigurerade Turf-användarnamnet (t.ex. `sensor.turf_rank_grock` om användarnamnet är `grock`).

```yaml
type: entities
title: "🏃 Turf-statistik"
show_header_toggle: false
entities:
  - entity: sensor.turf_rank_användarnamn
    name: Aktuell Rank/Titel
    icon: mdi:shield-star
  - entity: sensor.turf_place_användarnamn
    name: Placering i omgången
    icon: mdi:trophy-outline
  - entity: sensor.turf_zones_användarnamn
    name: Ägda zoner just nu
    icon: mdi:map-marker-multiple
  - entity: sensor.turf_points_per_hour_användarnamn
    name: Poäng per timme (PPH)
    icon: mdi:speedometer
```

### Alternativ 2: Markdown-kort (Profilkort)
Det här kortet hämtar attributen och formaterar spelarens profil vackert med text och ikoner. Ersätt `användarnamn` med ditt Turf-användarnamn.

```yaml
type: markdown
title: "🏆 Turf Profil"
content: |-
  ### 👤 Spelarinfo
  * **Titel/Rank:** {{ states('sensor.turf_rank_användarnamn') }} *(Nivå {{ state_attr('sensor.turf_rank_användarnamn', 'rank_level') }})*
  * **Placering i rundan:** Plats **{{ states('sensor.turf_place_användarnamn') }}** i världen 🌍

  ### 📊 Speldata
  * **Ägda zoner:** {{ states('sensor.turf_zones_användarnamn') }} st 📍
  * **Aktuellt flöde:** {{ states('sensor.turf_points_per_hour_användarnamn') }} PPH ⚡
  * **Totala poäng (karriär):** {{ state_attr('sensor.turf_rank_användarnamn', 'total_points') | int }} poäng 🌟
```

## 🤖 Automatisera notiser för nya zoner

När du har konfigurerat bevakade regioner och/eller areor kan du låta Home Assistant skicka en push-notis direkt när en ny zon dyker upp i flödet. Du får en separat notis per sensortyp — en för regioner och en för areor — så att det alltid är tydligt vad notisen gäller.

1. Gå till **Inställningar** → **Automatiseringar och scener** och skapa en ny automatisering.
2. Klicka på de tre prickarna uppe till höger och välj **Redigera i YAML**.
3. Klistra in följande kod och byt ut `användarnamn` mot ditt Turf-användarnamn och `notify.mobile_app_din_telefon` mot ditt enhets-id för notiser.

```yaml
alias: "Turf: Ny zon i bevakade regioner/areor (användarnamn)"
description: "Skickar en notis när en ny zon skapas i en bevakad region eller area."
mode: parallel

trigger:
  - platform: state
    entity_id:
      - sensor.turf_latest_zones_in_watched_regions_användarnamn
      - sensor.turf_latest_zones_in_watched_areas_användarnamn

condition:
  - condition: template
    value_template: "{{ trigger.to_state.attributes.count > 0 }}"

action:
  - choose:
      - conditions:
          - condition: template
            value_template: >
              {{ trigger.entity_id == 'sensor.turf_latest_zones_in_watched_regions_användarnamn' }}
        sequence:
          - service: notify.mobile_app_din_telefon
            data:
              title: "🌟 Nya Turf-zoner i bevakade regioner"
              message: >
                {% set zones = trigger.to_state.attributes.new_zones %}
                {% set ns = namespace(lines=[]) %}
                {% for r in (zones | map(attribute='region') | unique | list) %}
                  {% set ns.lines = ns.lines + [r + ": " + (zones | selectattr('region', 'equalto', r) | map(attribute='name') | join(', '))] %}
                {% endfor %}
                {{ ns.lines | join('\n') }}

      - conditions:
          - condition: template
            value_template: >
              {{ trigger.entity_id == 'sensor.turf_latest_zones_in_watched_areas_användarnamn' }}
        sequence:
          - service: notify.mobile_app_din_telefon
            data:
              title: "🌟 Nya Turf-zoner i bevakade areor"
              message: >
                {% set zones = trigger.to_state.attributes.new_zones %}
                {% set ns = namespace(lines=[]) %}
                {% for a in (zones | map(attribute='area') | unique | list) %}
                  {% set ns.lines = ns.lines + [a + ": " + (zones | selectattr('area', 'equalto', a) | map(attribute='name') | join(', '))] %}
                {% endfor %}
                {{ ns.lines | join('\n') }}
```

Notisen kan se ut så här om det finns nya zoner i två bevakade regioner:

> **Nya Turf-zoner i bevakade regioner**
> Stockholm: Vasagatan42, Kungsgatan7
> Västra Götaland: Avenyn5

*Varje Turf-konto får egna sensorer — om du har flera konton konfigurerade skapar du en separat automation per konto. Regionerna/areorna styrs enbart via integrationens konfiguration, ingen ändring i automationen behövs när du lägger till eller tar bort regioner.*

## 🐞 Felsökning

* **Ogiltigt användarnamn**: Kontrollera att spelarnamnet är rättstavat och existerar i Turf.

---

*Koden har till stor del tagits fram med hjälp av Gemini AI.*
