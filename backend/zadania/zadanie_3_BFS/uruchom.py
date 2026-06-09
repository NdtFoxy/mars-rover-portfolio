# -*- coding: utf-8 -*-
"""
Zadanie projektowe 3: Niepoinformowane strategie przeszukiwania (BFS).
Uruchom z dowolnego miejsca:  python3 uruchom.py
Generuje: zbior/mapa.txt (dane wejściowe) i decyzja/sciezka.txt (wynik BFS).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)
ZBIOR = os.path.join(HERE, "zbior")
DECYZJA = os.path.join(HERE, "decyzja")
os.makedirs(ZBIOR, exist_ok=True)
os.makedirs(DECYZJA, exist_ok=True)

import random
from app.core.environment import Environment
from zadania.zadanie_3_BFS.bfs import bfs_find_path

random.seed(42)


def render(env, sx, sy, gx, gy):
    sym = {0: ".", 1: "#", 2: "X"}
    rows = []
    for y in range(env.height):
        r = ""
        for x in range(env.width):
            if (x, y) == (sx, sy):
                r += "S"
            elif (x, y) == (gx, gy):
                r += "G"
            else:
                r += sym.get(env.get_terrain_type(x, y), "?")
        rows.append(r)
    return "\n".join(rows)


env = Environment(20, 15)
env.reset()

path = None
for _ in range(300):
    sx, sy = env._get_free_sand_position()
    gx, gy = env._get_free_sand_position()
    if (sx, sy) != (gx, gy):
        path, expanded = bfs_find_path(sx, sy, "N", gx, gy, env, return_stats=True)
        if path is not None:
            break

mapa = render(env, sx, sy, gx, gy)
moves = sum(1 for a in path if a == "MOVE_FORWARD")

with open(os.path.join(ZBIOR, "mapa.txt"), "w", encoding="utf-8") as f:
    f.write("DANE WEJSCIOWE (Zadanie 3 - BFS)\n")
    f.write("Legenda: . piasek | # skala | X krater | S start | G cel\n\n")
    f.write(mapa + "\n\n")
    f.write(f"Start = ({sx},{sy}),  Cel = ({gx},{gy})\n")

with open(os.path.join(DECYZJA, "sciezka.txt"), "w", encoding="utf-8") as f:
    f.write("DECYZJA: najkrotsza sciezka znaleziona przez BFS (liczba akcji)\n")
    f.write(f"Akcje: {len(path)} (ruchy do przodu: {moves})\n")
    f.write(f"Rozwiniete wezly (koszt obliczen): {expanded}\n\n")
    f.write(" -> ".join(path) + "\n")

print("=" * 60)
print(" ZADANIE 3 - BFS (niepoinformowane przeszukiwanie)")
print("=" * 60)
print(mapa)
print(f"\nStart=({sx},{sy})  Cel=({gx},{gy})")
print(f"Sciezka BFS: {len(path)} akcji | rozwiniete wezly: {expanded}")
print("Zapisano: zbior/mapa.txt, decyzja/sciezka.txt")
