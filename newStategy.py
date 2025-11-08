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

arena = collections.deque([collections.deque([EXPLORED])])

pieces = {
    "start": [0, 0],
    "robo": [0, 0],
}

square_char = WHITE_SQUARE  # Definir automaticamente com base no que o robo está vendo

RIGHT = "d"
LEFT = "a"
UP = "w"
DOWN = "s"

# Estado de limite da arena. False = pode expandir, True = limite ('X') definido.
boundaries_set = {UP: False, DOWN: False, LEFT: False, RIGHT: False}

# Mapeamento do movimento: [dr, dc] (delta row, delta column)
movements = {
    UP: [-1, 0],
    DOWN: [1, 0],
    LEFT: [0, -1],
    RIGHT: [0, 1],
}

# Inicia o código apontando para uma direção (DIREITA) referente a matriz "arena".
direction = RIGHT

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
        pieces_pos[(pos[0], pos[1])] = name

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


# --- Funções de Expansão ---


def adjust_positions(row, col):
    global pieces
    for _, pos in pieces.items():
        pos[0] += row
        pos[1] += col


def expand_arena(expand_key, char_to_fill=NON_EXPLORED):
    """
    Expande a arena na direção da chave (w, s, a, d).
    A nova linha/coluna respeita os limites (X) já marcados nas dimensões cruzadas.
    """
    global arena

    if expand_key in [UP, DOWN]:
        # Expansão Vertical: Adicionando uma LINHA

        # 1. Cria a nova linha baseada no char_to_fill (NON_EXPLORED ou BOUNDARY)
        new_row = [char_to_fill] * len(arena[0])

        # 2. Respeita limites laterais (A e D)
        if boundaries_set[DOWN]:
            new_row[0] = UNVALIABLE
        if boundaries_set[RIGHT]:
            new_row[len(arena[0]) - 1] = UNVALIABLE

        if expand_key == UP:
            arena.appendleft(collections.deque(new_row))  # -> 0(1)
            adjust_positions(1, 0)  # Desce todas as peças

        elif expand_key == DOWN:
            arena.append(collections.deque(new_row))  # Mantém consistência
            # Posições não mudam

    elif expand_key in [LEFT, RIGHT]:
        # Expansão Horizontal: Adicionando uma COLUNA

        # 1. Decide o índice de inserção (0 para 'a', -1 para 'd')
        insert_func = "appendleft" if expand_key == LEFT else "append"

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

        if expand_key == LEFT:
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


def mark_boundary(key):
    """
    Se o robô estiver na última célula da arena na direção 'key',
    adiciona uma linha/coluna de BOUNDARY ('X') e define o limite.
    """
    global boundaries_set

    if not is_on_edge(key):
        messages.append(
            f"⚠️ O robô não está na célula mais externa na direção '{key.upper()}' para marcar um limite."
        )
        return False

    # Se o limite já foi marcado, apenas confirma
    if boundaries_set[key]:
        messages.append(f"❌ O limite '{key.upper()}' já está selado.")
        return False

    # 1. Expande a arena, preenchendo a nova linha/coluna com 'X'
    # Esta expansão agora respeita os limites cruzados!
    expand_arena(key, char_to_fill=UNVALIABLE)

    # 2. Marca o limite como permanente
    boundaries_set[key] = True

    messages.append(
        f"✅ Limite ({UNVALIABLE}) adicionado permanentemente na direção '{key.upper()}'."
    )
    return True


def create_obstacle(key):
    """
    Adiciona Obstaculo na frente do robo
    """

    movement = movements[key]

    new_obs_name = f"obs_{len(pieces)}"  # Cria um nome único
    pieces[new_obs_name] = [
        pieces["robo"][0] + movement[0],
        pieces["robo"][1] + movement[1],
    ]


# --- Loop Principal de Movimento ---


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
        expand_arena(action)

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
    while True:
        clear_screen()
        show_arena()

        command = input("Comando: ").lower().strip()

        if command == "q":
            print("👋 Agente desativado. Até mais!")
            break

        if command in [UP, LEFT, DOWN, RIGHT]:
            update_agent(command)

        elif command == "f":
            mark_boundary(direction)

        elif command == "x":
            create_obstacle(direction)

        elif command:
            print(f"Comando inválido: {command}. Tente novamente.")


# Inicia o programa
if __name__ == "__main__":
    main_loop()
