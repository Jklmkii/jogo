import pygame
import sys

TILE = 64
pygame.init()
screen = pygame.display.set_mode((1024, 640))
pygame.display.set_caption("Caverna do Dragao - Edicao Teoria dos Grafos")
font = pygame.font.SysFont(None, 32)
font_small = pygame.font.SysFont(None, 20)
clock = pygame.time.Clock()

levels = [
    [
        "########",
        "#P.....#",
        "#......#",
        "#......#",
        "#......#",
        "#......#",
        "#.....K#",
        "#.....D#",
    ],
    [
        "##########",
        "#P.......#",
        "#........#",
        "#..B.B.B.#",
        "#........#",
        "#....D...#",
        "##########",
    ],
    [
        "############",
        "#P.........#",
        "#..........#",
        "#....B.....#",
        "#..........#",
        "#.......N..#",
        "#........D.#",
        "############",
    ],
    [
        "############",
        "#P........B#",
        "#IIIIIIIII.#",
        "#B.........#",
        "#.IIIIIIIII#",
        "#........B.#",
        "#IIIIIIIII.#",
        "#B.........#",
        "#DIIIIIIIII#",
        "############"
    ],
    [
        "############",
        "#P..B.....B#",
        "#..........#",
        "#..B.....B.#",
        "#..........#",
        "#.....B...N#",
        "#........D.#",
        "############"
    ],
    [
        "#############",
        "#P.#.......##",
        "#..#.#.###.##",
        "##...#.#...##",
        "####.#.#.####",
        "#....#.#...##",
        "#.####.###.##",
        "#..........D#",
        "#############"
    ],
    [
        "########",
        "#P.....#",
        "######.#",
        "#......#",
        "#.######",
        "#.....D#",
        "########"
    ],
    [
        "#############",
        "#.....#.....#",
        "#..P..#..D..#",
        "#.....#.....#",
        "#####.#.#####",
        "#...........#",
        "#############"
    ]
]

level = 0
player = [1, 1]
msg = ""
msg_timer = 0        
dialog_active = False
game_over = False
victory = False        

pulse_active = False
pulse_radius = 0.0
pulse_origin = [0, 0]
pulse_distances = {}

shortest_path_tiles = []   
player_steps = 0           
max_steps_allowed = 0      

hamiltonian_total = 0      
hamiltonian_visited = set()

torches_placed = set()     
torches_limit = 12         

ITEM_DATA = {
    "Chave":             {"weight": 1,  "rarity": 3, "rarity_name": "Epico",  "value": 50},
    "Ossos":             {"weight": 2,  "rarity": 1, "rarity_name": "Comum",  "value": 5},
    "Pedacos de Madeira":{"weight": 5,  "rarity": 1, "rarity_name": "Comum",  "value": 10},
    "Ouro":              {"weight": 10, "rarity": 2, "rarity_name": "Raro",   "value": 100},
    "Vidro":             {"weight": 3,  "rarity": 1, "rarity_name": "Comum",  "value": 15}
}

inventory = []
sort_mode = "peso"
sort_algo = "quicksort"

def quick_sort(arr, key_func):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left   = [x for x in arr if key_func(x) < key_func(pivot)]
    middle = [x for x in arr if key_func(x) == key_func(pivot)]
    right  = [x for x in arr if key_func(x) > key_func(pivot)]
    return quick_sort(left, key_func) + middle + quick_sort(right, key_func)

def merge_sort(arr, key_func):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left  = merge_sort(arr[:mid], key_func)
    right = merge_sort(arr[mid:], key_func)
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key_func(left[i]) <= key_func(right[j]):
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def heap_sort(arr, key_func):
    def heapify(n, i):
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n and key_func(arr[i]) < key_func(arr[l]):
            largest = l
        if r < n and key_func(arr[largest]) < key_func(arr[r]):
            largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(n, largest)
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)
    for i in range(n - 1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(i, 0)
    return arr

def apply_sorting():
    global inventory
    if not inventory:
        return
    if sort_mode == "peso":
        inventory = quick_sort(inventory, lambda x: x["weight"])
    elif sort_mode == "raridade":
        inventory = merge_sort(inventory, lambda x: x["rarity"])
    elif sort_mode == "valor":
        inventory = heap_sort(inventory, lambda x: x["value"])

def run_bfs():
    global pulse_distances, shortest_path_tiles
    pulse_distances = {}
    shortest_path_tiles = []
    
    queue   = [(player[0], player[1], 0)]
    visited = {(player[0], player[1])}
    parent  = {} 
    target_pos = None
    
    while queue:
        cx, cy, dist = queue.pop(0)
        pulse_distances[(cx, cy)] = dist
        
        if grid[cy][cx] in ("D", "K") and target_pos is None:
            target_pos = (cx, cy)
            
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[ny]):
                if grid[ny][nx] not in ("#", "I") and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (cx, cy)
                    queue.append((nx, ny, dist + 1))
                    
    if target_pos in parent:
        curr = target_pos
        while curr in parent:
            shortest_path_tiles.append(curr)
            curr = parent[curr]

