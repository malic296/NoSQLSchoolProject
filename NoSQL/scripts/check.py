import subprocess


def run_command(command, title):
    print(f"\n{'=' * 10} {title} {'=' * 10}")
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print("CHYBA:", result.stderr.strip())
    except Exception as e:
        print(f"Nepodařilo se spustit příkaz: {e}")


if __name__ == "__main__":
    run_command("nodetool status", "STAV CLUSTERU")

    run_command("nodetool ring | grep dc1 | awk '{print $1, $2, $3, $7, $8}'", "ROZLOŽENÍ TOKENŮ (SHARDING)")

    run_command(
        "cqlsh cassandra-1 -u cassandra -p cassandra -e 'SELECT count(*) FROM school_project.sensor_data;'",
        "POČET ZÁZNAMŮ V TABULCE"
    )