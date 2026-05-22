# 🏃 Turf Game Integration för Home Assistant

En anpassad integration (Custom Component) för att hämta statistik och information från det platsbaserade mobilspelet [Turf](https://turfgame.com/) in i Home Assistant.

## ✨ Funktioner

Just nu stöder integrationen följande:
- **Zoner:** Visar hur många zoner en specifik spelare "äger" just nu.

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

## 🐞 Felsökning

* **"Config flow could not be loaded"**: Dubbelkolla att din mapp heter exakt `turf_game` (med understreck, inte bindestreck).
* **Ogiltigt användarnamn**: Kontrollera att spelarnamnet är rättstavat och existerar i Turf.

---

*Denna integration är ett hobbyprojekt skapat av communityt och är inte officiellt kopplad till Andrimner (utvecklarna bakom Turf).*