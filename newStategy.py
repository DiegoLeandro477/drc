import time

# =-=-=-=-=-=-=-=-=
import os
import collections
import bot

NON_EXPLORED = "?"
EXPLORED = "."
ROBO = "R"
UNVALIABLE = "▣"
OBSTACLE = "X"
START = "★"
BLACK_SQUARE = "■"
WHITE_SQUARE = "□"
DISCARD = "O"
PHARMACY = "F"
timer = 0.1

RIGHT = "d"
LEFT = "a"
UP = "w"
DOWN = "s"

arena = collections.deque([collections.deque([EXPLORED])])
messages = []

pieces = {
    START: [0, 0],
    DISCARD: collections.deque(),
    OBSTACLE: collections.deque(),
    ROBO: [0, 0],
}

square_char = WHITE_SQUARE  # Definir automaticamente com base no que o robo está vendo


# Estado de limite da arena. False = pode expandir, True = limite ('X') definido.
boundaries_set = {
    UP: False,
    DOWN: False,
    LEFT: False,
    RIGHT: False,
}

# Mapeamento do movimento: [dr, dc] (delta row, delta column)
movements = {
    UP: [-1, 0],
    DOWN: [1, 0],
    LEFT: [0, -1],
    RIGHT: [0, 1],
}

directions = {
    (-1, 0): UP,
    (1, 0): DOWN,
    (0, -1): LEFT,
    (0, 1): RIGHT,
}

# Inicia o código apontando para uma direção (DIREITA) referente a matriz "arena".
direction = RIGHT
hasCubes = False

# --- FUNÇÕES DE EXIBIÇÃO ---


def reset_simulation():
    global arena, messages, pieces, square_char, boundaries_set
    arena = collections.deque([collections.deque([EXPLORED])])
    messages = []

    pieces = {
        START: [0, 0],
        DISCARD: collections.deque(),
        OBSTACLE: collections.deque(),
        ROBO: [0, 0],
    }

    square_char = (
        WHITE_SQUARE  # Definir automaticamente com base no que o robo está vendo
    )

    # Estado de limite da arena. False = pode expandir, True = limite ('X') definido.
    boundaries_set = {
        UP: False,
        DOWN: False,
        LEFT: False,
        RIGHT: False,
    }


def clear_screen():
    """Limpa o console para uma exibição mais limpa."""
    os.system("cls" if os.name == "nt" else "clear")


def debug(txt, timer):
    print(f"debug[{timer}s]: {txt}")
    time.sleep(timer)


def show_arena(path=[]):
    """Imprime a arena no console com bordas."""
    global messages
    clear_screen()

    bot.print_matrix()

    print("🗺️ Arena:")
    COL_WIDTH = 4
    total_width = len(arena[0]) * COL_WIDTH + 1

    print("-" * total_width)

    # Inverte o dicionário de peças [nome:valor para valor:nome]
    pieces_pos = {}
    for name, pos in pieces.items():
        # 💡 ADIÇÃO DE FILTRO:
        # Garante que 'pos' seja uma lista/tupla de coordenadas [r, c].
        # Pula itens que são listas de posições (como 'discards', que é um deque)
        if isinstance(pos, list) or isinstance(pos, tuple):
            # O acesso pos[0] e pos[1] agora é seguro, pois 'pos' é uma coordenada válida.
            pieces_pos[(pos[0], pos[1])] = name

        elif isinstance(pos, collections.deque):
            for dis_pos in pos:
                pieces_pos[(dis_pos[0], dis_pos[1])] = f"{name}_{len(pieces_pos)}"

    for row in range(len(arena)):
        for col in range(len(arena[0])):
            content = arena[row][col]
            if (row, col) in pieces_pos:
                piece_name = pieces_pos[(row, col)]
                if piece_name == ROBO:
                    content = ROBO
                elif (row, col) in path:
                    content = "$"
                elif piece_name == START:
                    content = START
                elif OBSTACLE in piece_name:
                    content = OBSTACLE
                elif DISCARD in piece_name:
                    content = DISCARD
            print(f"| {content} ", end="")
        print("|")

    print("-" * total_width)
    for i in messages:
        print(i)

    messages = []

    time.sleep(timer)


def add_discard():
    global pieces

    if pieces[ROBO] not in [tuple(p) for p in pieces[DISCARD]]:
        # Adiciona a posição: Usa .append() para colocar a nova coordenada
        pieces[DISCARD].append([pieces[ROBO][0], pieces[ROBO][1]])
        print(pieces[DISCARD])


def add_pharmacy():
    """
    Adiciona Obstaculo na frente do robo
    """
    global pieces, arena

    movement = movements[direction]

    new_r = pieces[ROBO][0] + movement[0]
    new_c = pieces[ROBO][1] + movement[1]

    if not (0 <= new_r < len(arena) and 0 <= new_c < len(arena[0])):
        expand_arena()

    new_obs_name = PHARMACY
    pieces[new_obs_name] = [pieces[ROBO][0], pieces[ROBO][1]]


