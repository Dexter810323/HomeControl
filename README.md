Ebbe a repoba kerül fel az átdolgozott lakásvezérlésem

fizikai eszközök amiket írni vagy olvasni tud a program:
- DS18B20 hőszenzor jelenleg 4db
- TUYA eszközök
  - fogyasztásmérők
  - hőszivattyú
  - pára és hőmérséklet mérő eszköz
  - szoba termosztát
- modbus szenzorok
  - lifepo akkumlátorra kötött shunt (300A) 2db (ezen keresztül tudom kiolvasni a napelemem 2 stringjének teljesítményét)
  - 220v fogyasztásmérő
- axpert klón 3000VA inverter (jelenleg ICC pi szoftverrel olvasva)

amit kiolvas még a program:
- openweathermap on keresztül api hívással kapott időjárás értékeket, és előrejelzést ami segíti a lakás fogyasztásának beállítását
- solcast apin keresztül kapott előrejelzés értékeket, ami szintén segíti a programot az energia irányításban

amiről szól a program:
a kapott adatok függvényében és a paraméterek alapján igazítja a lakás energia irányítását.
figyel az inverter maximumának nem túllépésére (egyszerre indított eszközöket lekapcsolja ha kell)
az előrejelzések és paraméterek alapján takarékoskodik az akkumlátor kapacitással, így a fizetős árammal is
optimális esetben napsütéses időben próbálja elindítani a leg több fogyasztót az ingyen energia legjobb kihasználására
ebbe bele tartozik a gázfűtés elsőbbségének korlátozása ha van nap, és ,egfelelőek a körülmények a hőszivattyús fűtésre

kicsi a rendszer, sok sok fogyasztóval. 
3.2 kWp napelem
3KVA inverter
16A MVM fizetős nappali áram
16A MVM fizetős éjszakai áram
6 kWh Lifepo4 akkumlátor

1 sütő (2.5kW)
1 hűtő (0.5kW)
1 mosógép (2.2kW)
1 mosogatógép (2.2kW)
1 hőszivattyú (9.5kW) (10-04 hóig lakást fűt, 05-09 hóig medencét)
1 split klíma (3.5kW) (még nincs beüzemelve, de nyáron fog hűteni)
1 puffer fűtőszál (3kW)
spotlámpák, routerek, számítógépek, tvk, nas, gázkazán

kommunikációja a programnak:
mqtt adatokkal kommunikál a homeassistant szerverem felé, ami naplózza az adatokat, de nem avatkozik be semmibe
mqtt adatokkal komminukál a konyhában lévő ESP32 touch eszközzel, ami megjeleníti a napgörbét, a lakás aktuális energetikáját, és
képes beavatkozni az eszközök ki be kapcsolásába az érintőképernyőn keresztül
mqtt adatokkal kommunikál a raspbarry pi eszközzel amin fut az icc pi alkalmazás, így ami képes az inverter paramétereit megváltoztatni menet közbe
így képes a lakást átkapcsolni napelemről fizetős hálózatra, vagy finomhangolhatja az akkuk töltését amperben

a beállítás file szabadon írható, paraméterezhető, a program azonnal végrehajtja a módosításokat

nincs verzió, jelenleg 3 program kód látja el ezeket a feladatokat, 2 éve íródtak, ebbe a repoba az a verzió kerül amit átdolgozok, frissítek, és a közel végleges formába hozom.
a repo tartalma szabadidőm függvényében folyamatosan változni fog.

a szoftver mögött elég bonyolult rendszer van, mind fűtés oldalon, mind elektromos oldalon.

a program éves szinten 3.2MWh áramot irányít, és 4 ember életét könnyíti meg, 
135nm-en alapvetően gáz fűtéssel, ahol évente 350m3 gázfelhasználást spórol meg az 1100m3 ből egy 40+ éves lakásban,
állandó 24,5 fokon bent, valamint tavasztól őszig 7m3 medencét tart 32-33 fokon kint.
