from airport_wiki_scraper.routes_scraper import *
from mwparserfromhell import parse
import mwparserfromhell as mwp
from airport_wiki_scraper.airroute import AirRoute
from datetime import datetime
import dateutil.parser as dparser
import pytest

# Below examples adapted from:
# Template:Airport_destination_list
# Wikipedia:WikiProject_Aviation/Style_guide/Layout_(Airports)

# Tested using Wikipedia sandbox to ensure they are correctly rendered on Wikipedia

ORIGIN = "MyAirport"

example_a_2col = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]] (begins {{date|2026-10-1}}),<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (ends March 1, 2018),<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> (suspended)<br />'''Charter:''' [[Calvi – Sainte-Catherine Airport|Calvi]], [[Dublin Airport|Dublin]]<br/> {{em|Seasonal Charter:}} [[Grand Bahama International Airport|Freeport]]
| [[Puño Airlines]] | [[Miami International Airport|Miami]] (resumes May 12, 2023)<ref name=Puno>Ref 4</ref> <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]<ref name=Puno/>
}}"""

example_a_solutions = [
    # A regular test case
    AirRoute(origin=ORIGIN, destination="Athens International Airport", airline="Oceanic Airlines"),

    # Case with begin date and uses date template
    AirRoute(origin=ORIGIN, destination="Los Angeles International Airport", airline="Oceanic Airlines", begins=datetime(2026, 10, 1)),

    # Case with end date and uses date in plain text
    AirRoute(origin=ORIGIN, destination="Sydney Airport", airline="Oceanic Airlines", ends=datetime(2018, 3, 1)),

    # Suspended flight
    AirRoute(origin=ORIGIN, destination="Dulles International Airport", airline="Oceanic Airlines", suspended=True),

    # Charter flight
    AirRoute(origin=ORIGIN, destination="Calvi – Sainte-Catherine Airport", airline="Oceanic Airlines", charter=True),

    # Test handling of multiple charter flights grouped together
    AirRoute(origin=ORIGIN, destination="Dublin Airport", airline="Oceanic Airlines", charter=True),

    # Seasonal charter flight, uses italics formatting for seasonal charter label
    AirRoute(origin=ORIGIN, destination="Grand Bahama International Airport", airline="Oceanic Airlines", seasonal=True, charter=True),

    # Test second airline, seasonal and charter flags should be reset
    AirRoute(origin=ORIGIN, destination="Miami International Airport", airline="Puño Airlines", resumes=datetime(2023, 5, 12)),

    # Seasonal flight, uses italics formatting for seasonal label
    AirRoute(origin=ORIGIN, destination="Grand Bahama International Airport", airline="Puño Airlines", seasonal=True)
]

example_b_3col = """{{Airport destination list
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref>
}}"""

example_b_3col_end = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref>
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
}}"""

example_b_4col = """{{Airport destination list
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
|4thcoltitle=Notes|4thcolunsortable=yes
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> | |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref> |
}}"""

example_b_4col_end = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> | |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref> |
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
|4thcoltitle=Notes|4thcolunsortable=yes
}}"""

# Empty 3rd/4th column parameters are not parsed
example_b_noparam3 = """{{Airport destination list
|3rdcoltitle=|3rdcolunsortable=
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/>
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]
}}"""

example_b_noparam4 = """{{Airport destination list
|3rdcoltitle=|3rdcolunsortable=
|4thcoltitle=|4thcolunsortable=
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/>
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]
}}"""

example_b_solutions = [
    # Uses simpler test cases, to test handling of 2 and 3 columns
    AirRoute(origin=ORIGIN, destination="Athens International Airport", airline="Oceanic Airlines"),
    AirRoute(origin=ORIGIN, destination="Los Angeles International Airport", airline="Oceanic Airlines"),
    AirRoute(origin=ORIGIN, destination="Sydney Airport", airline="Oceanic Airlines"),
    AirRoute(origin=ORIGIN, destination="Dulles International Airport", airline="Oceanic Airlines"),
    AirRoute(origin=ORIGIN, destination="Miami International Airport", airline="Puño Airlines"),
    AirRoute(origin=ORIGIN, destination="Grand Bahama International Airport", airline="Puño Airlines", seasonal=True)
]

example_c_2col = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (all flights suspended until 24 October 2026)
}}"""

