# -*- coding: utf-8 -*-
"""
Zadanie projektowe 4: Poinformowane strategie przeszukiwania (A*).
Uruchom:  python3 uruchom.py
Generuje: zbior/mapa.txt (mapa + koszty kafli) i decyzja/sciezka.txt (wynik A*).
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
from zadania.zadanie_4_Astar.astar import astar_find_path, TERRAIN_COSTS, TURN_COST
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


def path_cost(path, sx, sy, sdir, env):
    dirs = ['N', 'E', 'S', 'W']
    off = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
    x, y, d = sx, sy, sdir
    cost = 0.0
    for a in path:
        if a == "TURN_LEFT":
            d = dirs[(dirs.index(d) - 1) % 4]; cost += TURN_COST
        elif a == "TURN_RIGHT":
            d = dirs[(dirs.index(d) + 1) % 4]; cost += TURN_COST
        elif a == "MOVE_FORWARD":
            dx, dy = off[d]; x, y = x + dx, y + dy
            cost += TERRAIN_COSTS.get(env.get_terrain_type(x, y), 1.0)
    return cost


env = Environment(20, 15)
env.reset()

path = None
for _ in range(300):
    sx, sy = env._get_free_sand_position()
    gx, gy = env._get_free_sand_position()
    if (sx, sy) != (gx, gy):
        path, a_exp = astar_find_path(sx, sy, "N", gx, gy, env, return_stats=True)
        if path is not None:
            break

_, b_exp = bfs_find_path(sx, sy, "N", gx, gy, env, return_stats=True)  # porównanie
cost = path_cost(path, sx, sy, "N", env)
mapa = render(env, sx, sy, gx, gy)

with open(os.path.join(ZBIOR, "mapa.txt"), "w", encoding="utf-8") as f:
    f.write("DANE WEJSCIOWE (Zadanie 4 - A*)\n")
    f.write("Legenda: . piasek | # skala | X krater | S start | G cel\n")
    f.write(f"Zroznicowane koszty wjazdu: piasek={TERRAIN_COSTS[0]}, skala={TERRAIN_COSTS[1]}, obrot={TURN_COST}\n\n")
    f.write(mapa + "\n\n")
    f.write(f"Start = ({sx},{sy}),  Cel = ({gx},{gy})\n")

with open(os.path.join(DECYZJA, "sciezka.txt"), "w", encoding="utf-8") as f:
    f.write("DECYZJA: najtansza sciezka znaleziona przez A* (koszt + heurystyka)\n")
    f.write(f"Koszt energetyczny sciezki: {cost:.1f}\n")
    f.write(f"Rozwiniete wezly: A*={a_exp}  vs  BFS={b_exp}  (A* przeszukuje mniej dzieki heurystyce)\n\n")
    f.write(" -> ".join(path) + "\n")

print("=" * 60)
print(" ZADANIE 4 - A* (poinformowane przeszukiwanie z kosztem)")
print("=" * 60)
print(mapa)
print(f"\nStart=({sx},{sy})  Cel=({gx},{gy})")
print(f"Koszt sciezki A*: {cost:.1f} | rozwiniete: A*={a_exp} vs BFS={b_exp}")
print("Zapisano: zbior/mapa.txt, decyzja/sciezka.txt")
