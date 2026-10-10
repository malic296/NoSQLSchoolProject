# Návod k nasazení (HOWTO) - Část 1: NoSQL (Apache Cassandra)

## 1. Požadavky na systém
*   **Operační paměť (RAM):** Minimálně 16 GB RAM (každý uzel Cassandry má alokováno 512 MB haldy, plus režie kontejnerů a OS).
*   **Architektura:** Testováno a plně funkční na platformě x86_64.
*   **Nástroje:** Nainstalovaný Docker a Docker Compose.

## 2. Postup nasazení
1. Naklonujte repozitář nebo rozbalte adresář s projektem.
2. V kořenovém adresáři repozitáře vytvořte kopii vzorového souboru proměnných prostředí:
   `cp .env.example .env` (Linux/Mac) nebo `Copy-Item .env.example .env` (PowerShell).
3. Přejděte do složky 1. části:
   `cd "1 - NoSQL technologie"`
4. Spusťte celé řešení na pozadí jediným příkazem:
   `docker compose up -d`
5. Vyčkejte na inicializaci. Sledovat průběh importu dat můžete příkazem:
   `docker compose logs -f cassandra-init`

## 3. Orientační čas spuštění
*   **První spuštění (včetně stažení Docker obrazů a importu ~240 000 záznamů):** Cca 5–8 minut v závislosti na rychlosti sítě a disku.
*   **Opakované spuštění (již stažené obrazy a existující data):** Cca 2–3 minuty (čeká se pouze na Discovery fázi Cassandry). Importní skript je idempotentní a přeskočí se.

## 4. Kontrola správného běhu řešení
Úspěšné nasazení ověříte spuštěním kontrolního Python skriptu uvnitř hlavního uzlu. Tento skript vypíše stav clusteru, rozložení dat (tokeny) a aktuální počet záznamů v databázi.

**Příkaz:**
`docker compose exec cassandra-1 python3 /scripts/check.py`

**Očekávaný výstup (kontrolní seznam):**
*   V sekci STAV CLUSTERU musí být vidět 3 uzly se statusem `UN` (Up, Normal).
*   V sekci ROZLOŽENÍ TOKENŮ musí být vypsány přidělené rozsahy pro všechny 3 uzly.
*   V sekci POČET ZÁZNAMŮ musí být hodnota > 0 (pokud doběhl inicializační kontejner).