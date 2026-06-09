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
    path = []
    while current_state in came_from:
        current_state, action = came_from[current_state]
        path.append(action)
    path.reverse()
    return path


def bfs_find_path(start_x: int, start_y: int, start_dir: str, goal_x: int, goal_y: int,
                  env: Environment, return_stats: bool = False):
    """BFS.
    `return_stats=True` zwraca `(ścieżka, liczba_rozwiniętych_węzłów)`.
    `return_stats=True` возвращает `(ścieżka, liczba_rozwiniętych_węzłów)`.
    """
    start_state = (start_x, start_y, start_dir)
    queue = deque([start_state])
    came_from: Dict = {}
    visited = {start_state}
    expanded = 0

    dirs = ['N', 'E', 'S', 'W']
    offsets = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}

    while queue:
        current_state = queue.popleft()
        cx, cy, cdir = current_state
        expanded += 1

        if cx == goal_x and cy == goal_y:
            path = reconstruct_path(came_from, current_state)
            return (path, expanded) if return_stats else path

        idx = dirs.index(cdir)
        successors = [
            ((cx, cy, dirs[(idx - 1) % 4]), "TURN_LEFT"),
            ((cx, cy, dirs[(idx + 1) % 4]), "TURN_RIGHT"),
        ]
        dx, dy = offsets[cdir]
        nx, ny = cx + dx, cy + dy
        if env.is_within_bounds(nx, ny) and env.get_terrain_type(nx, ny) != 2:
            successors.append(((nx, ny, cdir), "MOVE_FORWARD"))

        for next_state, action in successors:
            if next_state not in visited:
                visited.add(next_state)
                came_from[next_state] = (current_state, action)
                queue.append(next_state)

    return (None, expanded) if return_stats else None
