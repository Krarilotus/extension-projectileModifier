# Projectile Modifier

Állítsd be mind a 77 egységtípus lövedékeit, sortüzének méretét és automatikus tüzelési időközét. A katapult mangonelköveket lőhet; az ostromtornyok és a közelharci egységek automatikus távolsági támadást kaphatnak.

**Balance Changes → Lövedékek**

Nyiss meg egy csoportot, majd egy egységet. A kard jelölőnégyzetével engedélyezheted a számérték módosítását; a beállítást lenyitva olvashatod a súgót. A kikapcsolt beállítások megtartják a fájl értékeit vagy az eredeti működést. A változtatások alkalmazásához indítsd újra a játékot.

Engedélyezi az automatikus tüzelést a közelharci egységeknek és az ostromtornyoknak is. Alapértelmezés szerint lecseréli az eredeti lövéseket. Az eredeti lövedéket használja, ennek hiányában nyilakat. A játékütem szimulációs lépés, nem ezredmásodperc.

Az automatikus tüzelés célpontjai. A szövetséges egységek és épületek kimaradnak. A falak közé a saját falak is beletartoznak. Egyéni fontossági sorrend a YAML-fájlban adható meg.

Tölts be YAML-fájlt a haladó beállításokhoz: mozgás, késleltetett sortűz, pontosság, magasság és animáció. Az alább bekapcsolt beállítások felülírják a fájl értékeit. Fájl nélkül az alapbeállítások használhatók. Példák és teljes táblázat a README.md fájlban; szerkesztési séma a projectile-config.schema.json fájlban.

UCP 3.0.7+, map-extensions 1.x és Crusader/Extreme 1.41 szükséges. Az időzítők és a függőben lévő sortüzek mentésre kerülnek; betöltéshez egyező beállítások kellenek. Ez az aláíratlan 1.3.2-es tesztváltozat Monsterfish 1.2.0-s verziójára épül. A játékon belüli, többjátékos és felvételi ellenőrzések még hátravannak; lásd VALIDATION.md. A fejlesztői referencia angol nyelvű.
