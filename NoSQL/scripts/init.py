import os
import time
import logging
import csv
from datetime import datetime
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

APP_USER = os.environ.get("APP_USER", "MyUser")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "MyPassword")

def connect_to_cluster():
    auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
    cluster = Cluster(['cassandra-1', 'cassandra-2', 'cassandra-3'], auth_provider=auth_provider)

    for i in range(10):
        try:
            session = cluster.connect()
            logger.info("Úspěšně připojeno k Cassandra clusteru.")
            return session, cluster
        except Exception as e:
            logger.warning(f"Pokus {i+1}/10 selhal. Čekám 10s... ({str(e)})")
            time.sleep(10)
    raise Exception("Nepodařilo se připojit k clusteru.")

def initialize_db(session):
    logger.info(f"Inicializuji uživatele '{APP_USER}' a práva...")
    session.execute(f"CREATE ROLE IF NOT EXISTS {APP_USER} WITH PASSWORD = '{APP_PASSWORD}' AND LOGIN = true;")

    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS school_project 
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3};
    """)
    session.execute(f"GRANT ALL PERMISSIONS ON KEYSPACE school_project TO {APP_USER};")
    session.set_keyspace('school_project')

    logger.info("Vytvářím tabulky pro E-commerce dataset...")

    # 1. Tabulka pro produkty
    session.execute("""
        CREATE TABLE IF NOT EXISTS products(
            product_id text PRIMARY KEY,
            category_name text,
            weight_g double
        );
    """)

    # 2. Tabulka pro objednávky (s časovým razítkem)
    session.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id text PRIMARY KEY,
            customer_id text,
            status text,
            purchase_timestamp timestamp
        );
    """)

    # 3. Tabulka pro položky v objednávkách (Partition Key = order_id, Clustering Key = order_item_id)
    session.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_id text,
            order_item_id int,
            product_id text,
            price double,
            freight_value double,
            PRIMARY KEY (order_id, order_item_id)
        );
    """)

    # Indexy (SAI) pro budoucí netriviální dotazy
    session.execute("CREATE CUSTOM INDEX IF NOT EXISTS orders_status_sai ON orders (status) USING 'StorageAttachedIndex';")
    session.execute("CREATE CUSTOM INDEX IF NOT EXISTS orders_customer_sai ON orders (customer_id) USING 'StorageAttachedIndex';")

def import_products(session):
    file_path = "/data/olist_products_dataset.csv"
    if not os.path.exists(file_path): return
    logger.info("Importuji produkty...")
    stmt = session.prepare("INSERT INTO products (product_id, category_name, weight_g) VALUES (?, ?, ?)")

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            weight = float(row['product_weight_g']) if row['product_weight_g'] else 0.0
            session.execute(stmt, (row['product_id'], row['product_category_name'], weight))
    logger.info("Produkty naimportovány.")

def import_orders(session):
    file_path = "/data/olist_orders_dataset.csv"
    if not os.path.exists(file_path): return
    logger.info("Importuji objednávky (tohle může trvat pár minut)...")
    stmt = session.prepare("INSERT INTO orders (order_id, customer_id, status, purchase_timestamp) VALUES (?, ?, ?, ?)")

    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Olist dataset používá formát '2017-10-02 10:56:33'
                dt = datetime.strptime(row['order_purchase_timestamp'], '%Y-%m-%d %H:%M:%S') if row['order_purchase_timestamp'] else None
                session.execute(stmt, (row['order_id'], row['customer_id'], row['order_status'], dt))
                count += 1
                if count % 10000 == 0: logger.info(f" -> Vloženo {count} objednávek...")
            except: continue
    logger.info(f"Objednávky naimportovány (celkem {count}).")

def import_order_items(session):
    file_path = "/data/olist_order_items_dataset.csv"
    if not os.path.exists(file_path): return
    logger.info("Importuji položky objednávek (tohle může trvat pár minut)...")
    stmt = session.prepare("INSERT INTO order_items (order_id, order_item_id, product_id, price, freight_value) VALUES (?, ?, ?, ?, ?)")

    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                session.execute(stmt, (
                    row['order_id'],
                    int(row['order_item_id']),
                    row['product_id'],
                    float(row['price']),
                    float(row['freight_value'])
                ))
                count += 1
                if count % 10000 == 0: logger.info(f" -> Vloženo {count} položek...")
            except: continue
    logger.info(f"Položky objednávek naimportovány (celkem {count}).")

def import_data_if_empty(session):
    result = session.execute("SELECT count(*) FROM orders LIMIT 1;")
    if result.one()[0] == 0:
        logger.info("Tabulky jsou prázdné. Zahajuji plný import CSV dat...")
        import_products(session)
        import_orders(session)
        import_order_items(session)
    else:
        logger.info("Data již existují. Import přeskočen (Idempotence dodržena).")

if __name__ == "__main__":
    session, cluster = connect_to_cluster()
    try:
        initialize_db(session)
        import_data_if_empty(session)
        logger.info("Inicializace kompletně dokončena!")
    finally:
        cluster.shutdown()