example_c_solutions = [
    # Tests "all suspended"
    AirRoute(origin=ORIGIN, destination="Athens International Airport", airline="Oceanic Airlines", resumes=datetime(2026, 10, 24), suspended=True),
    AirRoute(origin=ORIGIN, destination="Los Angeles International Airport", airline="Oceanic Airlines", resumes=datetime(2026, 10, 24), suspended=True),
    AirRoute(origin=ORIGIN, destination="Sydney Airport", airline="Oceanic Airlines", resumes=datetime(2026, 10, 24), suspended=True),
]

example_d_2col = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]] (suspended until October 24, 2026)
}}"""

example_d_solutions = [
    # Tests "suspended until + date"
    AirRoute(origin=ORIGIN, destination="Athens International Airport", airline="Oceanic Airlines", resumes=datetime(2026, 10, 24), suspended=True),
]

# Airline without wikilink
example_e_2col = """{{Airport destination list
| Oceanic Airlines | [[Athens International Airport|Athens]]
}}"""

# Extraneous end parameters. i.e. George Airport
example_e_2col_end = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]] |
}}"""

example_e_comment = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]], <!--[[Los Angeles Internationaal Airport|Los Angeles]]<ref name=LA>Ref 2</ref>-->
}}"""

example_e_efn_ref = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]]{{efn|Ethiopian Airlines flights make an intermediate stop in Hong Kong en route to the listed destination. However, the airline has no [[Freedoms of the air|fifth freedom rights]] to carry passengers solely between Manila and Hong Kong.<ref>{{OAGWorldMay2025Ref|title=Addis Ababa, Ethiopia ADD|pages=17-19}}</ref>}}
}}"""

# Airline without wikilink and with nowrap, i.e. Juneau International Airport
example_e_nowrap_txt = """{{Airport destination list
| {{nowrap|Oceanic Airlines}} | [[Athens International Airport|Athens]]
}}"""

# Airline with nowrap
example_e_nowrap_link = """{{Airport destination list
| {{nowrap|[[Oceanic Airlines]]}} | [[Athens International Airport|Athens]]
}}"""

# Airline with operator
example_e_operator = """{{Airport destination list
| [[Oceanic Airlines]] operated by [[Another Airline]] | [[Athens International Airport|Athens]]
}}"""

example_e_op_for = """{{Airport destination list
| [[Oceanic Airlines]] for [[Another Airline]] | [[Athens International Airport|Athens]]
}}"""

# Some valid 3-col and 4-col APDLs lack ending 3rd/4th columns, leading to failure to parse final
# rows due to identified misalignment, i.e. Kelleys Island Land Field 
example_e_3col_empty = """{{Airport destination list
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
|[[Oceanic Airlines]] | [[Athens International Airport|Athens]]
}}"""


example_e_solutions = [
    AirRoute(origin=ORIGIN, destination="Athens International Airport", airline="Oceanic Airlines"),
]

# Right column parameter split across two lines -- MW parses correctly but not mwparserfromhell
# i.e. Gdańsk Lech Wałęsa Airport
example_f = """{{airport-dest-list
|[[Ryanair]] | [[Budapest Ferenc Liszt International Airport
|Budapest]] }}
"""

example_f_solutions = [
    AirRoute(origin=ORIGIN, destination="Budapest Ferenc Liszt International Airport", airline="Ryanair")
]

# Airports that lack wikilinks, i.e. Rubondo Airstrip
example_g = """{{airport-dest-list
| {{nowrap|[[Coastal Aviation]]}} | Grumeti, Kogatende, [[Lake Manyara Airport|Manyara]]}}"""

example_g_solutions = [
    AirRoute(origin=ORIGIN, destination="Grumeti", airline="Coastal Aviation"),
    AirRoute(origin=ORIGIN, destination="Kogatende", airline="Coastal Aviation"),
    AirRoute(origin=ORIGIN, destination="Lake Manyara Airport", airline="Coastal Aviation")
]

