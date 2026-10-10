# Dokumentace - Část 1: NoSQL technologie (Apache Cassandra)

## Úvod
Tato část semestrální práce ukazuje nasazení a praktické využití distribuované NoSQL databáze Apache Cassandra (verze 5.0) nad reálnými daty z brazilské e-commerce platformy Olist. Čtenář se seznámí s architekturou wide-column storu, modelováním dat (Query-First přístup), správou clusteru, využitím sekundárních indexů (SAI) a analýzou časových řad objednávek. Z důvodu lokálního rozsahu projektu nejsou do architektury zahrnuta vícečetná datová centra, šifrování komunikace mezi uzly (TLS) ani dedikované monitorovací nástroje. 

Pro nasazení je využit oficiální obraz `cassandra:5.0`, který garantuje stabilitu a podporu nejnovějších funkcí (např. vylepšené SAI indexy). Pro inicializační kontejner je využit lehký obraz `python:3.11-slim`.

## Architektura
**Schématický popis:**
Řešení je postaveno na jednom clusteru (`SchoolCluster`) umístěném v jednom datovém centru (`dc1`) s jedním rackem (`rack1`). Skládá se ze 3 rovnocenných databázových uzlů (masterless architektura) a jednoho efemérního inicializačního kontejneru napsaného v Pythonu, který se po vložení dat ukončí.
*(Pozn.: Zde vložte vyexportovaný obrázek architektury z draw.io, např. `![Architektura](architektura.png)`).*

*   **Cluster a Uzly:** Nasazen je 1 cluster obsahující přesně 3 uzly. To je minimální počet pro demonstraci distribuované konsenze a výpadků při RF=3.
*   **Sharding (Partitioning):** Sharding je v Cassandře řešen nativně pomocí virtuálních tokenů (vnodes). Data jsou distribuována mezi 3 uzly pomocí hashovací funkce Murmur3 nad definovaným Partition Key (např. `order_id` nebo `category_name`).
*   **Replikace:** Celý Keyspace je konfigurován s replikačním faktorem 3 (`SimpleStrategy`). Každý záznam existuje ve 3 fyzických kopiích. To garantuje dostupnost i při výpadku dvou uzlů (při čtení s konzistencí ONE).
*   **Perzistence dat:** Data jsou ukládána v primární paměti do MemTable a asynchronně flushována na disk do neměnných souborů SSTable. Ztrátě dat před flushem brání Commit Log. Volumes v Docker Compose zajišťují zachování datových souborů i po restartu kontejnerů.
*   **Distribuce dat pro čtení/zápis:** Zápis či čtení může přijmout jakýkoliv uzel (koordinátor), který podle tokenu přesně ví, které uzly data fyzicky drží, a požadavek tam směruje (scatter-gather).
*   **Zabezpečení:** Autentizace je vynucena aktivací `PasswordAuthenticator` a `CassandraAuthorizer` v souboru `cassandra.yaml`. Komunikace probíhá pod vyhrazeným aplikačním uživatelem definovaným v souboru `.env`. 

## Případ užití
Vybraná databáze slouží jako analytické a provozní úložiště pro platformu elektronického obchodu. Cassandra byla vybrána pro svou excelentní propustnost při zápisu (vysoký objem transakcí, logy objednávek, nákupní košíky) a schopnost pracovat s obrovskými časovými řadami. Tradiční relační databáze by při tomto objemu (stovky tisíc událostí) začala trpět na zamykání tabulek při zápisu. Redis neposkytuje dostatečnou flexibilitu pro perzistentní komplexní modely nad diskovým úložištěm a MongoDB má vyšší režii u sharding balancingu.

## Výhody a nevýhody
*   **Výhody:** Extrémní dostupnost, lineární škálovatelnost bez downtime (přidáním uzlu vzroste výkon), nulový "single point of failure". Velmi rychlé čtení časových řad díky Clustering klíčům.
*   **Nevýhody:** Nemožnost dělat `JOIN` (nutnost data ukládat víckrát – denormalizace). Slabší podpora ad-hoc analytických dotazů (nutnost vytvářet sekundární indexy typu SAI, jinak hrozí neefektivní table scan).

