import os
import time
import json
import urllib.request
import urllib.error
import base64
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ELASTIC_PASSWORD = os.environ.get('ELASTIC_PASSWORD')
KIBANA_PASSWORD = os.environ.get('KIBANA_PASSWORD')
LOGSTASH_PASSWORD = os.environ.get('LOGSTASH_PASSWORD')

ES_URL = "http://elasticsearch:9200"


def get_auth_header():
    auth_string = f"elastic:{ELASTIC_PASSWORD}"
    b64_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    return f"Basic {b64_auth}"


def send_es_request(endpoint, payload):
    url = f"{ES_URL}/{endpoint}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', get_auth_header())

    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode()
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Chyba u {endpoint}: {e.code} - {e.read().decode()}")
        raise e


def wait_for_elasticsearch():
    logger.info("Čekám na plný start Elasticsearch...")
    max_retries = 15
    for i in range(max_retries):
        try:
            req = urllib.request.Request(ES_URL)
            req.add_header('Authorization', get_auth_header())
            with urllib.request.urlopen(req) as response:
                if response.getcode() == 200:
                    logger.info("Elasticsearch je připraven!")
                    return
        except Exception as e:
            logger.warning(f"Pokus {i + 1}/{max_retries} selhal. Čekám 10s... ({e})")
            time.sleep(10)
    raise Exception("Nepodařilo se připojit k Elasticsearch.")


def setup_security():
    logger.info("Nastavuji heslo pro kibana_system...")
    send_es_request("_security/user/kibana_system/_password", {"password": KIBANA_PASSWORD})

    logger.info("Vytvářím roli logstash_writer...")
    role_payload = {
        "cluster": ["manage_index_templates", "monitor", "manage_ilm"],
        "indices": [{"names": ["*"], "privileges": ["write", "create", "create_index", "manage", "manage_ilm"]}]
    }
    send_es_request("_security/role/logstash_writer", role_payload)

    logger.info("Vytvářím uživatele logstash_internal...")
    user_payload = {
        "password": LOGSTASH_PASSWORD,
        "roles": ["logstash_writer"]
    }
    send_es_request("_security/user/logstash_internal", user_payload)


if __name__ == "__main__":
    time.sleep(5)
    wait_for_elasticsearch()
    setup_security()
    logger.info("Bezpečnostní Setup ELK dokončen!")