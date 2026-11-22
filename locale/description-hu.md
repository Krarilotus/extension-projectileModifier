# Custom Projectiles

Szabd testre, mit lőnek ki az egységek, milyen gyakran és milyen messzire tüzelnek, és mely célpontokat részesítik előnyben.

## Használat

1. Normál játékhoz hagyd üresen a **Lövedékbeállítások fájlja (YAML)** mezőt.
2. Másold a `vanilla-projectiles.yml` fájlt a bővítmény mappájából vagy a ZIP-fájlból a játék `ucp/resources/custom-projectiles/` mappájába. Ha kell, hozd létre a mappát, majd szerkeszd a másolatot, és válaszd ki a **Testreszabások > Balance Changes** menüben.
3. Indítsd újra a játékot.

## Mire képes

Add hozzá ezeket a beállításokat a megfelelő egységhez a másolatodban.

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

### Lőszer kiválasztása célpont szerint

Állítsd be, hogy a katapultok automatikusan teheneket lőjenek az ellenséges katapultokra.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

*Megjegyzés: ez egy gépi fordítás, amely még emberi ellenőrzésre vár.*
