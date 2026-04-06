from collections import deque
from typing import List, Tuple, Optional, Set
from .environment import Environment

def bfs_find_path(start_x: int, start_y: int, start_dir: str, goal_x: int, goal_y: int, env: Environment) -> Optional[List[str]]:
    start_state = (start_x, start_y, start_dir)
    
    # 1. Struktura OPEN: Kolejka węzłów do rozwinięcia (FIFO - zasada działania BFS)
    # Przechowujemy: (obecny_stan, ścieżka_akcji_jak_tu_dotrzeć)
    open_list = deque()
    open_list.append((start_state,[]))
    
    # 2. Struktura CLOSED: Zbiór węzłów już odwiedzonych (zapobiega zapętleniu)
    closed_set: Set[Tuple[int, int, str]] = set()
    closed_set.add(start_state)
    
    dirs = ['N', 'E', 'S', 'W']
    offsets = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
    
    # 3. Pętla główna: dopóki lista OPEN nie jest pusta
    while open_list:
        (cx, cy, cdir), path = open_list.popleft()
        
        # 4. czy agent stoi na polu z celem?
        if cx == goal_x and cy == goal_y:
            return path
            
        # 5. Rozwijanie węzła o 3 możliwe akcje
        idx = dirs.index(cdir)
        
        # Akcja A: Obrót w lewo (pozycja się nie zmienia, zmienia się kierunek)
        left_dir = dirs[(idx - 1) % 4]
        state_l = (cx, cy, left_dir)
        if state_l not in closed_set:
            closed_set.add(state_l)
            open_list.append((state_l, path + ["TURN_LEFT"]))
            
        # Akcja B: Obrót w prawo
        right_dir = dirs[(idx + 1) % 4]
        state_r = (cx, cy, right_dir)
        if state_r not in closed_set:
            closed_set.add(state_r)
            open_list.append((state_r, path + ["TURN_RIGHT"]))
            
        # Akcja C: Ruch do przodu
        dx, dy = offsets[cdir]
        nx, ny = cx + dx, cy + dy
        
        # Ruch jest możliwy tylko jeśli jesteśmy w granicach i wchodzimy na Piasek (0)
        # Góry (1) traktujemy jako przeszkody (ściany), ponieważ BFS zakłada równy koszt przejścia.
        if env.is_within_bounds(nx, ny) and env.get_terrain_type(nx, ny) == 0:
            state_f = (nx, ny, cdir)
            if state_f not in closed_set:
                closed_set.add(state_f)
                open_list.append((state_f, path + ["MOVE_FORWARD"]))
                
    # Zwraca None, jeśli cel jest całkowicie otoczony górami i niedostępny
    return None