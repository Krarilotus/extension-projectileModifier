# Custom Projectiles

Szabd testre, mit lőnek ki az egységek, milyen gyakran és milyen messzire tüzelnek, és mely célpontokat részesítik előnyben.

## Használat

1. Normál játékhoz hagyd üresen a **Lövedékbeállítások fájlja (YAML)** mezőt.
2. Másold a `vanilla-projectiles.yml` fájlt a bővítmény mappájából vagy a ZIP-fájlból a játék `ucp/resources/custom-projectiles/` mappájába. Ha kell, hozd létre a mappát, majd szerkeszd a másolatot, és válaszd ki a **Testreszabások > Balance Changes** menüben.
3. Indítsd újra a játékot.

## Mire képes

A másolatodban keresd meg a megfelelő egységet, és cseréld le a `native` értékeit a megadottakra.

### Az íjászok újratöltésének lassítása

Adj az európai íjászoknak több időt két lövés között.

```yaml
units:
  European archer:
    interval: 600
```

### Nagyobb hatótáv a katapultoknak

Engedd, hogy a katapultok akár 40 mezőre lévő célpontokra is lőhessenek.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

### Több kő kilövése egyszerre

Állítsd be, hogy a kővetőgép minden sortűzzel tíz követ lőjön ki.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Egy kővetőgép sortüze repülés közben](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/534bfdd4d0c01dfdefece636841d2fc336bc0ddb/docs/screenshots/mangonel-volley.jpg)

### Lőszer kiválasztása célpont szerint

Állítsd be, hogy a katapultok automatikusan teheneket lőjenek az ellenséges katapultokra.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

## Mentések

A mentések a fájl módosítása után is betölthetők: a módosított beállítások újraindítják a lövési időzítőket, a repülő lövedékek elveszítik a módosított egyéni grafikát, a lerakott díszek pedig, amelyek típusát törölted, egyszerű tűztartókká válnak. A mentések kikapcsolt modullal is betölthetők. Írd a fájl elejére: `allow_config_changes_on_load: false`, ha a más beállításokkal készült mentéseket el akarod utasítani.

*Megjegyzés: ez egy gépi fordítás, amely még emberi ellenőrzésre vár.*
