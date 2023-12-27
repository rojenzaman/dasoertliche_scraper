# dasoertliche.de scraper

Simple scraper to fetch some listings from a given topic on dasoertliche.de


## Why?

Actually the main reason which motivated me, was to get local landlords from a specific city. I wanted to get in touch with them to apply for any flat near by. Well, I can tell you that it worked out pretty well. Probably someone will find this helpful as well. At the moment the data is stored locally in a json file in the data directory which is ignored by git.


### setup

```sh
git clone https://github.com/p3t3r67x0/dasoertliche_scraper.git
cd dasoertliche_scraper
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```


### how to use

Before running the script activate the virtual environment. You can query for anything which might interest you.


```sh
pyhhon crawler.py --query Hausverwaltung --offset 5 --postal-code 10963
```

If you do not wish to get results with an offset

```sh
pyhhon crawler.py --query Hausverwaltung --postal-code 10963
```

If you do not wish to get any results from a specific postal code you might not use the `--postal-code` option.

```sh
pyhhon crawler.py --query Hausverwaltung
```


### logging

Well there is not any neat logging, instead some simple process output

```
Next url https://www.dasoertliche.de/?kw=Ferienwohnung&ci=&form_name=search_nat&recFrom=5

Detail url https://www.dasoertliche.de/Themen/Astra-Hotel-Kaiserslautern-Inh-Ingeborg-Weismantel-Kaiserslautern-Innenstadt-Rudolf-Breitscheid-Str
Detail url https://www.dasoertliche.de/Themen/Atalay-Ferienwohnung-Bad-Reichenhall-Karlstein-Am-Schroffen
Detail url https://www.dasoertliche.de/Themen/Athena-Ferienwohnung-Pirna-Weinleite
Detail url https://www.dasoertliche.de/Themen/ATLAS-REISEBÜRO-GmbH-Kempten-Allgäu-Ursulasried-Ursulasrieder-Str
Detail url https://www.dasoertliche.de/Themen/Atlas-Touring-Potsdam-Nördliche-Innenstadt-Lindenstr
Detail url https://www.dasoertliche.de/Themen/Atoos-Kleinanzeigen-Marktplatz-München-Riem-Astrid-Lindgren-Str
Detail url https://www.dasoertliche.de/Themen/atraveo-GmbH-Ferienwohnungsvermietung-Düsseldorf
Detail url https://www.dasoertliche.de/Themen/Attila-Teoman-Ferienwohnungen-Düsseldorf-Pempelfort-Moltkestr
Detail url https://www.dasoertliche.de/Themen/Auer-Heinrich-Gästehaus-Flora-Reit-im-Winkl-Dorfstr
Detail url https://www.dasoertliche.de/Themen/Auer-Wohnungsbaugesellschaft-mbH-Aue-Aue-Poststr
Detail url https://www.dasoertliche.de/Themen/Auerbach-Heinrich-Ferienwohnungen-u-Monika-Ferienwohnungen-Bayerisch-Gmain-Berchtesgadener-Str
Detail url https://www.dasoertliche.de/Themen/August-Dieter-August-Carola-Ferienwohnungsvermietung-Elend-Heinrich-Heine-Weg
Detail url https://www.dasoertliche.de/Themen/Augustins-Ferienwohnung-Würzburg-Heidingsfeld-Rübezahlweg
Detail url https://www.dasoertliche.de/Themen/Aumannwirt-Landgasthof-Bad-Feilnbach-Altofing-Mühlweg
Detail url https://www.dasoertliche.de/Themen/AURA-HOTEL-Ostseeperlen-Ostseebad-Boltenhagen-Strandpromenade
Detail url https://www.dasoertliche.de/Themen/Auras-Micaela-Ferienwohnungen-Bad-Saarow-Pieskow-Fürstenwalder-Chaussee
Detail url https://www.dasoertliche.de/Themen/Aurich-Ferienwohnung-Oelsnitz-Erzgeb-Am-Förstersteig
Detail url https://www.dasoertliche.de/Themen/Ausflugslokal-Hovestadt-Inh-Dieter-Hovestadt-Gastlichkeit-Tradition-Heek-Ahle
Detail url https://www.dasoertliche.de/Themen/Autenrieth-Ludwig-Ferienwohnungen-und-Zimmervermietung-Starnberg-Kirchplatz
Detail url https://www.dasoertliche.de/Themen/Autenrieth-Ludwig-Ferienwohnungen-und-Zimmervermietung-Weßling-Hochstadt-Dorfstr
Detail url https://www.dasoertliche.de/Themen/Autenrieth-Sieglinde
Detail url https://www.dasoertliche.de/Themen/Auto-Bike-Kuhn-S-Bad-Kissingen-Rosenstr
Detail url https://www.dasoertliche.de/Themen/Auto-Mischner-Bad-Schandau-Prossen-Gründelweg
Detail url https://www.dasoertliche.de/Themen/Autohof-und-Ferienwohnung-Eisermann-Inhaber-Andreas-und-Kerstin-Eisermann-Gersdorf-Lindenhofweg
Detail url https://www.dasoertliche.de/Themen/Aymanns-Heike-Ferienwohnung-Vossberghof-Kranenburg-Nütterden-Schmelendriß
```

### issues

Happy to hear from you. Open a issue or just blame me


### todo

- improve methods command line options
- implement further storage options
- implement an export to your contact book
