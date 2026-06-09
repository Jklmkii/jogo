import pygame
import sys

# Configurações Iniciais - 1024x640
TILE = 64
pygame.init()
screen = pygame.display.set_mode((1024, 640))
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
        "#P..B.....B#",  # Baú 1 [4,1] e Baú 2 [10,1]
        "#..........#",
        "#..B.....B.#",  # Baú 3 [3,3] e Baú 4 [9,3]
        "#..........#",
        "#.....B...N#",  # Baú 5 [6,5] e NPC da Chave [10,5]
        "#........D.#",  # Porta de Saída Final [9,6]
        "############"
    ]
]

level = 0
player = [1, 1]
msg = ""
dialog_active = False
game_over = False  # Estado de Fim de Jogo

pulse_active = False
pulse_radius = 0.0
pulse_origin = [0, 0]
pulse_distances = {}  

# --- BANCO DE DADOS DE ITENS ---
ITEM_DATA = {
    "Chave": {"weight": 1, "rarity": 3, "rarity_name": "Epico", "value": 50},
    "Ossos": {"weight": 2, "rarity": 1, "rarity_name": "Comum", "value": 5},
    "Pedacos de Madeira": {"weight": 5, "rarity": 1, "rarity_name": "Comum", "value": 10},
    "Ouro": {"weight": 10, "rarity": 2, "rarity_name": "Raro", "value": 100},
    "Vidro": {"weight": 3, "rarity": 1, "rarity_name": "Comum", "value": 15}
}

inventory = []
sort_mode = "peso"       
sort_algo = "quicksort"  

def quick_sort(arr, key_func):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if key_func(x) < key_func(pivot)]
    middle = [x for x in arr if key_func(x) == key_func(pivot)]
    right = [x for x in arr if key_func(x) > key_func(pivot)]
    return quick_sort(left, key_func) + middle + quick_sort(right, key_func)

