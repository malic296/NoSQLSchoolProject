# Návod ke spuštění (ELK Stack)

Tato sekce popisuje, jak krok za krokem spustit projektovou část Elastic Stacku.

## 1. Konfigurace prostředí
Ve složce `ELK` se nachází soubor `.env.example`. Zkopírujte jej, přejmenujte na `.env` a doplňte vlastní přístupová hesla pro služby:

    cp .env.example .env

*(Pro testování na lokálním prostředí a účely hodnocení je doporučeno nechat hodnoty tak, jak jsou předvyplněné v repozitáři).*

## 2. Spuštění kontejnerů
V adresáři `ELK` spusťte všechny služby jediným příkazem:

    docker compose up -d

Co se stane na pozadí:
1. Nastartuje Elasticsearch.
2. Jakmile hlásí stav `healthy`, spustí se jednorázový Python skript `setup.py`, který vytvoří bezpečné účty pro Logstash a Kibanu.
3. Poté nastartuje Kibana a Logstash. Logstash automaticky začne stahovat a parsovat 6 CSV souborů do 3 indexů (`flights-000001`, `airports-000001`, `airlines-000001`).

## 3. Přístup a vizualizace
* **Kibana:** Dostupná na adrese `http://localhost:5601`.
* **Přihlášení:** Výchozí uživatel je `elastic`, heslo je hodnota `ELASTIC_PASSWORD` ze souboru `.env`.
* **Data:** Po načtení Logstashem jsou data okamžitě vidět v sekci *Management -> Dev Tools* příkazem `GET _cat/indices?v`.
* Vyhledávací REST API dotazy lze spouštět přímo v konzoli Dev Tools (jejich znění je v `elk/queries/queries.txt`).

## 4. Zastavení a vyčištění
Pro ukončení chodu a smazání kontejnerů spusťte:

    docker compose down

Pro úplné promazání databázových svazků a začátek načisto použijte:

    docker compose down -v