## Garance (Brewerův CAP teorém a PACELC)
*   **CAP teorém:** Cassandra v tomto nasazení funguje jako **AP systém** (dostupnost a tolerance vůči rozdělení sítě). V případě síťového rozdělení systém stále přijímá zápisy a umožňuje čtení, byť s rizikem vrácení neaktuálních dat.
*   **PACELC:** Spadá do kategorie **PA/EL** (Pokud dojde k Partition, volíme Availability; v případě Else volíme Latency nad konzistencí). S naší výchozí konzistencí `ONE` dosahujeme okamžité latence za cenu eventual consistency. Pokud u konkrétního dotazu požadujeme přesná data, lze dynamicky přepnout na konzistenci `QUORUM` nebo `ALL` a přesunout řešení k silnější konzistenci.

## Specifika vlastního řešení (Konfigurace a Docker Compose)
Řešení neobsahuje neoficiální modifikace zdrojového kódu, opírá se o standardní image, ale využívá pokročilou customizaci v `docker-compose.yml`:
*   **Služby a obrazy:** 3x `cassandra:5.0` (databázové uzly), 1x `python:3.11-slim` (inicializační skript `cassandra-init`). Značka `latest` není použita.
*   **Porty:** Pouze port `9042` (nativní CQL transport) je publikován z `cassandra-1` na hostitele pro přístup nástrojů (např. DBeaver/DataGrip).
*   **Sítě a volumes:** Interní overlay Docker síť pro discovery uzlů. Bind mounts (`./data`, `./scripts`) zajišťují bezstavovost init kontejneru a sdílení dat s hostitelským OS.
*   **Proměnné prostředí:** Všechna hesla, názvy clusterů a cesty jsou externalizovány do `.env` (ukázka uložena v `.env.example`).
*   **Omezení prostředků:** Explicitní nastavení haldy JVM `JVM_OPTS=-Xms512M -Xmx512M` brání OOM (Out-of-Memory) pádům Docker deamona.
*   **Závislosti a init skripty:** Kontejner `cassandra-init` spouští inicializaci až ve chvíli, kdy všechny 3 databázové uzly nahlásí `service_healthy`. Python skript idempotentně (kontroluje počet záznamů přes `SELECT count(*)`) vytvoří uživatele a provede import velkého objemu CSV souborů.

## Dataset
Pro řešení byl zvolen dataset "Brazilian E-Commerce Public Dataset by Olist". Obsahuje 3 relačně propojené datasety: Objednávky (~100k záznamů), Položky objednávek (~112k záznamů) a Produkty (~32k záznamů). Analýza v Pythonu (viz `data/analyza_dat.ipynb`) ukázala 100% propojenost datových entit, ale odhalila několik chybějících hodnot (např. prázdná váha produktu), které jsou ošetřeny rovnou při importu databáze.

## Závěr
Navržené řešení spolehlivě demonstruje schopnosti Apache Cassandra jakožto robustního wide-column storu. Díky automatizaci přes Docker a Python je projekt okamžitě reprodukovatelný. Prohloubil jsem si znalosti denormalizace, indexace pomocí SAI a uvědomil si omezení dotazovacího jazyka CQL (např. absence agregací přes více tabulek), které si vyžadují naprosto jiný "Query-First" způsob myšlení oproti SQL databázím. Architekturu lze snadno dále rozšiřovat např. o Spark pro komplexní datovou analýzu.

## Prohlášení o použití AI
V průběhu vypracování práce byl použit nástroj umělé inteligence (LLM model / Asistent).
*   **Název a verze nástroje:** LLM Model (přes vývojové prostředí).
*   **Účel:** Nástroj byl využit pro generování boilerplate kódu do souboru `docker-compose.yml`, sepsání idempotentní importní Python logiky a generování nápadů na netriviální dotazy pro specifika Cassandry (UDF, SAI, LWT transakce).
*   **Korekce výstupů:** Umělá inteligence při návrhu přístupových údajů vygenerovala uživatelské jméno obsahující velká písmena. Bylo nutné upravit jméno na malá písmena, neboť Cassandra bez explicitních uvozovek vynucuje u auth loginů malá písmena. Dále byly ignorovány "anti-pattern" warningy Cassandra Python driveru týkající se operátoru `USE`.

## Zdroje a nástroje
*   DataStax, *Apache Cassandra 5.0 Documentation*. Dostupné na: https://docs.datastax.com/
*   Kaggle, *Brazilian E-Commerce Public Dataset by Olist*. Dostupné na: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
*   Python Software Foundation, *Pandas a Cassandra-driver Documentation*.