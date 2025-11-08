import time

# =-=-=-=-=-=-=-=-=
import os
import collections

messages = []

NON_EXPLORED = "?"
EXPLORED = "."
ROBO = "R"
UNVALIABLE = "X"
START = "★"
BLACK_SQUARE = "■"
WHITE_SQUARE = "□"
DISCARD = "O"

arena = collections.deque([collections.deque([EXPLORED])])

pieces = {
    "start": [0, 0],
    "discards": collections.deque(),
    "robo": [0, 0],
}


square_char = WHITE_SQUARE  # Definir automaticamente com base no que o robo está vendo

RIGHT = "d"
LEFT = "a"
UP = "w"
DOWN = "s"

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


def clear_screen():
    """Limpa o console para uma exibição mais limpa."""
    os.system("cls" if os.name == "nt" else "clear")


def show_arena():
    """Imprime a arena no console com bordas."""
    global messages
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
                pieces_pos[(dis_pos[0], dis_pos[1])] = "discard"

    for row in range(len(arena)):
        for col in range(len(arena[0])):
            content = arena[row][col]
            if (row, col) in pieces_pos:
                piece_name = pieces_pos[(row, col)]
                if piece_name == "robo":
                    content = ROBO
                elif piece_name == "start":
                    content = START
                elif "obs" in piece_name:
                    content = UNVALIABLE
                elif "discard" in piece_name:
                    content = DISCARD
            print(f"| {content} ", end="")
        print("|")

    print("-" * total_width)

    print(f"🤖 Posição: ({pieces['robo'][0]}, {pieces['robo'][1]}), dir:{direction}")
    print(
        f"Bordas Encontradas(X): W:{boundaries_set[UP]}, S:{boundaries_set[DOWN]}, A:{boundaries_set[LEFT]}, D:{boundaries_set[RIGHT]}"
    )
    print(f"Quadrado: {square_char}")
    if messages:
        print(f"Msg:{messages}")
        messages = []

    print("\nComandos: [w/a/s/d] Mover, [f] Marcar Fim, [x] Marcar obstaculo, [q] Sair")


def add_discard():
    global messages, pieces

    if pieces["robo"] not in [tuple(p) for p in pieces["discards"]]:
        # Adiciona a posição: Usa .append() para colocar a nova coordenada
        pieces["discards"].append([pieces["robo"][0], pieces["robo"][1]])
        print(pieces["discards"])

        messages.append(
            f"📦 Área de descarte encontrada e adicionada em {pieces['robo']}."
        )
    else:
        messages.append(f"🚫 Área de descarte em {pieces['robo']} já registrada.")


# --- Funções de Expansão ---


def adjust_positions(row, col):
    global pieces

    for _, pos in pieces.items():
        if isinstance(pos, list) or isinstance(pos, tuple):

            pos[0] += row
            pos[1] += col
        elif isinstance(pos, collections.deque):
            for discard_pos in pos:
                discard_pos[0] += row
                discard_pos[1] += col


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
        if boundaries_set[DOWN]:
            new_row[0] = UNVALIABLE
        if boundaries_set[RIGHT]:
            new_row[len(arena[0]) - 1] = UNVALIABLE

        if direction == UP:
            arena.appendleft(collections.deque(new_row))  # -> 0(1)
            adjust_positions(1, 0)  # Desce todas as peças

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
            adjust_positions(0, 1)  # Move todas as peças para direita


# --- Funções de Limite ---


def is_on_edge(current_key):
    """Verifica se o robô está na borda mais externa na direção de 'current_key'."""
    robo_r, robo_c = pieces["robo"]
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
    global pieces, arena

    movement = movements[direction]

    new_r = pieces["robo"][0] + movement[0]
    new_c = pieces["robo"][1] + movement[1]

    if not (0 <= new_r < len(arena) and 0 <= new_c < len(arena[0])):
        expand_arena()

    new_obs_name = f"obs_{len(pieces)}"  # Cria um nome único
    pieces[new_obs_name] = [
        pieces["robo"][0] + movement[0],
        pieces["robo"][1] + movement[1],
    ]


# Calcular a heuristica das celulas
def heuristics(_start, _end):
    return abs(_start[0] - _end[0]) + abs(_start[1] - _end[1])