# --- Funções de Expansão ---


def adjust_positions(movement):
    global pieces

    for _, pos in pieces.items():
        if isinstance(pos, list) or isinstance(pos, tuple):

            pos[0] += movement[0]
            pos[1] += movement[1]
        elif isinstance(pos, collections.deque):
            for discard_pos in pos:
                discard_pos[0] += movement[0]
                discard_pos[1] += movement[1]


def expand_arena(char_to_fill=NON_EXPLORED):
    """
    Expande a arena na direção da chave (w, s, a, d).
    A nova linha/coluna respeita os limites (X) já marcados nas dimensões cruzadas.
    """
    global arena

    if direction in [UP, DOWN]:
        # Expansão Vertical: Adicionando uma LINHA

        # 1. Cria a nova linha baseada no char_to_fill (NON_EXPLORED ou BOUNDARY)
        new_row = [char_to_fill] * len(arena[0])

        # 2. Respeita limites laterais (A e D)
        if boundaries_set[LEFT]:
            new_row[0] = UNVALIABLE
        if boundaries_set[RIGHT]:
            new_row[len(arena[0]) - 1] = UNVALIABLE

        if direction == UP:
            arena.appendleft(collections.deque(new_row))  # -> 0(1)
            adjust_positions(movements[DOWN])  # Desce todas as peças

        elif direction == DOWN:
            arena.append(collections.deque(new_row))  # Mantém consistência
            # Posições não mudam

    elif direction in [LEFT, RIGHT]:
        # Expansão Horizontal: Adicionando uma COLUNA

        # 1. Decide o índice de inserção (0 para 'a', -1 para 'd')
        insert_func = "appendleft" if direction == LEFT else "append"

        for r in range(len(arena)):
            # 2. Caractere base da nova célula
            new_char = char_to_fill

            # 3. Respeita limites superior (W) e inferior (S)
            if r == 0 and boundaries_set[UP]:
                new_char = UNVALIABLE
            elif r == len(arena) - 1 and boundaries_set[DOWN]:
                new_char = UNVALIABLE

            # Chama a função 0(1) (appendleft ou append)
            getattr(arena[r], insert_func)(new_char)

        if direction == LEFT:
            adjust_positions(movements[RIGHT])  # Move todas as peças para direita


# --- Funções de Limite ---


def is_on_edge(current_key):
    """Verifica se o robô está na borda mais externa na direção de 'current_key'."""
    robo_r, robo_c = pieces[ROBO]
    rows = len(arena)
    cols = len(arena[0])

    if current_key == UP:
        return robo_r == 0
    elif current_key == DOWN:
        return robo_r == rows - 1
    elif current_key == LEFT:
        return robo_c == 0
    elif current_key == RIGHT:
        return robo_c == cols - 1
    return False


def mark_boundary():
    """
    Se o robô estiver na última célula da arena na direção 'key',
    adiciona uma linha/coluna de BOUNDARY ('X') e define o limite.
    """
    global boundaries_set

    if not is_on_edge(direction):
        messages.append(
            f"⚠️ O robô não está na célula mais externa na direção '{direction.upper()}' para marcar um limite."
        )
        return False

    # Se o limite já foi marcado, apenas confirma
    if boundaries_set[direction]:
        messages.append(f"❌ O limite '{direction.upper()}' já está selado.")
        return False

    # 1. Expande a arena, preenchendo a nova linha/coluna com 'X'
    # Esta expansão agora respeita os limites cruzados!
    expand_arena(char_to_fill=UNVALIABLE)

    # 2. Marca o limite como permanente
    boundaries_set[direction] = True

    messages.append(
        f"✅ Limite ({UNVALIABLE}) adicionado permanentemente na direção '{direction.upper()}'."
    )
    return True


def add_obstracle():
    """
    Adiciona Obstaculo na frente do robo
    """
    global pieces

    pos = (
        pieces[ROBO][0] + movements[direction][0],
        pieces[ROBO][1] + movements[direction][1],
    )

    pieces[OBSTACLE].append([pos[0], pos[1]])
    debug(f"obst:{pieces[OBSTACLE]}", 5)


# Calcular a heuristica das celulas
def heuristics(_start, _end):
    return abs(_start[0] - _end[0]) + abs(_start[1] - _end[1])


