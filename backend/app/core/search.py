import heapq
from typing import List, Tuple, Optional, Dict
from .environment import Environment

TERRAIN_COSTS = {
    0: 2.0,  # 0 - Piasek (Sand)
    1: 6.0   # 1 - Skały (Rock)
    # 2 - Krater (jako ściana)
}
TURN_COST = 0.5 

def heuristic(x: int, y: int, goal_x: int, goal_y: int) -> float:
    """Odległość Manhattan"""
    return abs(x - goal_x) + abs(y - goal_y)

def reconstruct_path(came_from: Dict, current_state: Tuple) -> List[str]:
    path =[]
    while current_state in came_from:
        current_state, action = came_from[current_state]
        path.append(action)
    path.reverse()
    return path

def astar_find_path(start_x: int, start_y: int, start_dir: str, goal_x: int, goal_y: int, env: Environment) -> Optional[List[str]]:
    """Algorytm A* z funkcją priorytetu f(n) = g(n) + h(n)"""
    start_state = (start_x, start_y, start_dir)

    open_heap =[]
    heapq.heappush(open_heap, (0, 0, start_state))

    g_score = {start_state: 0.0}
    came_from = {}

    dirs =['N', 'E', 'S', 'W']
    offsets = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}

    while open_heap:
        current_f, current_g, current_state = heapq.heappop(open_heap)
        cx, cy, cdir = current_state

        if cx == goal_x and cy == goal_y:
            return reconstruct_path(came_from, current_state)

        if current_g > g_score.get(current_state, float('inf')):
            continue

        idx = dirs.index(cdir)
        successors = []

        successors.append(((cx, cy, dirs[(idx - 1) % 4]), "TURN_LEFT", TURN_COST))
        successors.append(((cx, cy, dirs[(idx + 1) % 4]), "TURN_RIGHT", TURN_COST))

        dx, dy = offsets[cdir]
        nx, ny = cx + dx, cy + dy
        if env.is_within_bounds(nx, ny):
            terrain_type = env.get_terrain_type(nx, ny)
            
            # Kratery 2
            if terrain_type != 2:
                forward_cost = TERRAIN_COSTS.get(terrain_type, 100.0)
                successors.append(((nx, ny, cdir), "MOVE_FORWARD", forward_cost))

        for next_state, action, action_cost in successors:
            tentative_g = current_g + action_cost

            if tentative_g < g_score.get(next_state, float('inf')):
                came_from[next_state] = (current_state, action)
                g_score[next_state] = tentative_g
                f = tentative_g + heuristic(next_state[0], next_state[1], goal_x, goal_y)
                heapq.heappush(open_heap, (f, tentative_g, next_state))

    return None