chest_dialog = False
chest_item   = ""
chest_x      = 0
chest_y      = 0

def chest_item_for(lv, nx, ny):
    """Retorna o item do baú na posição (nx, ny) do nível lv."""
    if lv == 1:
        if nx == 3: return "Chave"
        if nx == 5: return "Ossos"
        if nx == 7: return "Pedacos de Madeira"
    elif lv == 3:
        if nx == 10 and ny == 1: return "Vidro"
        if nx == 1  and ny == 3: return "Ossos"
        if nx == 9  and ny == 5: return "Pedacos de Madeira"
        if nx == 1  and ny == 7: return "Chave"
    elif lv == 4:
        if nx == 4  and ny == 1: return "Vidro"
        if nx == 10 and ny == 1: return "Vidro"
        if nx == 3  and ny == 3: return "Pedacos de Madeira"
        if nx == 9  and ny == 3: return "Ossos"
        if nx == 6  and ny == 5: return "Ossos"
    return "Ouro"

def load_level(i):
    global grid, player, msg, msg_timer, dialog_active, inventory
    global pulse_active, pulse_distances, chest_dialog
    global shortest_path_tiles, player_steps, max_steps_allowed
    global hamiltonian_total, hamiltonian_visited, torches_placed
    
    grid = [list(r) for r in levels[i]]
    inventory    = []
    msg          = ""
    msg_timer    = 0
    dialog_active = False
    chest_dialog  = False
    pulse_active  = False
    pulse_distances = {}
    
    shortest_path_tiles = []
    player_steps = 0
    hamiltonian_visited = set()
    torches_placed = set()
    
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c == "P":
                player = [x, y]
                grid[y][x] = "."
                
    if i == 5: 
        run_bfs()
        for (tx, ty), dist in pulse_distances.items():
            if levels[i][ty][tx] == "D":
                max_steps_allowed = dist + 4  
                break
        pulse_active = False
        pulse_distances = {}
    elif i == 6: 
        hamiltonian_total = sum(row.count(".") for row in grid) + 1  
        hamiltonian_visited.add((player[0], player[1]))

def set_msg(text, duration=3000):
    """Define uma mensagem com timer automático (ms)."""
    global msg, msg_timer
    msg       = text
    msg_timer = duration

load_level(level)

TILE_COLORS = {
    "#": (100, 100, 100),
    "K": (255, 128,   0),
    "D": (255, 215,   0),
    "B": (139,  69,  19),
    "N": (  0, 180, 255),
    ".": ( 30,  30,  30),
    "I": ( 30,  30,  30),
}

