# Custom Projectiles 1.6.0

Állítsd be mind a 77 egységtípus lövedékeit, sortüzének méretét és automatikus tüzelési időközét. A katapult mangonelköveket lőhet; az ostromtornyok és a közelharci egységek automatikus távolsági támadást kaphatnak.

Másold a vanilla-projectiles.yml fájlt a modul ZIP-jéből az ucp/resources/custom-projectiles/ mappába, szerkeszd a másolatot, majd válaszd ki itt. A kihagyott beállítások változatlanok; az üres útvonal nem módosít semmit. Az UCP kötelező és javasolt értékeinek szabályai az egész kiválasztott fájlra vonatkoznak. Módosítás után indítsd újra a játékot.

UCP 3.0.7+, map-extensions 1.x és Crusader/Extreme 1.41 szükséges. Mind a 33 beállítás és 77 egységnév megtalálható a vanilla-projectiles.yml és README.md fájlban. Helyi tesztváltozat; a játékon belüli ellenőrzés még hátravan.

Pontosság: az inaccuracy a játék egész koordinátaegységeit használja: 1 = 1/8 mező, 8 = 1 mező. 0 megszünteti a véletlen célzási hibát; elhagyva az eredeti pontosság marad. A spread külön hat.

Katapultok, hajítógépek, mangonelek és balliszták: az interval követi a lövés animációját, és nem rövidíti le. A sync_to_animation: false visszaállítja a független időzítőt. Frissítés után kezdj új játékot.
