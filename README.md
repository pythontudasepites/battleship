# Torpedó játék
## A Torpedó (angol nyelvterületen Battleship) a legismertebb táblás játékok egyike, amely számítógépes formában is játszható gépi ellenféllel.
## A játék használata
A program a klasszikus Torpedójáték számítógépes változata, amelyben a játékos a számítógéppel mint gépi ellenféllel mérkőzik meg. A játék a hagyományos szabályokat követi: mindkét fél egy 10×10 mezős táblán helyezi el a flottáját, majd felváltva próbálják elsüllyeszteni egymás hajóit.

### A játék indítása
A program elindítása után két játéktábla jelenik meg. A bal oldali tábla a játékos saját flottáját, a jobb oldali pedig az ellenfél rejtett hajóit reprezentálja. A játék kezdetén a program kiírja, hogy milyen méretű hajót kell éppen elhelyezni.

### Hajók elhelyezése
A hajók elhelyezése egérkattintásokkal történik a saját táblán. A program mindig jelzi, hogy a következő hajónak hány mezőből kell állnia. A hajó részeit a kívánt mezőkre kattintva lehet kijelölni. A program minden kattintás után ellenőrzi, hogy az aktuális elrendezésből még kialakítható-e szabályos hajó, ezért érvénytelen mező nem választható ki.

A program csak a szabályos elhelyezést engedi meg:

a hajók kizárólag vízszintesen vagy függőlegesen helyezhetők el;
a hajótest nem tartalmazhat megszakítást;
a hajók egymással még a sarkukon sem érintkezhetnek.
Amikor egy hajó elkészült, hangjelzés hallható, majd a program automatikusan a következő hajó elhelyezésére kér.

Miután az összes hajó felkerült a táblára, a játék automatikusan átvált csata üzemmódba.

### Csata
A játék során a jobb oldali táblán kell bal egérgombbal rákattintani arra a mezőre, amelyre lövést szeretnénk leadni.

A lövés eredménye azonnal megjelenik:

kis fekete pont: a lövés nem talált;
piros X szürke háttéren: találat érte a hajót, de az még nem süllyedt el;
fekete mező: a hajó teljes egészében elsüllyedt.
Az emberi játékos minden lövését automatikusan követi a számítógép válaszlépése, amely a saját táblán jelenik meg ugyanilyen jelölésekkel.

### A játék vége
A játék addig tart, amíg valamelyik fél összes hajója el nem süllyed. A győztesről a program üzenetet jelenít meg.

### Az ellenfél sértetlen hajóinak megjelenítése
A csata során a jobb egérgombbal a gép játékos még sértetlen hajóinak helye is megjeleníthető. Ez a funkció lehetővé teszi, hogy egy elvesztett játék után megtekintsük a még találatot nem kapott ellenséges hajók helyzetét, így könnyen visszanézhető, mely mezőket kellett volna még megtalálni a győzelemhez.

## Képernyőképek
Az alábbi képek a játék néhány fontosabb állapotát mutatják be: a hajók elhelyezését, a csata közbeni megjelenítést és a játék végét.