# Airports with labels like "Charter" and "Seasonal" but for other purposes.
example_h = """{{Airport destination list
|[[Eagle Air Services]]|'''Cropdusting:''' [[Saramacca District|Saramacca]]}}"""

example_h_solutions = [
    AirRoute(origin=ORIGIN, destination="Saramacca District", airline="Eagle Air Services")
]

# Template name variations, i.e. Jumla Airport
example_i_whitespace = """{{ airport-dest-list
| [[Nepal Airlines]] | [[Nepalgunj Airport|Nepalgunj]]}}"""

example_i_underscore = """{{Airport_destination_list
| [[Nepal Airlines]] | [[Nepalgunj Airport|Nepalgunj]]}}"""

example_i_solutions = [
    AirRoute(origin=ORIGIN, destination="Nepalgunj Airport", airline="Nepal Airlines")
]

example_page = """{{Infobox airport}}
=Airlines and Destinations=
==Passenger==
{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]] (begins {{date|2026-10-1}}),<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (ends March 1, 2018),<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> (suspended)<br />'''Charter:''' [[Calvi – Sainte-Catherine Airport|Calvi]], [[Dublin Airport|Dublin]]<br/> {{em|Seasonal Charter:}} [[Grand Bahama International Airport|Freeport]]
| [[Puño Airlines]] | [[Miami International Airport|Miami]]<ref name=Puno>Ref 4</ref> <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]<ref name=Puno/>
}}
==Cargo==
{{Airport-dest-list
| [[Oceanic Airlines Cargo]] | [[Athens International Airport|Athens]]
}}"""


example_page_cargo = """{{Infobox airport}}
=Airlines and Destinations=
==Cargo==
{{Airport-dest-list
| [[Oceanic Airlines Cargo]] | [[Athens International Airport|Athens]]
}}"""

# Test APDLs under bolded headings

example_page_bold = """{{Infobox airport}}
=Airlines and Destinations=
==Passenger==
{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]] (begins {{date|2026-10-1}}),<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (ends March 1, 2018),<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> (suspended)<br />'''Charter:''' [[Calvi – Sainte-Catherine Airport|Calvi]], [[Dublin Airport|Dublin]]<br/> {{em|Seasonal Charter:}} [[Grand Bahama International Airport|Freeport]]
| [[Puño Airlines]] | [[Miami International Airport|Miami]]<ref name=Puno>Ref 4</ref> <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]<ref name=Puno/>
}}
==Cargo==
{{Airport-dest-list
| [[Oceanic Airlines Cargo]] | [[Athens International Airport|Athens]]
}}"""

example_page_cargo_bold = """{{Infobox airport}}
'''Cargo'''
{{Airport-dest-list
| [[Oceanic Airlines Cargo]] | [[Athens International Airport|Athens]]
}}"""

example_page_pass_bold = """{{Infobox airport}}
'''Passenger'''
{{Airport-dest-list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]]
}}"""


example_page_pass = """{{Infobox airport}}
=Airlines and Destinations=
{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]] (begins {{date|2026-10-1}}),<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (ends March 1, 2018),<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> (suspended)<br />'''Charter:''' [[Calvi – Sainte-Catherine Airport|Calvi]], [[Dublin Airport|Dublin]]<br/> {{em|Seasonal Charter:}} [[Grand Bahama International Airport|Freeport]]
| [[Puño Airlines]] | [[Miami International Airport|Miami]]<ref name=Puno>Ref 4</ref> <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]<ref name=Puno/>
}}"""


example_page_cargo_2 = """==Airlines and destinations==
===Cargo===
{{Airport destination list
<!-- -->
| [[Ameriflight]]|'''Seasonal:''' [[Hollywood Burbank Airport|Burbank]]
}}
"""