def merge_sort(arr, key_func):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key_func)
    right = merge_sort(arr[mid:], key_func)
    
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key_func(left[i]) <= key_func(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
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

chest_dialog = False
chest_item = ""
chest_x = 0
chest_y = 0

def load_level(i):
    global grid, player, msg, dialog_active, inventory, pulse_active, pulse_distances
    grid = [list(r) for r in levels[i]]
    inventory = []  
    msg = ""
    dialog_active = False
    pulse_active = False 
    pulse_distances = {}

    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c == "P":
                player = [x, y]
                grid[y][x] = "."

load_level(level)

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        
        if game_over:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                level = 0
                game_over = False
                load_level(level)
            continue

        if chest_dialog:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_s:
                    item_properties = ITEM_DATA[chest_item].copy()
                    item_properties["name"] = chest_item
                    inventory.append(item_properties)
                    apply_sorting()  
                    msg = f"{chest_item} coletado(a)!"
                    grid[chest_y][chest_x] = "."
                    chest_dialog = False
                elif e.key == pygame.K_n:
                    msg = "Voce deixou o item no bau."
                    chest_dialog = False
            continue

        if dialog_active:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_s:
                    if level == 4:  # Sistema de Venda da Fase 5
                        total_value = sum(item["value"] for item in inventory)
                        if total_value >= 50:
                            inventory.clear()  
                            key_properties = ITEM_DATA["Chave"].copy()
                            key_properties["name"] = "Chave"
                            inventory.append(key_properties)
                            apply_sorting()
                            msg = "Chave comprada por 50!"
                        else:
                            msg = f"Falta valor! Você tem ${total_value}/50"
                    else:  
                        gold_item = next((item for item in inventory if item["name"] == "Ouro"), None)
                        if gold_item:
                            inventory.remove(gold_item)
                            key_properties = ITEM_DATA["Chave"].copy()
                            key_properties["name"] = "Chave"
                            inventory.append(key_properties)
                            apply_sorting()
                            msg = "NPC criou uma chave!"
                        else:
                            msg = "Voce nao possui ouro."
                    dialog_active = False
                elif e.key == pygame.K_n:
                    msg = "Talvez outra hora."
                    dialog_active = False
            continue

        if e.type == pygame.KEYDOWN:
            
            if e.key == pygame.K_t:
                pulse_active = True
                pulse_radius = 0.0
                pulse_origin = list(player)
                pulse_distances = {}
                
                queue = [(player[0], player[1], 0)]
                visited = {(player[0], player[1])}
                
                while queue:
                    cx, cy, dist = queue.pop(0)
                    pulse_distances[(cx, cy)] = dist
                    
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= ny < len(grid) and 0 <= nx < len(grid[ny]):
                            if grid[ny][nx] != "#" and grid[ny][nx] != "I" and (nx, ny) not in visited:
                                visited.add((nx, ny))
                                queue.append((nx, ny, dist + 1))
                msg = "Sensor de Rota ativo!"

            # Modos de Ordenação
            if e.key == pygame.K_1:
                sort_mode, sort_algo = "peso", "quicksort"
                apply_sorting()
                msg = "Ordenado: Peso"
            elif e.key == pygame.K_2:
                sort_mode, sort_algo = "raridade", "mergesort"
                apply_sorting()
                msg = "Ordenado: Raridade"
            elif e.key == pygame.K_3:
                sort_mode, sort_algo = "valor", "heapsort"
                apply_sorting()
                msg = "Ordenado: Valor"

            dx, dy = 0, 0
            if e.key == pygame.K_w: dy = -1
            if e.key == pygame.K_s: dy = 1
            if e.key == pygame.K_a: dx = -1
            if e.key == pygame.K_d: dx = 1

            nx = player[0] + dx
            ny = player[1] + dy

            if 0 <= ny < len(grid) and 0 <= nx < len(grid[ny]):
                t = grid[ny][nx]
                if t != "#" and t != "I":
                    player = [nx, ny]

                    if t == "K":
                        key_properties = ITEM_DATA["Chave"].copy()
                        key_properties["name"] = "Chave"
                        inventory.append(key_properties)
                        apply_sorting()
                        grid[ny][nx] = "."
                        msg = "Chave coletada!"

                    if t == "B":
                        chest_dialog = True
                        if level == 1:
                            if nx == 3: chest_item = "Chave"
                            elif nx == 5: chest_item = "Ossos"
                            elif nx == 7: chest_item = "Pedacos de Madeira"
                        elif level == 3: 
                            if nx == 10 and ny == 1: chest_item = "Vidro"
                            elif nx == 1 and ny == 3: chest_item = "Ossos"
                            elif nx == 9 and ny == 5: chest_item = "Pedacos de Madeira"
                            elif nx == 1 and ny == 7: chest_item = "Chave"
                        elif level == 4:  
                            if nx == 4 and ny == 1: chest_item = "Vidro"                
                            elif nx == 10 and ny == 1: chest_item = "Vidro"             
                            elif nx == 3 and ny == 3: chest_item = "Pedacos de Madeira" 
                            elif nx == 9 and ny == 3: chest_item = "Ossos"              
                            elif nx == 6 and ny == 5: chest_item = "Ossos"              
                        else:
                            chest_item = "Ouro"
                        chest_x, chest_y = nx, ny

                    if t == "N":
                        dialog_active = True

                    
                    has_key = any(item["name"] == "Chave" for item in inventory)
                    if t == "D":
                        if has_key:
                            level += 1
                            if level >= len(levels):
                                game_over = True  
                            else:
                                load_level(level)
                        else:
                            msg = "Porta Trancada!"

    # tela de Fim de Jogo
    if game_over:
        screen.fill((15, 15, 15))
        lbl_gameover = font.render("FIM DE JOGO", True, (255, 215, 0))
        lbl_restart = font_small.render("Pressione [R] para recomecar da primeira fase", True, (200, 200, 200))
        screen.blit(lbl_gameover, (512 - lbl_gameover.get_width() // 2, 280))
        screen.blit(lbl_restart, (512 - lbl_restart.get_width() // 2, 340))
        pygame.display.flip()
        clock.tick(60)
        continue

    # radar
    if pulse_active:
        pulse_radius += 0.08 
        max_dist = max(pulse_distances.values()) if pulse_distances else 0
        if pulse_radius > max_dist + 1: 
            pulse_active = False

    screen.fill((20, 20, 20))

    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            r = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
            pygame.draw.rect(screen, (60, 60, 60), r, 1)
            
            colors = {
                "#": (120, 120, 120), 
                "K": (255, 128, 0),   
                "D": (255, 215, 0),   
                "B": (160, 82, 45), 
                "N": (0, 180, 255), 
                ".": (30, 30, 30),
                "I": (30, 30, 30) 
            }
            pygame.draw.rect(screen, colors.get(c, (30, 30, 30)), r)

            if pulse_active and (x, y) in pulse_distances:
                if int(pulse_radius) == pulse_distances[(x, y)]:
                    flash_surf = pygame.Surface((TILE, TILE))
                    flash_surf.fill((0, 255, 0))  
                    flash_surf.set_alpha(180)     
                    screen.blit(flash_surf, (x * TILE, y * TILE))

    pygame.draw.rect(screen, (0, 102, 255), (player[0] * TILE, player[1] * TILE, TILE, TILE))

    pygame.draw.rect(screen, (40, 40, 40), (768, 0, 256, 640))
    screen.blit(font.render("Inventario", True, (255, 255, 255)), (785, 15))
    screen.blit(font_small.render(f"Filtro: {sort_mode.upper()}", True, (0, 255, 255)), (785, 45))
    screen.blit(font_small.render(f"Algo: {sort_algo.upper()}", True, (200, 200, 200)), (785, 65))
    pygame.draw.line(screen, (100, 100, 100), (775, 85), (1015, 85), 1)

    for idx, item in enumerate(inventory):
        name_surface = font_small.render(f"{item['name']}", True, (255, 255, 255))
        screen.blit(name_surface, (785, 95 + idx * 45))
        details = f"{item['weight']}kg | {item['rarity_name']} | ${item['value']}"
        details_surface = font_small.render(details, True, (180, 180, 180))
        screen.blit(details_surface, (785, 112 + idx * 45))

    pygame.draw.line(screen, (100, 100, 100), (775, 520), (1015, 520), 1)
    screen.blit(font.render(f"Fase {level+1}", True, (255, 255, 255)), (785, 535))
    screen.blit(font.render(msg[:18], True, (255, 255, 0)), (785, 580))

    # Caixas de Diálogo
    if dialog_active or chest_dialog:
        overlay = pygame.Surface((1024, 640)); overlay.set_alpha(180); overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (50, 50, 50), (162, 180, 700, 220))
        pygame.draw.rect(screen, (255, 255, 255), (162, 180, 700, 220), 3)

        if dialog_active:
            if level == 4: 
                current_total = sum(item["value"] for item in inventory)
                screen.blit(font.render("Eu vendo uma chave por $50 de valor em itens.", True, (255, 255, 255)), (192, 230))
                screen.blit(font.render(f"Seu saldo atual de troca: ${current_total} / $50", True, (255, 255, 255)), (192, 270))
            else:
                screen.blit(font.render("Eu poderia fazer uma chave se voce", True, (255, 255, 255)), (192, 230))
                screen.blit(font.render("tiver a materia prima (Ouro).", True, (255, 255, 255)), (192, 270))
        else:
            screen.blit(font.render(f"O bau contem: {chest_item}", True, (255, 255, 255)), (192, 240))
            screen.blit(font.render("Deseja pegar este item?", True, (255, 255, 255)), (192, 290))

        screen.blit(font.render("[S] Sim", True, (0, 255, 0)), (192, 330))
        screen.blit(font.render("[N] Nao", True, (255, 100, 100)), (192, 370))

    pygame.display.flip()
    clock.tick(60)