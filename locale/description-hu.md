# Custom Projectiles 1.8.6

Mind a 77 egységtípus YAML-ban állítható. A normál lövedékek és a tehenek külön kezelhetők. Az időközök igazodnak a támogatott tüzelési animációkhoz; az inaccuracy játékbeli egységei: 1 = 1/8 mező, 8 = 1 mező, 0 = pontos célzás.

A csoportméret-korlát csak az MI célzására vonatkozik; a játékos támadási parancsait nem tiltja.

Másold ki a teljes vanilla-projectiles.yml fájlt a ZIP-ből, szerkeszd, majd válaszd ki a másolatot. A native megőrzi a játék szabályait; az üres útvonal nem változtat semmin. Az auto_targeting: false csak kézi támadási parancsokat enged. A strict_range: false visszaállítja a kerekített hatótáv-ellenőrzést; a turn_before_shot: false kikapcsolja a fordulás javítását. A kötelező/javasolt jelölés a teljes fájl kiválasztására vonatkozik. Módosítás után indítsd újra a játékot.

Saját grafika: a projectiles alatt adj meg egy nevet inherits és sprites mezőkkel (teljes, megfelelő GM1-fájl). A decorations és az egységek near_decorations szabályai után a parázstartó gombbal helyezhetők el a díszítések. Formátumok: README.md és examples/custom-sprites-and-decorations.yml. Csak megfelelő falra vagy toronyra építhető; az udvarházra nem.

UCP 3.0.7+, Crusader/Extreme 1.41 és a modul függőségei szükségesek. Tesztverzió; lásd VALIDATION.md.
