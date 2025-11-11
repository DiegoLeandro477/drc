import collections  # Importa a biblioteca collections para usar deques.
import random  # Importa a biblioteca random para gerar números e posições aleatórias.
import time
import os

# --- Definição das Constantes e Configurações ---
# Lista dos elementos especiais que devem ser posicionados na matriz.
ELEMENTS_TO_PLACE = [
    ("R", 1),  # Robô (1 instância)
    ("X", 1),  # Obstáculos (2 instâncias)
    ("O", 4),  # Descartes/Colecionáveis (4 instâncias)
    ("F", 1),  # Ponto Final (1 instância)
]

# Caractere de preenchimento padrão para as células vazias.
EXPLORED_CHAR = "."

# Intervalo de dimensões permitidas (linhas min/max, colunas min/max).
MIN_ROWS, MAX_ROWS = 4, 8
MIN_COLS, MAX_COLS = 5, 8

robo = (0, 0)
start = None
direction = "a"
arena = None
# --- FIM das Constantes ---


def generate_random_grid():
    """
    Gera uma matriz (deque de deques) com dimensões aleatórias e
    posiciona os elementos especiais (R, X, O, F) de forma não sobreposta.
    """
    global robo, start

    # 1. Escolhe as dimensões da matriz aleatoriamente dentro dos limites.
    num_rows = random.randint(MIN_ROWS, MAX_ROWS)
    num_cols = random.randint(MIN_COLS, MAX_COLS)

    # Cria uma lista de todas as coordenadas (r, c) possíveis na matriz.
    all_positions = [(r, c) for r in range(num_rows) for c in range(num_cols)]

    # Escolhe um subconjunto de coordenadas para posicionar os elementos.
    # O número total de elementos especiais (1+2+4+1 = 8) deve ser menor
    # que o número total de células (4x5=20 até 8x8=64).
    # Se o número de células for muito pequeno (ex: 4x5=20), a chance de
    # repetição de coordenadas é baixa, mas para garantir exclusividade,
    # usamos random.sample.
    total_elements = sum(count for _, count in ELEMENTS_TO_PLACE)

    # Seleciona 'total_elements' posições únicas e aleatórias.
    selected_positions = random.sample(all_positions, total_elements)

    # Dicionário para mapear as coordenadas selecionadas para o elemento.
    placement_map = {}

    # 2. Mapeia os elementos às posições selecionadas.
    pos_index = 0
    for char, count in ELEMENTS_TO_PLACE:
        for _ in range(count):
            # Associa o caractere à coordenada.
            placement_map[selected_positions[pos_index]] = char
            pos_index += 1

    # 3. Constrói a Matriz de Collections.deque.
    # Inicializa a matriz como um deque vazio.
    matrix = collections.deque()

    # Itera sobre as linhas.
    for r in range(num_rows):
        # Cria a linha atual como um deque vazio.
        row_deque = collections.deque()

        # Itera sobre as colunas.
        for c in range(num_cols):
            # Verifica se a coordenada atual (r, c) está no mapa de posicionamento.
            if (r, c) in placement_map:
                # Se sim, adiciona o caractere especial (R, X, O, ou F).
                char = placement_map[(r, c)]
            else:
                # Se não, adiciona o caractere de preenchimento padrão (.).
                char = EXPLORED_CHAR

            # Adiciona o caractere à linha (deque).
            if char == "R":
                robo = (r, c)
                start = robo
                row_deque.append(EXPLORED_CHAR)
            else:
                row_deque.append(char)

        # Adiciona a linha (deque) à matriz principal (deque).
        matrix.append(row_deque)

    # Retorna a matriz gerada.
    return matrix


def print_matrix():
    """
    Imprime a matriz (deque de deques) de forma formatada.
    """
    # Exibe as dimensões da matriz.
    if not arena:
        print("A arena não foi gerada ainda.")
        return

    num_rows = len(arena)
    num_cols = len(arena[0]) if arena else 0
    print(f"🗺️ Arena Gerada ")

    # Imprime uma linha superior para a borda.
    print("-" * (num_cols * 4 + 1))

    for r in range(num_rows):
        # Itera sobre as colunas da linha atual.
        for c in range(num_cols):

            # 💡 Verifica se a coordenada atual (r, c) é a posição do robô.
            if r == robo[0] and c == robo[1]:
                # Se for, o caractere a ser impresso é 'R'.
                char_to_print = "R"
            else:
                # Caso contrário, pega o caractere original da matriz (., X, O, F).
                char_to_print = arena[r][c]

            # Imprime o caractere formatado.
            print(f"| {char_to_print} ", end="")

        # Imprime o fechamento da linha e quebra de linha.
        print("|")

    # Imprime a linha inferior para a borda.
    print("-" * (num_cols * 4 + 1))


def move_analizy(dir):
    """Calcula a nova posição e lida com a expansão da arena."""
    global arena, robo

    new_pos = robo[0] + dir[0], robo[1] + dir[1]

    # 2. Caso DENTRO DOS LIMITES ATUAIS
    if 0 <= new_pos[0] < len(arena) and 0 <= new_pos[1] < len(arena[0]):
        # ATUALIZA a posição do robo
        if arena[new_pos[0]][new_pos[1]] != "X":
            robo = new_pos
        return arena[new_pos[0]][new_pos[1]]
    return None


def gyroAngle(angle):
    global direction
    direction = angle
    return direction


if __name__ == "__main__":
    arena = generate_random_grid()
    print_matrix()