# Clearly a mistake, but should still handle just in case. e.g. Inyokern Airport
# Expect to only retrieve one cargo list.
example_page_cargo_3 = """
=Airlines and Destinations=
==Cargo==
{{Airport-dest-list
| [[Oceanic Airlines Cargo]] | [[Athens International Airport|Athens]]
}}
=Airlines and Destinations=
==Cargo==
{{Airport-dest-list
| [[Oceanic Airlines Cargo]] | [[Athens International Airport|Athens]]
}}"""

# To be used for tests of misaligned ref tags
example_dsm = """{{Airport destination list
<!-- -->
| [[Allegiant Air]] | [[Austin–Bergstrom International Airport|Austin]],<ref name="AustinAllegiant">{{cite news |last1=Smith |first1=Eve Chen and Brian |title=Allegiant and Sun Country are merging. What it means for Iowa fliers |url=https://www.desmoinesregister.com/story/travel/2026/01/12/allegiant-sun-country-merger-des-moines-flights/88144550007/?gnt-cfr=1&gca-cat=p&gca-uir=true&gca-epti=z111250p000950c000950e111250v003334d--50--b--50--&gca-ft=150&gca-ds=sophi |access-date=31 March 2026 |work=The Des Moines Register |date=12 January 2026}}</ref> [[Logan International Airport|Boston]],<ref name="AustinAllegiant"/> [[Hollywood Burbank Airport|Burbank]],<ref name="AustinAllegiant"/> [[Fort Lauderdale–Hollywood International Airport|Fort Lauderdale]],<ref name="AustinAllegiant"/> [[Southwest Florida International Airport|Fort Myers]],<ref>{{cite web|url=https://www.palmbeachpost.com/story/news/2025/07/29/allegiant-airlines-florida-flights-fort-myers-rsw/85418997007/|archive-url=https://web.archive.org/web/20250729132050/https://www.palmbeachpost.com/story/news/2025/07/29/allegiant-airlines-florida-flights-fort-myers-rsw/85418997007/|url-status=dead|archive-date=July 29, 2025|title=Allegiant airlines adds 6 new Florida routes, some starting at $49. Where, when|website=The Palm Beach Post|date=July 29, 2025|access-date=July 29, 2025}}</ref> [[Jack Edwards Airport|Gulf Shores]],<ref>{{cite web|date=May 21, 2025 |url=https://www.streetinsider.com/dr/news.php?id=24830342&gfv=1 |title=Allegiant Announces Five New Routes with One-Way Fares as Low as $39*|website=Street Insider}}</ref> [[William P. Hobby Airport|Houston-Hobby]],<ref>{{cite news |last1=Miranda |first1=Janet |title=Allegiant launches flights from Houston's Hobby Airport to another Gulf Coast destination |url=https://www.bizjournals.com/houston/news/2025/05/23/allegiant-hobby-airport-gulf-shores-flights-begin.html |access-date=31 March 2026 |work=Houston Business Journal |date=23 May 2025}}</ref> [[Jacksonville International Airport|Jacksonville (FL)]],<ref name=ALLE>{{Cite web|url=https://www.msn.com/en-us/news/us/allegiant-offering-nonstop-flights-from-jax-to-akron-canton-de-moines-grand-rapids/ar-AA1umT2j|title=Allegiant offering nonstop flights from JAX to Akron-Canton, De Moines, Grand Rapids|website=[[MSN]] |date=November 2024}}</ref> [[Harry Reid International Airport|Las Vegas]],<ref name="AustinAllegiant"/> [[John Wayne Airport|Orange County]],<ref name="AustinAllegiant"/> [[Orlando Sanford International Airport|Orlando/Sanford]],<ref name="AustinAllegiant"/> [[Philadelphia International Airport|Philadelphia]],<ref name="Allegiant2026"/<ref>{{cite news |title=Allegiant Adds 30 New Nonstop Routes, Entering Four New Markets |url=https://fox40.com/business/press-releases/cision/20251118LA27048/allegiant-adds-30-new-nonstop-routes-entering-four-new-markets/ |access-date=18 November 2025 |agency=FOX 40 |date=18 November 2025 |language=en |archive-date=January 7, 2026 |archive-url=https://web.archive.org/web/20260107091511/https://fox40.com/business/press-releases/cision/20251118LA27048/allegiant-adds-30-new-nonstop-routes-entering-four-new-markets/ |url-status=dead }}</ref> [[Mesa Gateway Airport|Phoenix/Mesa]],<ref name="AustinAllegiant"/>  [[Punta Gorda Airport (Florida)|Punta Gorda (FL)]],<ref name="AustinAllegiant"/> [[St. Pete–Clearwater International Airport|St. Petersburg/Clearwater]]<ref>{{cite news |last1=Beeman |first1=Perry |title=Allegiant's DSM base opens Thursday, four nonstop flights added • Iowa Capital Dispatch |url=https://iowacapitaldispatch.com/2021/06/30/allegiants-dsm-base-opens-thursday-four-nonstop-flights-added/ |access-date=31 March 2026 |work=Iowa Capital Dispatch |date=30 June 2021}}</ref><br />'''Seasonal:''' [[Destin–Fort Walton Beach Airport|Destin/Fort Walton Beach]],<ref name="AustinAllegiant"/> [[Nashville International Airport|Nashville]],<ref name="NashvilleAllegiant">{{cite news |last1=Reyna-Rodriguez |first1=Victoria |title=Four new direct flights from Des Moines airport start soon. See the new routes. |url=https://www.desmoinesregister.com/story/travel/2025/05/05/des-moines-international-airport-new-direct-routes-starting-2025/83410112007/?gnt-cfr=1&gca-cat=p&gca-uir=true&gca-epti=z114550p000050c000050e114550v002534d--41--b--41--&gca-ft=196&gca-ds=sophi |access-date=31 March 2026 |work=The Des Moines Register |date=5 May 2025}}</ref> [[Newark Liberty International Airport|Newark]],<ref name="NashvilleAllegiant"/> [[Portland International Airport|Portland (OR)]],<ref name="NashvilleAllegiant"/> [[Sarasota–Bradenton International Airport|Sarasota]]<ref name="AustinAllegiant"/> 
<!-- -->
| [[American Airlines]] | [[Charlotte Douglas International Airport|Charlotte]],<ref name="CLTAA">{{cite news |last1=Block |first1=Francesca |title=American Airlines flight from Des Moines to Charlotte canceled after engine fire |url=https://www.desmoinesregister.com/story/news/2023/06/23/mechanical-issue-grounds-plane-at-des-moines-airport-friday/70352154007/?gnt-cfr=1&gca-cat=p&gca-uir=true&gca-epti=z116534e005650v116534d--72--b--72--&gca-ft=156&gca-ds=sophi |access-date=31 March 2026 |work=The Des Moines Register |date=23 June 2023}}</ref> [[Dallas Fort Worth International Airport|Dallas/Fort Worth]], [[Phoenix Sky Harbor International Airport|Phoenix–Sky Harbor]]<ref name="DCADESAA"/><br/>'''Seasonal:''' [[O'Hare International Airport|Chicago–O'Hare]]<ref name="ChicagoAmerican"/> 
<!-- -->
| [[American Eagle (airline brand)|American Eagle]] | [[O'Hare International Airport|Chicago–O'Hare]],<ref name="ChicagoAmerican">{{cite news |title=American Airlines adds more flights from Des Moines to Chicago |url=https://www.kcci.com/article/des-moines-flights-to-chicago-ohare-airport-american-airlines/69887597 |access-date=31 March 2026 |work=KCCI |date=31 December 2025 |language=en}}</ref> [[Dallas Fort Worth International Airport|Dallas/Fort Worth]],<ref name="DCADESAA"/> [[Los Angeles International Airport|Los Angeles]],<ref>{{cite web|title=American Airlines Adds 8 New Routes For Winter 2025-26|website=Aviation A2Z|url=https://aviationa2z.com/index.php/2025/03/26/american-airlines-adds-8-new-routes-for-winter-2025-26/|date=March 26, 2025|access-date=March 26, 2025}}</ref> [[LaGuardia Airport|New York–LaGuardia]],<ref name="DCADESAA"/> [[Phoenix Sky Harbor International Airport|Phoenix–Sky Harbor]],<ref name="DCADESAA"/> [[Ronald Reagan Washington National Airport|Washington–National]]<ref name="DCADESAA">{{cite news |last1=Geer |first1=Caleb |title=American Airlines announces new nonstop flight from Des Moines to Los Angeles |url=https://www.weareiowa.com/article/travel/american-airlines-nonstop-direct-flight-des-moines-los-angeles-dsm-lax-tickets-price/524-777eb289-c52a-491d-a571-9881ace2ef4e |access-date=31 March 2026 |date=26 March 2025}}</ref><br />'''Seasonal:''' [[Charlotte Douglas International Airport|Charlotte]],<ref name="CLTAA"/> [[Miami International Airport|Miami]],<ref name="CLTAA"/> [[Philadelphia International Airport|Philadelphia]]<ref name="CLTAA"/> 
<!-- -->
| [[Delta Air Lines]] | [[Hartsfield–Jackson Atlanta International Airport|Atlanta]]<ref name="ATLDelta">{{cite news |last1=Kealey |first1=Kate |title=Are flights being canceled? What to know about reduced flights at the Des Moines airport. |url=https://www.desmoinesregister.com/story/travel/2025/11/06/dsm-airport-flight-cancellations-today-faa/87125937007/?gnt-cfr=1&gca-cat=p&gca-uir=true&gca-epti=z113634p000350c000350e006850v113634d--58--b--58--&gca-ft=261&gca-ds=sophi |access-date=31 March 2026 |work=The Des Moines Register |date=6 November 2025}}</ref> 
<!-- -->
| {{nowrap|[[Delta Connection]]}} | [[Detroit Metropolitan Airport|Detroit]],<ref>{{cite news |last1=Derby |first1=Kevin |title=Delta Flight With 56 Passengers Slid Off the Runway at Des Moines |url=https://aviationa2z.com/index.php/2025/12/01/delta-flight-slid-off-the-runway-at-des-moines/ |access-date=31 March 2026 |work=Aviation A2Z |date=1 December 2025}}</ref> [[Minneapolis–Saint Paul International Airport|Minneapolis/St. Paul]],<ref name="ATLDelta"/> [[LaGuardia Airport|New York–LaGuardia]]<ref>{{cite news |title=American Airlines to add daily nonstop flight to New York from Des Moines in June |url=https://www.desmoinesregister.com/story/money/business/2023/01/31/american-airlines-adding-nonstop-flight-nyc-new-york-city-des-moines/69858571007/?gnt-cfr=1&gca-cat=p&gca-uir=true&gca-epti=z114934e110650v114934d--54--b--54--&gca-ft=142&gca-ds=sophi |access-date=31 March 2026 |work=The Des Moines Register |date=31 January 2023}}</ref> 
<!-- -->
| [[Frontier Airlines]] | [[Denver International Airport|Denver]]<ref>{{cite news |last1=Norvell |first1=Dawn Gilbertson and Kim |title=Frontier-Spirit airlines merger could bring Des Moines travelers some new options |url=https://www.desmoinesregister.com/story/news/2022/02/07/budget-airlines-frontier-spirit-merger-des-moines-airport-impact/6693619001/?gnt-cfr=1&gca-cat=p&gca-uir=true&gca-epti=z118234e008950v118234d--91--b--91--&gca-ft=151&gca-ds=sophi |access-date=31 March 2026 |work=The Des Moines Register |date=7 February 2022}}</ref><br />'''Seasonal:''' [[Orlando International Airport|Orlando]],<ref>{{cite news |last1=Burks |first1=Robin |title=Orlando Airport Adds 5 NEW Nonstop Flights This Month |url=https://allears.net/2026/03/29/orlando-airport-adds-5-new-nonstop-flights-this-month-4/ |access-date=31 March 2026 |date=29 March 2026}}</ref> [[Phoenix Sky Harbor International Airport|Phoenix–Sky Harbor]]<ref>{{cite web|title=Frontier Adds 23 New Routes|url=https://airlinegeeks.com/2025/12/04/frontier-adds-23-new-routes/|website=airlinegeeks.com|date=December 4, 2025|access-date=December 7, 2025}}</ref> 
<!-- -->
| {{nowrap|[[Southwest Airlines]]}} | [[Midway International Airport|Chicago–Midway]],<ref>https://airlinegeeks.com/2025/08/15/southwest-exits-11-routes-in-network-reshuffle/</ref> [[Denver International Airport|Denver]],<ref name="SWADenver">{{cite news |last1=Smith |first1=Brian |title=Southwest Airlines is changing its routes from Des Moines in 2026. See what's new. |url=https://www.desmoinesregister.com/story/travel/2025/08/18/southwest-des-moines-airport-routes-st-louis-chicago-midway-changing/85681622007/?gnt-cfr=1&gca-cat=p&gca-uir=true&gca-epti=z114334p000550c000550e005850v114334d--68--b--68--&gca-ft=138&gca-ds=sophi |access-date=31 March 2026 |work=The Des Moines Register |date=18 August 2025}}</ref> [[Harry Reid International Airport|Las Vegas]]<ref name="SWADenver"/> [[Nashville International Airport|Nashville]] (begins March 11, 2027)<ref>{{cite web |last1=Cheng |first1=Lucia |title=New terminal helps Des Moines add new Southwest route for 2027 |url=https://www.desmoinesregister.com/story/travel/2026/07/16/flights-des-moines-airport-southwest-nashville-nonstop-flight/90943772007/ |access-date=25 September 2026}}</ref><br /> '''Seasonal:''' [[Phoenix Sky Harbor International Airport|Phoenix–Sky Harbor]]<ref name="SWADenver"/>  
<!-- -->
| [[United Airlines]] | [[O'Hare International Airport|Chicago–O'Hare]],<ref name="ORDUnited">{{cite news |last1=Derby |first1=Kevin |title=Two United Airlines Attendants Brawl Delays Flight by 4 Hours |url=https://aviationa2z.com/index.php/2025/10/29/united-airlines-attendants-brawl-delays-flight-by-4-hours/ |access-date=31 March 2026 |work=Aviation A2Z |date=29 October 2025}}</ref> [[Denver International Airport|Denver]],<ref name="DenverUnitedAirlines">{{cite news |title=Des Moines airport remains closed after plane slides off runway |url=https://www.kcrg.com/2025/11/30/des-moines-airport-remains-closed-after-plane-slides-off-runway/ |access-date=31 March 2026 |work=KCRG |date=30 November 2025 |language=en}}</ref> [[George Bush Intercontinental Airport|Houston–Intercontinental]]{{cn|date=November 2024}}
<!-- -->
| [[United Express]] | [[O'Hare International Airport|Chicago–O'Hare]],<ref name="ORDUnited"/> [[Denver International Airport|Denver]],<ref name="DenverUnitedAirlines"/> [[George Bush Intercontinental Airport|Houston–Intercontinental]] {{citation needed|date=March 2026}} 
}}
"""

