import pandas as pd
import os

# Cesty k původním staženým souborům
flights_file = 'flights.csv'
airports_file = 'airports.csv'
airlines_file = 'airlines.csv'

print("Rozděluji data do 3 kolekcí po 2 souborech...")

# 1. Kolekce: Lety (časové řady, v zadání musí mít > 5000 záznamů)
# Načteme jen 40 000 řádků, abychom udrželi malé soubory (pod 100 MB)
df_flights = pd.read_csv(flights_file, nrows=40000)
# Rozdělíme na dva soubory
df_flights.iloc[:20000].to_csv('kolekce1_flights_part1.csv', index=False)
df_flights.iloc[20000:].to_csv('kolekce1_flights_part2.csv', index=False)
print("Kolekce 1 (Lety) - Hotovo. (2 soubory, každý 20 000 záznamů)")

# 2. Kolekce: Letiště (geodata pro mapy v Kibaně)
df_airports = pd.read_csv(airports_file)
mid_airports = len(df_airports) // 2
df_airports.iloc[:mid_airports].to_csv('kolekce2_airports_part1.csv', index=False)
df_airports.iloc[mid_airports:].to_csv('kolekce2_airports_part2.csv', index=False)
print("Kolekce 2 (Letiště) - Hotovo. (2 soubory)")

# 3. Kolekce: Aerolinky (číselník)
df_airlines = pd.read_csv(airlines_file)
mid_airlines = len(df_airlines) // 2
df_airlines.iloc[:mid_airlines].to_csv('kolekce3_airlines_part1.csv', index=False)
df_airlines.iloc[mid_airlines:].to_csv('kolekce3_airlines_part2.csv', index=False)
print("Kolekce 3 (Aerolinky) - Hotovo. (2 soubory)")

print("Příprava dat kompletní! Původní soubory můžeš smazat.")