# A_estrela para encontrar caminhos dentro da arena
def a_stars(destiny):
    if isinstance(destiny, list):
        destiny = tuple(destiny)

    start_pos = tuple(pieces["robo"])
    paths_discovered = []
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
            ) and arena[new_position[0]][new_position[1]] not in [UNVALIABLE]:
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
    start_pos = tuple(pieces["robo"])
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

                if cell_content != UNVALIABLE and next_pos not in visited:
                    visited.add(next_pos)
                    queue.append(next_pos)

    # Se a fila esvaziar e o "?" não for encontrado
    return None


# --- funções de Movimento ---


def move_position(pos):
    global direction
    # Verifica se a direção está apontada para a posição, se não aponta a direção.
    # move o robo para a posição
    movement = (pos[0] - pieces["robo"][0], pos[1] - pieces["robo"][1])
    if movement not in directions:
        return False

    if directions[movement] != direction:
        direction = directions[movement]

    update_agent(directions[movement])


def walk(destiny):
    clear_screen()
    global steps_cont
    if pieces["robo"] == destiny:
        return
    path = a_stars(destiny)
    if path:
        path.pop(0)
        for position in path:
            clear_screen()
            show_arena()
            time.sleep(0.5)
            if not move_position(position):
                walk(destiny)
                break


def update_agent(action):
    """Calcula a nova posição e lida com a expansão da arena."""
    global arena, pieces, direction, square_char

    if action not in movements:
        return

    # Verifica se o movimento é andar ou mudar a direção
    if action != direction:
        direction = action
        return

    movement = movements[action]

    new_pos = pieces["robo"][0] + movement[0], pieces["robo"][1] + movement[1]

    # 2. Caso DENTRO DOS LIMITES ATUAIS
    if 0 <= new_pos[0] < len(arena) and 0 <= new_pos[1] < len(arena[0]):
        # ATUALIZA a posição do robo
        pieces["robo"][0], pieces["robo"][1] = new_pos

    # 3. Caso FORA DOS LIMITES (Expansão Necessária)
    else:
        # Expansão da arena
        # Chama a expansão inteligente que respeita os limites cruzados
        expand_arena()

        # Determina a nova posição do robô na borda recém-criada
        if action == UP:
            pieces["robo"][0] = 0
        elif action == DOWN:
            pieces["robo"][0] = len(arena) - 1
        elif action == LEFT:
            pieces["robo"][1] = 0
        elif action == RIGHT:
            pieces["robo"][1] = len(arena[0]) - 1

    arena[pieces["robo"][0]][pieces["robo"][1]] = EXPLORED
    square_char = BLACK_SQUARE if square_char == WHITE_SQUARE else WHITE_SQUARE


# --- Função Principal ---


def main_loop():
    global hasCubes
    while True:
        clear_screen()
        show_arena()

        # Verifica se já pegou os cubos
        if hasCubes:
            # Verifica se existe alguma área de descarte
            if pieces["discards"]:
                pos = pieces["discards"][0]
                walk(pos)
                pieces["discards"].popleft()
                continue
            else:
                hasCubes = False
        else:
            # Procurar o ? mais perto do robô e printar a pos dele na tela
            closest_unexplored = find_closest_unexplored()
            if closest_unexplored:
                messages.append(f"🔍 Próximo alvo: {closest_unexplored}")

                walk(closest_unexplored)
                continue
            else:
                messages.append("🎉 Nenhuma célula '?' encontrada.")
                # Começar a procurar as laterais para expandir a arena
                for dir, movement in movements.items():
                    if not boundaries_set[dir]:
                        # O robo tem que se direcionar ate essa borda da arena e expandir
                        ...

        command = input("Comando: ").lower().strip()

        if command == "q":
            print("👋 Agente desativado. Até mais!")
            break

        if command in [UP, LEFT, DOWN, RIGHT]:
            update_agent(command)

        elif command == "f":
            mark_boundary()

        elif command == "c":
            add_discard()
        elif command == "x":
            add_obstracle()
        elif command == "cubes":
            hasCubes = True

        elif command:
            print(f"Comando inválido: {command}. Tente novamente.")


# Inicia o programa
if __name__ == "__main__":
    main_loop()
