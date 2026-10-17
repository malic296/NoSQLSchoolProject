# Semestrální práce - Část 2: Elastic Stack (ELK)

Tato část projektu demonstruje nasazení a využití Elastic Stacku (Elasticsearch, Kibana, Logstash) pro zpracování a analýzu dat o letecké dopravě z roku 2015.

## Architektura
Celý stack je definován v souboru `docker-compose.yml` a spouští se v kontejnerech:
* **Elasticsearch** (1 uzel, ukládání dat a vyhledávání)
* **Kibana** (vizualizace dat a správa clusteru)
* **Logstash** (zpracování dat z CSV a odeslání do Elasticsearch)
* **Python Setup Kontejner** (jednorázový inicializační skript, který čeká na start Elasticsearch a přes REST API nastaví hesla a uživatelské role pro Kibanu a Logstash)

## Datová sada
Zvolené téma: **Letecká doprava v USA (2015)**
Data jsou rozdělena do 3 kolekcí a 6 souborů, přičemž kolekce letů obsahuje celkem 40 000 záznamů:
1. `flights` (Lety - časové řady zpoždění a letové detaily)
2. `airports` (Letiště - geolokační data a kódy letišť)
3. `airlines` (Aerolinky - názvy a kódy společností)

## Zpracování v Logstashi
Logstash parsuje CSV soubory pomocí 6 oddělených pipeline `.conf` skriptů (spravovaných přes `pipelines.yml`). Pomocí filtru `csv` se definují sloupce, `mutate` filtry slučují nebo mažou nepotřebná data (např. vytváření GPS souřadnic) a output se směruje pod speciálním uživatelem do Elasticsearch za využití Composable Index Templates (ve formátu JSON), které správně typují například polohu letišť na `geo_point` nebo data na formát `date`.

## Výstupy
* Vizualizace: Ve složce `results/` se nachází vyexportovaný pohled na dashboard `dashboard.png`.
* Dotazy: Ukázky využití vyhledávání přes REST API (včetně agregací a geoprostorového hledání) jsou uloženy v `elk/queries/queries.txt`.