# A_estrela para encontrar caminhos dentro da arena
def a_stars(destiny):
    if isinstance(destiny, list):
        destiny = tuple(destiny)

    start_pos = tuple(pieces[ROBO])
    paths_discovered = []
    obstacles = {tuple(obs_pos) for obs_pos in pieces[OBSTACLE]}
    if not start_pos:
        return None
    paths_discovered.append((0, start_pos))
    cost = {start_pos: 0}
    predecessor = {start_pos: None}
    while paths_discovered:
        paths_discovered.sort()
        current_cost, current_position = paths_discovered.pop(0)
        if current_position == destiny:
            path = []
            while current_position:
                path.append(current_position)
                current_position = predecessor[current_position]
            return path[::-1]
        for _, movement in movements.items():
            new_position = (
                current_position[0] + movement[0],
                current_position[1] + movement[1],
            )
            new_cost = current_cost + 1
            if (
                0 <= new_position[0] < len(arena)
                and 0 <= new_position[1] < len(arena[0])
            ) and new_position not in obstacles:
                if new_position not in cost or new_cost < cost[new_position]:
                    cost[new_position] = new_cost
                    priority = new_cost + heuristics(new_position, destiny)
                    paths_discovered.append((priority, new_position))
                    predecessor[new_position] = current_position
    return None


def find_closest_unexplored():
    """
    Usa Busca em Largura (BFS) para encontrar a coordenada (r,c) da célula NÂO EXPLORADA (?) mais próxima do robo.
    """
    global arena, pieces

    # 1. Inicializa a fila de busca (BFS)
    start_pos = tuple(pieces[ROBO])
    queue = collections.deque([start_pos])

    # Conjunto para rastrear posições já visitadas para evitar loops
    visited = {start_pos}

    # Movimentos possíveis (dr, cr)
    movements_list = list(movements.values())

    # Executa a Busca em Largura
    while queue:
        current_r, current_c = queue.popleft()  # Pega a próxima posição mais próxima

        # Verifica se esta célula é o nosso alvo "?"
        if arena[current_r][current_c] == NON_EXPLORED:
            return (current_r, current_c)

        # Explora vizinhos
        for dr, dc in movements_list:
            next_r, next_c = current_r + dr, current_c + dc

            # Checa se o vizinho está dentro dos limites da arena
            if 0 <= next_r < len(arena) and 0 <= next_c < len(arena[0]):
                # Checa se a célula não é um obstáculo e não foi visitada
                cell_content = arena[next_r][next_c]
                next_pos = (next_r, next_c)

                if cell_content != OBSTACLE and next_pos not in visited:
                    visited.add(next_pos)
                    queue.append(next_pos)

    # Se a fila esvaziar e o "?" não for encontrado
    return None


def get_closest_edge_target(start_pos, direction_key):
    """
    Econtra o alvo acessível (não "X") mais próximo em uma borda
    """
    max_r = len(arena) - 1  # índice da última linha
    max_c = len(arena[0]) - 1  # índice da última coluna
    robo_r, robo_c = start_pos  # Posição inicial do robô

    primary_targey = None
    search_axis = None  # "row" (procura cima/baixo) ou "col" (direita/esquerda)

    if direction_key == UP:
        primary_targey = (0, robo_c)
        search_axis = "col"

    elif direction_key == DOWN:
        primary_targey = (max_r, robo_c)
        search_axis = "col"

    elif direction_key == LEFT:
        primary_targey = (robo_r, 0)
        search_axis = "row"

    elif direction_key == RIGHT:
        primary_targey = (robo_r, max_c)
        search_axis = "row"

    else:
        return None  # Direção inválida

    # Pega as coordenadas do alvo primeiro

    pr, pc = primary_targey

    if (0 <= pr <= max_r and 0 <= pc <= max_c) and arena[pr][pc] != OBSTACLE:
        return primary_targey

    offset = 1

    while True:
        # Celulas a checar nesse offset
        check_cells = []

        if search_axis == "col":
            check_cells.append((pr, pc - offset))
            check_cells.append((pr, pc + offset))

        elif search_axis == "row":
            check_cells.append((pr - offset, pc))
            check_cells.append((pr + offset, pc))

        cells_were_in_bounds = False

        for r, c in check_cells:

            if 0 <= r <= max_r and 0 <= c <= max_c:
                cells_were_in_bounds = True

                if arena[r][c] != OBSTACLE:
                    return (r, c)

        if not cells_were_in_bounds:
            return None

        offset += 1


def find_and_expand_closest_boundary():
    """
    Executa quando não há "?".
    """

    global arena, pieces, messages, direction
    # obtém a posição atual do robô (linha, coluna)

    avaliable_directions = []

    for dir_key in movements.keys():
        if not boundaries_set[dir_key]:
            avaliable_directions.append(dir_key)

    if not avaliable_directions:
        return None

    available_edges = []

    for dir_key in avaliable_directions:
        target_pos = get_closest_edge_target(pieces[ROBO], dir_key)

        if target_pos:
            dist = heuristics(pieces[ROBO], target_pos)
            available_edges.append((dist, dir_key, target_pos))

    if not available_edges:
        return None

    available_edges.sort()

    dist, target_dir, target_pos = available_edges[0]

    # Retorna a direção e a posição-alvo
    return (target_dir, target_pos)


