import pygame
import sys

# Configurações Iniciais - 1024x640
TILE = 64
pygame.init()
screen = pygame.display.set_mode((1024, 640))
pygame.display.set_caption("Caverna do Dragao ")
font = pygame.font.SysFont(None, 32)
font_small = pygame.font.SysFont(None, 20)
clock = pygame.time.Clock()

# Matrizes dos Níveis
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

# --- BANCO DE DADOS DE ITENS ---
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

# ─── Algoritmos de Ordenação ────────────────────────────────────────────────

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

# ─── BFS / Sensor de Rota ───────────────────────────────────────────────────

def run_bfs():

    global pulse_distances
    pulse_distances = {}
    queue   = [(player[0], player[1], 0)]
    visited = {(player[0], player[1])}
    while queue:
        cx, cy, dist = queue.pop(0)
        pulse_distances[(cx, cy)] = dist
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[ny]):
                if grid[ny][nx] not in ("#", "I") and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny, dist + 1))

# ─── Estado dos Baús ────────────────────────────────────────────────────────

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

# ─── Carregamento de Nível ──────────────────────────────────────────────────

def load_level(i):
    global grid, player, msg, msg_timer, dialog_active, inventory
    global pulse_active, pulse_distances, chest_dialog
    grid = [list(r) for r in levels[i]]
    inventory    = []
    msg          = ""
    msg_timer    = 0
    dialog_active = False
    chest_dialog  = False
    pulse_active  = False
    pulse_distances = {}
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c == "P":
                player = [x, y]
                grid[y][x] = "."

def set_msg(text, duration=3000):
    """Define uma mensagem com timer automático (ms)."""
    global msg, msg_timer
    msg       = text
    msg_timer = duration

load_level(level)

# ─── Cores e Renderização ───────────────────────────────────────────────────

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

# ─── Loop Principal ─────────────────────────────────────────────────────────

while True:
    dt = clock.tick(60)   

    # ── Timer de mensagem ──
    if msg_timer > 0:
        msg_timer -= dt
        if msg_timer <= 0:
            msg = ""

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        #  Tela de Vitória 
        if victory:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                level = 0
                victory = False
                game_over = False
                load_level(level)
            continue

        #  Tela de Fim de Jogo 
        if game_over:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                level = 0
                game_over = False
                load_level(level)
            continue

        #  chat do Baú 
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

        # Diálogo de NPC
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
                            set_msg("Chave comprada por $50!")
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

        # Teclas de Jogo
        if e.type == pygame.KEYDOWN:

            # Sensor de Rota (BFS)
            if e.key == pygame.K_t:
                run_bfs()
                pulse_active  = True
                pulse_radius  = 0.0
                pulse_origin  = list(player)
                set_msg("Sensor de Rota ativo!")

            # Ordenação
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

                    has_key = any(item["name"] == "Chave" for item in inventory)
                    if t == "D":
                        if has_key:
                            level += 1
                            if level >= len(levels):
                                victory = True          # NOVO: vitória ao completar todos os níveis
                            else:
                                load_level(level)
                        else:
                            set_msg("Porta Trancada!")

    if victory:
        screen.fill((5, 5, 20))
        lbl1 = font.render("PARABENS! VOCE VENCEU!", True, (255, 215, 0))
        lbl2 = font_small.render("Voce completou todos os 5 niveis!", True, (180, 180, 255))
        lbl3 = font_small.render("Pressione [R] para jogar novamente", True, (200, 200, 200))
        screen.blit(lbl1, (512 - lbl1.get_width() // 2, 260))
        screen.blit(lbl2, (512 - lbl2.get_width() // 2, 310))
        screen.blit(lbl3, (512 - lbl3.get_width() // 2, 350))
        pygame.display.flip()
        continue

    if game_over:
        screen.fill((15, 15, 15))
        lbl_go  = font.render("FIM DE JOGO", True, (255, 215, 0))
        lbl_rst = font_small.render("Pressione [R] para recomecar da primeira fase", True, (200, 200, 200))
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

            draw_tile_detail(screen, c, rx, ry)

            # Onda do sensor BFS
            if pulse_active and (x, y) in pulse_distances:
                if abs(pulse_radius - pulse_distances[(x, y)]) < 0.7:
                    alpha = 1 - abs(pulse_radius - pulse_distances[(x, y)]) / 0.7
                    flash = pygame.Surface((TILE, TILE))
                    flash.fill((0, 255, 80))
                    flash.set_alpha(int(alpha * 180))
                    screen.blit(flash, (rx, ry))

    # Jogador 
    px, py = player[0] * TILE, player[1] * TILE
    pygame.draw.rect(screen, (30, 90, 220), (px + 4, py + 4, TILE - 8, TILE - 8))
    pygame.draw.circle(screen, (140, 180, 255), (px + TILE // 2, py + 16), 8)   # cabeça

    # Inventário
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

    pygame.draw.line(screen, (100, 100, 100), (775, 520), (1015, 520), 1)
    screen.blit(font.render(f"Fase {level + 1}", True, (255, 255, 255)), (785, 535))

    # Controles
    screen.blit(font_small.render("WASD/Setas: mover",   True, (120, 120, 120)), (785, 560))
    screen.blit(font_small.render("T: sensor  1/2/3: ord", True, (120, 120, 120)), (785, 575))

    screen.blit(font.render(msg[:18], True, (255, 255, 0)), (785, 600))

    #Caixas de Diálogo
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