@pytest.mark.parametrize("input, has_passenger, has_cargo, pass_params, cargo_params", [
    (example_page,            True, True, 4, 2),
    (example_page_cargo,      False, True, 0, 2),
    (example_page_bold,       True, True, 4, 2),
    (example_page_pass,       True, False, 4, 0),
    (example_page_pass_bold,  True, False, 2, 0),
    (example_page_cargo_bold, False, True, 0, 2),
    (example_page_cargo_2,    False, True, 0, 2),
    (example_page_cargo_3,    False, True, 0, 2)
])
def test_get_apdl(input, has_passenger, has_cargo, pass_params, cargo_params):
    parsed = parse(input)
    p, c = get_apdl(parsed)
    if has_passenger:
        assert type(p) == mwp.nodes.Template
        assert "Airport destination list" in p.name or "Airport-dest-list" in p.name
        assert len(p.params) == pass_params
    else:
        assert p == None
    if has_cargo:
        assert type(c) == mwp.nodes.Template
        assert "Airport destination list" in c.name or "Airport-dest-list" in c.name
        assert len(c.params) == cargo_params
    else:
        assert c == None


@pytest.mark.parametrize("input, expected, name", [
    (example_a_2col,         example_a_solutions, "2 columns with multiple cases"),
    (example_b_3col,         example_b_solutions, "3 columns"),
    (example_b_3col_end,     example_b_solutions, "3 columns with named params at end"),
    (example_b_4col,         example_b_solutions, "4 columns"),
    (example_b_4col_end,     example_b_solutions, "4 columns with named params at end"),
    (example_b_noparam3,     example_b_solutions, "Ignore empty 3rd col parameters"),
    (example_b_noparam4,     example_b_solutions, "Ignore empty 4th col parameters"),
    (example_c_2col,         example_c_solutions, "test 'all suspended'"),
    (example_d_2col,         example_d_solutions, "test 'suspended until'"),
    (example_e_2col,         example_e_solutions, "airline not wikilink"),
    (example_e_2col_end,     example_e_solutions, "extraneous empty parameters at end"),
    (example_e_comment,      example_e_solutions, "comments should be ignored"),
    (example_e_efn_ref,      example_e_solutions, "footnotes and references should be ignored"),
    (example_e_nowrap_txt,   example_e_solutions, "handles airline nowrap without wikilink"),
    (example_e_nowrap_link,  example_e_solutions, "handles airline nowrap with wikilink"),
    (example_e_operator,     example_e_solutions, "handles non-compliant airline with operators"),
    (example_e_op_for,       example_e_solutions, "handles non-compliant airline cols with 'for'"),
    (example_e_3col_empty,   example_e_solutions, "handles empty last columns"),
    (example_f,              example_f_solutions, "parameter across line break quirk"),
    (example_g,              example_g_solutions, "airports without wikilinks"),
    (example_h,              example_h_solutions, "other colon labels are ignored"),
    (example_i_whitespace,   example_i_solutions, "template name with whitespace"),
    (example_i_underscore,   example_i_solutions, "template name with underscore replacing space"),
])
def test_extract_apdl(input, expected, name):
    parsed = parse(input)
    passenger, _ = get_apdl(parsed)
    assert passenger != None
    results = extract_apdl(passenger, ORIGIN)
    assert len(results) == len(expected), f"{name}: same number of results"
    assert results == expected, f"{name}: contents equal"