def draw_tile_detail(surface, c, rx, ry):
    """Desenha detalhes visuais extras sobre tiles especiais."""
    cx = rx + TILE // 2
    cy = ry + TILE // 2

    if c == "B": 
        inner = pygame.Rect(rx + 8, ry + 8, TILE - 16, TILE - 16)
        pygame.draw.rect(surface, (92, 58, 30), inner)
        pygame.draw.rect(surface, (60, 30, 10), (rx + TILE // 2 - 4, ry + TILE // 2 - 4, 8, 8))

    elif c == "N":  
        pygame.draw.circle(surface, (0, 140, 210), (cx, cy), TILE // 3)
        lbl = font_small.render("N", True, (255, 255, 255))
        surface.blit(lbl, lbl.get_rect(center=(cx, cy)))

    elif c == "D":  
        inner = pygame.Rect(rx + 10, ry + 6, TILE - 20, TILE - 12)
        pygame.draw.rect(surface, (200, 170, 0), inner)
        pygame.draw.rect(surface, (140, 100, 0), (cx - 4, cy - 4, 8, 8))

    elif c == "K":  
        pygame.draw.circle(surface, (255, 128, 0), (cx, ry + 20), 10)
        pygame.draw.circle(surface, (200, 80, 0),  (cx, ry + 20), 10, 2)
        pygame.draw.line(surface, (255, 128, 0), (cx, ry + 30), (cx, ry + TILE - 12), 4)
        pygame.draw.line(surface, (255, 128, 0), (cx, ry + TILE - 20), (cx + 6, ry + TILE - 14), 3)
        pygame.draw.line(surface, (255, 128, 0), (cx, ry + TILE - 28), (cx + 6, ry + TILE - 22), 3)

while True:
    dt = clock.tick(60)   

    if msg_timer > 0:
        msg_timer -= dt
        if msg_timer <= 0:
            msg = ""

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if victory:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                level = 0
                victory = False
                game_over = False
                load_level(level)
            continue

        if game_over:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                level = 0
                game_over = False
                load_level(level)
            continue

        if chest_dialog:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_s:
                    item_props = ITEM_DATA[chest_item].copy()
                    item_props["name"] = chest_item
                    inventory.append(item_props)
                    apply_sorting()
                    set_msg(f"{chest_item} coletado(a)!")
                    grid[chest_y][chest_x] = "."
                    chest_dialog = False
                elif e.key == pygame.K_n:
                    set_msg("Voce deixou o item no bau.")
                    chest_dialog = False
            continue

        if dialog_active:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_s:
                    if level == 4:
                        total_value = sum(item["value"] for item in inventory)
                        if total_value >= 50:
                            inventory.clear()
                            key_props = ITEM_DATA["Chave"].copy()
                            key_props["name"] = "Chave"
                            inventory.append(key_props)
                            apply_sorting()
                            set_msg("Chave bought por $50!")
                        else:
                            set_msg(f"Falta valor! Voce tem ${total_value}/50")
                    else:
                        gold_item = next((item for item in inventory if item["name"] == "Ouro"), None)
                        if gold_item:
                            inventory.remove(gold_item)
                            key_props = ITEM_DATA["Chave"].copy()
                            key_props["name"] = "Chave"
                            inventory.append(key_props)
                            apply_sorting()
                            set_msg("NPC criou uma chave!")
                        else:
                            set_msg("Voce nao possui ouro.")
                    dialog_active = False
                elif e.key == pygame.K_n:
                    set_msg("Talvez outra hora.")
                    dialog_active = False
            continue

        if e.type == pygame.KEYDOWN:

            if e.key == pygame.K_t:
                run_bfs()
                pulse_active  = True
                pulse_radius  = 0.0
                pulse_origin  = list(player)
                set_msg("Sensor de Rota active!")

            if e.key == pygame.K_SPACE and level == 7:
                pos = (player[0], player[1])
                if pos in torches_placed:
                    torches_placed.remove(pos)
                    set_msg("Tocha coletada de volta.")
                else:
                    if len(torches_placed) < torches_limit:
                        torches_placed.add(pos)
                        set_msg(f"Tocha ativada! ({len(torches_placed)}/{torches_limit})")
                    else:
                        set_msg("Limite de tochas atingido!")

            if e.key == pygame.K_1:
                sort_mode, sort_algo = "peso", "quicksort"
                apply_sorting(); set_msg("Ordenado: Peso")
            elif e.key == pygame.K_2:
                sort_mode, sort_algo = "raridade", "mergesort"
                apply_sorting(); set_msg("Ordenado: Raridade")
            elif e.key == pygame.K_3:
                sort_mode, sort_algo = "valor", "heapsort"
                apply_sorting(); set_msg("Ordenado: Valor")

            dx, dy = 0, 0
            if e.key in (pygame.K_w, pygame.K_UP):    dy = -1
            if e.key in (pygame.K_s, pygame.K_DOWN):  dy =  1
            if e.key in (pygame.K_a, pygame.K_LEFT):  dx = -1
            if e.key in (pygame.K_d, pygame.K_RIGHT): dx =  1

            nx = player[0] + dx
            ny = player[1] + dy

            if 0 <= ny < len(grid) and 0 <= nx < len(grid[ny]):
                t = grid[ny][nx]
                if t not in ("#", "I"):
                    
                    if level == 5:
                        player_steps += 1
                        if player_steps > max_steps_allowed:
                            game_over = True
                            set_msg("Passos esgotados! Falhou no caminho minimo.")
                            continue
                            
                    if level == 6:
                        if (nx, ny) in hamiltonian_visited:
                            set_msg("O chão ruiu! Voce nao pode re-visitar caminhos.")
                            continue
                        grid[player[1]][player[0]] = "#" 
                        hamiltonian_visited.add((nx, ny))

                    player = [nx, ny]

                    if t == "K":
                        key_props = ITEM_DATA["Chave"].copy()
                        key_props["name"] = "Chave"
                        inventory.append(key_props)
                        apply_sorting()
                        grid[ny][nx] = "."
                        set_msg("Chave coletada!")

                    if t == "B":
                        chest_dialog = True
                        chest_item   = chest_item_for(level, nx, ny)
                        chest_x, chest_y = nx, ny

                    if t == "N":
                        dialog_active = True

                    if t == "D":
                        if level < 5: 
                            if any(item["name"] == "Chave" for item in inventory):
                                level += 1
                                load_level(level)
                            else:
                                set_msg("Porta Trancada!")
                                
                        elif level == 5: 
                            level += 1
                            load_level(level)
                            
                        elif level == 6: 
                            if len(hamiltonian_visited) == hamiltonian_total:
                                level += 1
                                load_level(level)
                            else:
                                set_msg(f"Faltam {hamiltonian_total - len(hamiltonian_visited)} blocos para cobrir tudo!")
                                game_over = True 
                                
                        elif level == 7: 
                            all_covered = True
                            for cy in range(len(grid)):
                                for cx in range(len(grid[cy])):
                                    if grid[cy][cx] == ".":
                                        covered = any((cx+v[0], cy+v[1]) in torches_placed for v in [(0,0),(0,1),(0,-1),(1,0),(-1,0)])
                                        if not covered:
                                            all_covered = False
                            if all_covered and len(torches_placed) <= torches_limit:
                                level += 1
                                if level >= len(levels): 
                                    victory = True
                                else: 
                                    load_level(level)
                            else:
                                set_msg(f"Escuridao profunda! Use no maximo {torches_limit} tochas.")

    if victory:
        screen.fill((5, 5, 20))
        lbl1 = font.render("PARABENS! VOCE VENCEU O DESAFIO", True, (255, 215, 0))
        lbl2 = font_small.render("Voce completou com sucesso todos os 8 níveis!", True, (180, 180, 255))
        lbl3 = font_small.render("Pressione [R] para recomecar o jogo", True, (200, 200, 200))
        screen.blit(lbl1, (512 - lbl1.get_width() // 2, 260))
        screen.blit(lbl2, (512 - lbl2.get_width() // 2, 310))
        screen.blit(lbl3, (512 - lbl3.get_width() // 2, 350))
        pygame.display.flip()
        continue

    if game_over:
        screen.fill((15, 15, 15))
        lbl_go  = font.render("FIM DE JOGO", True, (255, 50, 50))
        lbl_rst = font_small.render("Pressione [R] para reiniciar a partir da primeira fase", True, (200, 200, 200))
        screen.blit(lbl_go,  (512 - lbl_go.get_width()  // 2, 280))
        screen.blit(lbl_rst, (512 - lbl_rst.get_width() // 2, 340))
        pygame.display.flip()
        continue

    if pulse_active:
        pulse_radius += 0.08
        max_dist = max(pulse_distances.values()) if pulse_distances else 0
        if pulse_radius > max_dist + 1:
            pulse_active = False

    screen.fill((20, 20, 20))

    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            rx, ry = x * TILE, y * TILE
            r = pygame.Rect(rx, ry, TILE, TILE)

            pygame.draw.rect(screen, TILE_COLORS.get(c, (30, 30, 30)), r)
            pygame.draw.rect(screen, (60, 60, 60), r, 1)

            if level == 7:
                is_illuminated = any((x + v[0], y + v[1]) in torches_placed for v in [(0,0), (0,1), (0,-1), (1,0), (-1,0)])
                if is_illuminated:
                    glow_layer = pygame.Surface((TILE, TILE))
                    glow_layer.fill((255, 200, 60))  
                    glow_layer.set_alpha(65)         
                    screen.blit(glow_layer, (rx, ry))

            if pulse_active and (x, y) in shortest_path_tiles and level == 5:
                pygame.draw.circle(screen, (0, 255, 0), (rx + TILE//2, ry + TILE//2), 6)

            if level == 7 and (x, y) in torches_placed:
                pygame.draw.circle(screen, (255, 69, 0), (rx + TILE//2, ry + TILE//2), 14)
                pygame.draw.circle(screen, (255, 215, 0), (rx + TILE//2, ry + TILE//2), 8)

            draw_tile_detail(screen, c, rx, ry)

            if pulse_active and (x, y) in pulse_distances:
                if abs(pulse_radius - pulse_distances[(x, y)]) < 0.7:
                    alpha = 1 - abs(pulse_radius - pulse_distances[(x, y)]) / 0.7
                    flash = pygame.Surface((TILE, TILE))
                    flash.fill((0, 255, 80))
                    flash.set_alpha(int(alpha * 180))
                    screen.blit(flash, (rx, ry))

    px, py = player[0] * TILE, player[1] * TILE
    pygame.draw.rect(screen, (30, 90, 220), (px + 4, py + 4, TILE - 8, TILE - 8))
    pygame.draw.circle(screen, (140, 180, 255), (px + TILE // 2, py + 16), 8)   

    pygame.draw.rect(screen, (40, 40, 40), (768, 0, 256, 640))
    screen.blit(font.render("Inventario", True, (255, 255, 255)), (785, 15))
    screen.blit(font_small.render(f"Filtro: {sort_mode.upper()}", True, (0, 255, 255)), (785, 45))
    screen.blit(font_small.render(f"Algo: {sort_algo.upper()}",   True, (200, 200, 200)), (785, 65))
    pygame.draw.line(screen, (100, 100, 100), (775, 85), (1015, 85), 1)

    for idx, item in enumerate(inventory):
        name_surf = font_small.render(f"{item['name']}", True, (255, 255, 255))
        screen.blit(name_surf, (785, 95 + idx * 45))
        details = f"{item['weight']}kg | {item['rarity_name']} | ${item['value']}"
        det_surf = font_small.render(details, True, (180, 180, 180))
        screen.blit(det_surf, (785, 112 + idx * 45))

    pygame.draw.line(screen, (100, 100, 100), (775, 485), (1015, 485), 1)
    
    if level == 5:
        screen.blit(font_small.render(f"Passos: {player_steps} / {max_steps_allowed}", True, (255, 100, 100)), (785, 495))
    elif level == 6:
        screen.blit(font_small.render(f"Nos visitados: {len(hamiltonian_visited)} / {hamiltonian_total}", True, (100, 255, 100)), (785, 495))
    elif level == 7:
        screen.blit(font_small.render(f"Tochas: {len(torches_placed)} / {torches_limit} [Espaco]", True, (255, 200, 0)), (785, 495))

    pygame.draw.line(screen, (100, 100, 100), (775, 520), (1015, 520), 1)
    screen.blit(font.render(f"Fase {level + 1}", True, (255, 255, 255)), (785, 535))

    screen.blit(font_small.render("WASD/Setas: mover",    True, (120, 120, 120)), (785, 560))
    screen.blit(font_small.render("T: sensor  1/2/3: ord", True, (120, 120, 120)), (785, 575))

    screen.blit(font.render(msg[:18], True, (255, 255, 0)), (785, 600))

    if dialog_active or chest_dialog:
        overlay = pygame.Surface((1024, 640))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (50, 50, 50),    (162, 180, 700, 220))
        pygame.draw.rect(screen, (255, 255, 255), (162, 180, 700, 220), 3)

        if dialog_active:
            if level == 4:
                total_value = sum(item["value"] for item in inventory)
                screen.blit(font.render("Eu vendo uma chave por $50 de valor em itens.", True, (255, 255, 255)), (192, 220))
                screen.blit(font.render(f"Seu saldo atual de troca: ${total_value} / $50",  True, (255, 255, 255)), (192, 260))
            else:
                screen.blit(font.render("Eu poderia fazer uma chave se voce",   True, (255, 255, 255)), (192, 230))
                screen.blit(font.render("tiver a materia prima (Ouro).",         True, (255, 255, 255)), (192, 270))
        else:
            screen.blit(font.render(f"O bau contem: {chest_item}",  True, (255, 255, 255)), (192, 240))
            screen.blit(font.render("Deseja pegar este item?",       True, (255, 255, 255)), (192, 290))

        screen.blit(font.render("[S] Sim", True, (0, 255, 0)),   (192, 330))
        screen.blit(font.render("[N] Nao", True, (255, 100, 100)), (192, 370))

    pygame.display.flip()
