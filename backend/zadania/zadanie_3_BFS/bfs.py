# -*- coding: utf-8 -*-
"""
Zadanie 3 — przeszukiwanie niepoinformowane: BFS.
Задanie 3 — непоинформированный поиск: BFS.

Przeszukiwanie grafu stanów wszerz (kolejka FIFO), bez kosztu i bez heurystyki.
Поиск по графу состояний в ширину (очередь FIFO), без стоимости и без эвристики.

Stan ma postać `(x, y, kierunek)`, a dostępne akcje to `MOVE_FORWARD`,
`TURN_LEFT` i `TURN_RIGHT`.
Состояние имеет вид `(x, y, kierunek)`, а доступные действия это `MOVE_FORWARD`,
`TURN_LEFT` и `TURN_RIGHT`.
"""
from collections import deque
from typing import List, Dict
from app.core.environment import Environment


def reconstruct_path(came_from: Dict, current_state: tuple) -> List[str]:
    """Odtwarza listę akcji od celu do startu, cofając się po mapie `came_from`,
    a następnie odwraca ją, by uzyskać kolejność start -> cel."""
    path = []
    while current_state in came_from:          # dopóki mamy zapisanego poprzednika
        current_state, action = came_from[current_state]   # cofnij się o jeden krok
        path.append(action)                    # zapamiętaj akcję, która tu doprowadziła
    path.reverse()                             # mieliśmy cel->start, odwracamy na start->cel
    return path


def bfs_find_path(start_x: int, start_y: int, start_dir: str, goal_x: int, goal_y: int,
                  env: Environment, return_stats: bool = False):
    """BFS.
    `return_stats=True` zwraca `(ścieżka, liczba_rozwiniętych_węzłów)`.
    `return_stats=True` возвращает `(ścieżka, liczba_rozwiniętych_węzłów)`.
    """
    start_state = (start_x, start_y, start_dir)
    queue = deque([start_state])   # OPEN: kolejka FIFO (klucz BFS -- przeszukiwanie wszerz)
    came_from: Dict = {}           # mapa nastepnik -> (poprzednik, akcja) do odtworzenia trasy
    visited = {start_state}        # CLOSED: stany juz dodane, chroni przed cyklami
    expanded = 0                   # licznik rozwinietych wezlow (do porownania z A*)

    dirs = ['N', 'E', 'S', 'W']    # kolejnosc kierunkow; obrot = przejscie o +/-1 w tej liscie
    offsets = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}  # wektor ruchu "do przodu"

    while queue:
        current_state = queue.popleft()   # FIFO: bierzemy najstarszy stan (najplytszy poziom)
        cx, cy, cdir = current_state
        expanded += 1

        if cx == goal_x and cy == goal_y:           # cel osiagniety -> pierwsza droga = najkrotsza
            path = reconstruct_path(came_from, current_state)
            return (path, expanded) if return_stats else path

        # Generowanie nastepnikow = 3 akcje agenta: obrot w lewo, obrot w prawo, ruch do przodu.
        idx = dirs.index(cdir)
        successors = [
            ((cx, cy, dirs[(idx - 1) % 4]), "TURN_LEFT"),    # obrot w lewo: tylko zmiana kierunku
            ((cx, cy, dirs[(idx + 1) % 4]), "TURN_RIGHT"),   # obrot w prawo: tylko zmiana kierunku
        ]
        dx, dy = offsets[cdir]
        nx, ny = cx + dx, cy + dy
        # Ruch do przodu mozliwy tylko gdy pole jest w granicach i nie jest kraterem (typ 2 = sciana).
        if env.is_within_bounds(nx, ny) and env.get_terrain_type(nx, ny) != 2:
            successors.append(((nx, ny, cdir), "MOVE_FORWARD"))

        for next_state, action in successors:
            if next_state not in visited:        # pomijamy stany juz odwiedzone (anty-cykl)
                visited.add(next_state)
                came_from[next_state] = (current_state, action)  # zapamietaj skad i jaka akcja
                queue.append(next_state)         # dopisz na koniec kolejki (FIFO)

    return (None, expanded) if return_stats else None   # brak sciezki (cel nieosiagalny)