@pytest.mark.parametrize("input, exp_processed, exp_date", [
    ("(begins October 1, 2025)", "October 1, 2025", datetime(2025, 10, 1)),
    ("(begins 1 October 2025)", "1 October 2025", datetime(2025, 10, 1)),
    ("(begins 2025 October 1)", "2025 October 1", datetime(2025, 10, 1)),
    ("(   begins 2025 October 1  )", "2025 October 1", datetime(2025, 10, 1)),
    ("begins March 15, 2019", "March 15, 2019", datetime(2019, 3, 15)),
    ("(begins March 15, 2019)", "March 15, 2019", datetime(2019, 3, 15)),
    ("(ends April 5, 2028)", "April 5, 2028", datetime(2028, 4, 5)),
    ("(resumes June 29, 2028)", "June 29, 2028", datetime(2028, 6, 29)),
    ("(beginning March 15, 2019)", "March 15, 2019", datetime(2019, 3, 15)),
    ("(ending April 5, 2028)", "April 5, 2028", datetime(2028, 4, 5)),
    ("(resuming June 29, 2028)", "June 29, 2028", datetime(2028, 6, 29)),
    ("(all flights suspended until 24 October 2026)", "24 October 2026", datetime(2026, 10, 24)),
    ("(suspended until 24 October 2026)", "24 October 2026", datetime(2026, 10, 24)),
])
def test_process_date_str(input, exp_processed, exp_date):
    processed = process_date_str(input)
    assert processed == exp_processed, f"'{input}' correctly processed"
    date = dparser.parse(processed, fuzzy=True)
    assert date == exp_date, f"date correctly parsed from '{processed}'"