# --- funções de Movimento ---


def move_position(pos):
    global direction
    # Verifica se a direção está apontada para a posição, se não aponta a direção.
    # move o robo para a posição
    movement = (pos[0] - pieces[ROBO][0], pos[1] - pieces[ROBO][1])
    if movement not in directions:
        return False

    direction = bot.gyroAngle(directions[movement])

    zone = bot.move_analizy(movements[direction])
    if zone:
        update_agent(zone)
        return True
    return False


def walk(destiny):
    global steps_cont

    max_recalculations = 3
    recalculations_count = 0

    while tuple(pieces[ROBO]) != destiny and recalculations_count < max_recalculations:
        path = a_stars(destiny)

        if not path or len(path) <= 1:
            break

        movement_failed = False
        path.pop(0)
        for position in path:
            reslt = move_position(position)
            show_arena(path)
            if not reslt:
                movement_failed = True
                break
        if movement_failed:
            recalculations_count += 1

    return True if tuple(pieces[ROBO]) == destiny else False


def update_agent(zone):
    """Calcula a nova posição e lida com a expansão da arena."""
    global arena, pieces, square_char, hasCubes

    if direction not in movements:
        return

    movement = movements[direction]

    new_pos = pieces[ROBO][0] + movement[0], pieces[ROBO][1] + movement[1]

    # 2. Caso DENTRO DOS LIMITES ATUAIS
    if 0 <= new_pos[0] < len(arena) and 0 <= new_pos[1] < len(arena[0]):
        # ATUALIZA a posição do robo

        if zone != OBSTACLE:
            pieces[ROBO][0], pieces[ROBO][1] = new_pos

    # 3. Caso FORA DOS LIMITES (Expansão Necessária)
    else:
        # Expansão da arena
        # Chama a expansão inteligente que respeita os limites cruzados
        expand_arena()

        # Determina a nova posição do robô na borda recém-criada
        if direction == UP:
            pieces[ROBO][0] = 0
        elif direction == DOWN:
            pieces[ROBO][0] = len(arena) - 1
        elif direction == LEFT:
            pieces[ROBO][1] = 0
        elif direction == RIGHT:
            pieces[ROBO][1] = len(arena[0]) - 1
    arena[pieces[ROBO][0]][pieces[ROBO][1]] = EXPLORED

    square_char = BLACK_SQUARE if square_char == WHITE_SQUARE else WHITE_SQUARE

    if zone == OBSTACLE:
        add_obstracle()
    elif zone == DISCARD:
        add_discard()
    elif zone == PHARMACY:
        hasCubes = True
        arena[pieces[ROBO][0]][pieces[ROBO][1]] = PHARMACY


# --- Função Principal ---


def main_loop():
    global hasCubes, direction
    while True:
        show_arena()

        # Verifica se já pegou os cubos
        if hasCubes:
            # Verifica se existe alguma área de descarte
            if pieces[DISCARD]:
                # pos = pieces[DISCARD][0]
                # walk(pos)
                # # descarta cubo  <<<<<<<<<<<<<<<<<<<<<<<<<<<
                # pieces[DISCARD].popleft()
                # new_obs_name = f"{OBSTACLE}_{len(pieces)}"  # Cria um nome único
                # pieces[new_obs_name] = [
                #     pieces[ROBO][0],
                #     pieces[ROBO][1],
                # ]
                # continue
                ...

        # Procurar o ? mais perto do robô e printar a pos dele na tela
        closest_unexplored = find_closest_unexplored()
        if closest_unexplored:
            path_success = walk(closest_unexplored)

            if path_success:
                continue
        else:

            boundarie = find_and_expand_closest_boundary()

            if boundarie:
                walk(boundarie[1])
                direction = bot.gyroAngle(boundarie[0])

                zone = bot.move_analizy(movements[direction])
                if zone:
                    update_agent(zone)
                else:
                    mark_boundary()
                continue
            else:
                print(f"Ponto inicial (mapa arenas): {bot.start}")
                print(f"finalizou a busca.. voltando ao ponto inicial{pieces[START]}")
                walk(pieces[START])
                # Se 'expansion_happened' for False, significa que não há '?'
                # E também não há bordas livres para expandir. A exploração terminou.
                show_arena()
                print("\n======================================")
                print("🎉 EXPLORAÇÃO CONCLUÍDA! 🎉")
                print("Nenhum '?' restante e todas as bordas estão seladas.")
                print("============================= =========")
                break  # Encerra o main_loop (e o programa)


# Inicia o programa
if __name__ == "__main__":
    for i in range(1):
        reset_simulation()
        bot.arena = bot.generate_random_grid()
        show_arena()
        main_loop()
