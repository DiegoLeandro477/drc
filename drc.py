from hub import button, light, light_matrix, motion_sensor, port, sound
import motor, runloop, motor_pair, color_sensor, color

# Aumentando o volume do brick
sound.volume(100)

# Definição dos pares dos motores de movimento
motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
# Definição dos pares de motores dos atuadores
motor_pair.pair(motor_pair.PAIR_2, port.C, port.D)

# Definição dos sensores de Cor
colorSensor = [color_sensor.color(port.E), color_sensor.color(port.F)]

# Matríz de movimentos e converções
m_hour = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # [cima, direita, baixo, esquerda]
movements = m_hour
# Converções entre angulo e movimento
ref_m = {
    -900: movements[2],
    0: movements[1],
    900: movements[0],
    1800: movements[3],
    movements[0]: 900,
    movements[1]: 0,
    movements[2]: -900,
    movements[3]: 1800,
}
# Converções opostas dos movimentos
opposite = {
    movements[0]: movements[2],
    movements[2]: movements[0],
    movements[1]: movements[3],
    movements[3]: movements[1],
}
# Converção das zonas para Caracteres        G
ref_zone = {
    0: "?",
    1: "O",
    2: "O",
    3: "F",
    4: "G",
    5: "G",
    6: "G",
    7: "X",
    8: "O",
    9: "O",
    10: " ",
    -1: "?",
}
# Criação do mapa da area de prova
arena = [
    ["?", "?", "?", "?", "?", "?"],
    ["?", "?", "?", "?", "?", "?"],  #        cima [900]
    ["?", "?", "?", "?", "?", "?"],  # esquerda[1800]        direita[0]
    ["?", "?", "?", "?", "?", "?"],  #        baixo [-900]
    ["?", "?", "?", "?", "?", "?"],
]


direction = 0
robo = None
pharmacies = []
zone_red = []
zone_green = ()
icon_zone = "?"
velo_max = -1000
steps_cont = 0
edge_arena = 0
zone_distance = 1150


# Função para imprimir a arena no Console
"""def show_arena():
    for row in range(len(arena)):
        for column in range(len(arena[0])):</*
            print('|', arena[row][column], end=' ')
        print('|')
    print("\n =-=-=-=-=-=-=-=-=-=-=-=-")"""


# Função para carregar todas as informações da arena
def loading():
    global zone_green, zone_red, pharmacies
    # show_arena()
    zone_red = []
    zone_green = ()
    for row in range(len(arena)):
        for column in range(len(arena[0])):
            if arena[row][column] == "O":
                zone_red.append((row, column))
            elif arena[row][column] == "G":
                zone_green = (row, column)
            elif arena[row][column] == "F":
                pharmacies.append((row, column))


# Retorna a direção que o robo está apontando
def compass():
    angle = gyroSensor()
    if 450 < angle < 1350:
        return 900
    elif -450 <= angle <= 450:
        return 0
    elif -1350 <= angle <= -450:
        return -900
    else:
        return 1800


# Ajustar um angulo recebido entre 1800 - -1799
def adjust_angle(angle):
    while angle < -1799 or angle > 1800:
        if angle > 1800:
            angle -= 3600
        elif angle < -1799:
            angle += 3600
    return angle


# Procurar as farmacias, portas e bordas.
def findPharmacyPos():
    global edge_arena
    for p in pharmacies:
        for movement in movements:
            pos = (p[0] + movement[0], p[1] + movement[1])
            if pos in pharmacies:
                pos_opposite = (
                    p[0] + opposite[movement][0],
                    p[1] + opposite[movement][1],
                )
                if (
                    robo
                    and (0 <= pos_opposite[0] < len(arena))
                    and (0 <= pos_opposite[1] < len(arena[0]))
                ):
                    new_movement = ref_m[adjust_angle(ref_m[movement] + 900)]
                    new_pos = (p[0] + new_movement[0], p[1] + new_movement[1])
                    if not (0 <= new_pos[0] < len(arena)) or not (
                        0 <= new_pos[1] < len(arena[0])
                    ):
                        edge_arena = ref_m[new_movement]
                    else:
                        edge_arena = ref_m[opposite[new_movement]]
                    return pos_opposite
                else:
                    break
    return None


# Fazer a leitura do sensor giroscópio
def gyroSensor():
    return motion_sensor.tilt_angles()[0]


# Calcular a heuristica das celulas
def heuristics(_start, _end):
    return abs(_start[0] - _end[0]) + abs(_start[1] - _end[1])


# Atualizar a posição do robo na arena
def update_robo_position(position):
    global robo, icon_zone
    if (
        robo is not None
        and (0 <= position[0] < len(arena))
        and (0 <= position[1] < len(arena[0]))
    ):
        arena[robo[0]][robo[1]] = icon_zone
        icon_zone = arena[position[0]][position[1]]
        robo = position
        arena[robo[0]][robo[1]] = "R"


# A_estrela para encontrar caminhos dentro da arena
def a_stars(destiny):
    paths_discovered = []
    if not robo:
        return None
    paths_discovered.append((0, robo))
    cost = {robo: 0}
    predecessor = {robo: None}
    while paths_discovered:
        paths_discovered.sort()
        current_cost, current_position = paths_discovered.pop(0)
        if current_position == destiny:
            path = []
            while current_position:
                path.append(current_position)
                current_position = predecessor[current_position]
            return path[::-1]
        for movement in movements:
            new_position = (
                current_position[0] + movement[0],
                current_position[1] + movement[1],
            )
            new_cost = current_cost + 1
            if (
                0 <= new_position[0] < len(arena)
                and 0 <= new_position[1] < len(arena[0])
            ) and arena[new_position[0]][new_position[1]] not in ["X", "F"]:
                if new_position not in cost or new_cost < cost[new_position]:
                    cost[new_position] = new_cost
                    priority = new_cost + heuristics(new_position, destiny)
                    paths_discovered.append((priority, new_position))
                    predecessor[new_position] = current_position
    return None


# Parar os motores e esperar um tempinho
async def stop():
    motor_pair.stop(motor_pair.PAIR_1)
    await runloop.sleep_ms(200)


# Aciona ou Para o atuador
def actuator(op):
    if op == "push":
        motor_pair.move_tank(motor_pair.PAIR_2, -800, -800)
    elif op == "empurre":
        motor_pair.move_tank(motor_pair.PAIR_2, 200, 200)
    else:
        motor_pair.stop(motor_pair.PAIR_2)


# Girar o robô para o angulo desejado
async def gyro_angle(angle):
    global direction

    direction = angle


# Movimento do robo de zona em zona analizando as possibilidades
async def move_analyze(steps):
    all_steps = abs(steps) * (zone_distance)
    _velocity = int(velo_max * 0.6) if steps > 0 else int(-(velo_max * 0.6))
    zone = color.WHITE
    for x in range(int(all_steps)):
        zone1, zone2 = color_sensor.color(port.E), color_sensor.color(port.F)
        if zone1 not in [color.WHITE] or zone2 not in [color.WHITE]:
            await stop()
            await move(-0.3)
            await aling("f")
            zone1, zone2 = color_sensor.color(port.E), color_sensor.color(port.F)
            while zone1 in [color.WHITE, color.UNKNOWN] and zone2 in [
                color.WHITE,
                color.UNKNOWN,
            ]:
                motor_pair.move(motor_pair.PAIR_1, 0, velocity=-100)
                zone1, zone2 = color_sensor.color(port.E), color_sensor.color(port.F)
            await stop()
            await runloop.sleep_ms(400)
            zone = zone1 if zone1 not in [color.WHITE, color.UNKNOWN] else zone2
            if ref_zone[zone] in ["G", "O"]:
                await motor_pair.move_for_time(
                    motor_pair.PAIR_1, 800, 0, velocity=_velocity
                )
                await gyro_angle(direction)
            else:
                motion_sensor.reset_yaw(direction)
                await stop()
                await move(-0.3)
            return zone
        error = int(((((direction - gyroSensor()) + 1800) % 3600) - 1800) * 0.4)
        motor_pair.move(motor_pair.PAIR_1, error, velocity=_velocity)
        await runloop.sleep_ms(1)
    return int(zone)


# Move independente de qualquer coisa
async def move(steps):
    all_steps = abs(steps) * zone_distance
    _velocity = (velo_max * 0.6) if steps > 0 else -(velo_max * 0.6)
    for x in range(all_steps):
        error = ((((gyroSensor() - direction) + 1800) % 3600) - 1800) * 2
        motors = [_velocity + error, _velocity - error]
        motor_pair.move_tank(motor_pair.PAIR_1, int(motors[0]), int(motors[1]))
        await runloop.sleep_ms(1)
    await stop()


# Move para uma posição expecífica
async def move_position(position):
    if robo and robo != position:
        movement = (position[0] - robo[0], position[1] - robo[1])
        if direction != ref_m[movement]:
            await gyro_angle(ref_m[movement])
        if position in pharmacies or robo in pharmacies:
            await move(1)
            update_robo_position(position)
        else:
            zone = await move_analyze(1)
            #        if arena[position[0]][position[1]] == '?':
            arena[position[0]][position[1]] = ref_zone[zone]
            loading()
            if ref_zone[zone] not in ["?", "X", "F"]:
                update_robo_position(position)
                return True
        #        else:
        #            update_robo_position(position)
        #            return True
        return False
    return True


# Alinhamento do robô com a cor.
async def aling(_direction):
    color_ = (color_sensor.color(port.E), color_sensor.color(port.F))
    velocity = int(velo_max * 0.1) if _direction == "f" else int(-(velo_max * 0.1))
    while True:
        if color_sensor.color(port.E) not in [color_[0], color.UNKNOWN]:
            if color_sensor.color(port.F) not in [color_[1], color.UNKNOWN]:
                break
            else:
                motor_pair.move_tank(motor_pair.PAIR_1, velocity, int(-(velocity / 2)))
        elif color_sensor.color(port.F) not in [color_[1], color.UNKNOWN]:
            motor_pair.move_tank(motor_pair.PAIR_1, int(-(velocity / 2)), velocity)
        else:
            motor_pair.move_tank(motor_pair.PAIR_1, velocity, velocity)
    await stop()


# Verifica se pode, pra poder alinhar
async def can_aling():
    global steps_cont
    for movement in movements:
        if robo:
            position = (robo[0] + movement[0], robo[1] + movement[1])
            if not (0 <= position[0] < len(arena)) or not (
                0 <= position[1] < len(arena[0])
            ):
                await gyro_angle(ref_m[movement])
                if (
                    color_sensor.color(port.E) is color.BLACK
                    or color_sensor.color(port.F) is color.BLACK
                ):
                    await move(-0.35)
                await aling("f")
                motion_sensor.reset_yaw(direction)
                await runloop.sleep_ms(200)
                await move(-0.35)
                steps_cont = 0


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\
# Responsável por achar um dos cantos do mapa
async def findPosition():
    global robo, arena, direction, m_hour, movements
    cont = 1
    _dir = " "
    while not button.pressed(button.LEFT) and not button.pressed(button.RIGHT):
        await light_matrix.write("?")
        await runloop.sleep_ms(10)
        light_matrix.clear()
    light_matrix.set_orientation(1)
    if button.pressed(button.LEFT):
        light_matrix.set_pixel(4, 2, 100)
        light_matrix.set_pixel(3, 1, 100)
        light_matrix.set_pixel(3, 2, 100)
        light_matrix.set_pixel(3, 3, 100)
        light_matrix.set_pixel(2, 2, 100)
        light_matrix.set_pixel(1, 2, 100)
        light_matrix.set_pixel(0, 2, 100)
        _dir = "<"
    else:
        light_matrix.set_pixel(0, 2, 100)
        light_matrix.set_pixel(1, 1, 100)
        light_matrix.set_pixel(1, 2, 100)
        light_matrix.set_pixel(1, 3, 100)
        light_matrix.set_pixel(2, 2, 100)
        light_matrix.set_pixel(3, 2, 100)
        light_matrix.set_pixel(4, 2, 100)
        _dir = ">"
    await runloop.sleep_ms(1000)
    direction = compass()
    robo = (0, 0)
    # pass_to_edge = (0,0)
    while True:
        zone = await move_analyze(1)
        """if ref_zone[zone] in ['G', ' ', 'O']:
            pass_to_edge = (((pass_to_edge[0] - 1) if direction == 900 else ((pass_to_edge[0] + 1) if direction == -900 else (pass_to_edge[0]))) , ((pass_to_edge[1] + 1) if direction == 0 else ((pass_to_edge[1] - 1) if direction == 1800 else (pass_to_edge[1]))))
            print("pass: ", pass_to_edge)"""
        await stop()
        if ref_zone[zone] == "X":
            await stop()
            save_dir = direction
            await gyro_angle(adjust_angle(direction + 900))
            if ref_zone[await move_analyze(1)] in ["?", "X"]:
                await gyro_angle(adjust_angle(direction + 1800))
                await move_analyze(1)
            angle = adjust_angle(direction + 1800)
            await gyro_angle(save_dir)
            await move_analyze(1)
            await move_analyze(1)
            await gyro_angle(angle)
            await move_analyze(1)
            await gyro_angle(save_dir)
        elif ref_zone[zone] in ["?", "F"]:
            robo = (
                (
                    (
                        (0 if ref_zone[zone] == "?" else 1)
                        if direction == 900
                        else (
                            len(arena) - 1 if ref_zone[zone] == "?" else len(arena) - 2
                        )
                    )
                    if direction in [-900, 900]
                    else (robo[0])
                ),
                (
                    (
                        (
                            len(arena[0]) - 1
                            if ref_zone[zone] == "?"
                            else len(arena[0]) - 2
                        )
                        if direction == 0
                        else (0 if ref_zone[zone] == "?" else 1)
                    )
                    if direction in [0, 1800]
                    else (robo[1])
                ),
            )
            # robo = ( ( (0 if zone == 1 else 1) if direction == -900 else ( len(arena)-1 if zone == 1 else len(arena)-2)) if direction in [-900, 900] else (robo[0]) , ( (len(arena[0])-1 if zone == 1 else len(arena[0])-2) if direction == 0 else ( 0 if zone == 1 else 1) ) if direction in [0, 1800] else (robo[1]) )
            if cont >= 2:
                for i in range(len(movements)):
                    m_hour[i] = ref_m[
                        adjust_angle(
                            (direction + (i * 900))
                            if _dir == "<"
                            else (direction - (i * 900))
                        )
                    ]
                    arena[robo[0]][robo[1]] = "R"

                await sound.beep(900, 400, 100)
                break
            await gyro_angle(
                adjust_angle((direction + 900) if _dir == "<" else (direction - 900))
            )
            cont += 1


# Achar uma nova celula para explorar o mais perto do robo possível
def next_zone():
    global arena
    # PROCURANDO [?] AO REDOR DO ROBO
    for movement in m_hour:
        if robo:
            pos = (robo[0] + movement[0], robo[1] + movement[1])
            if (0 <= pos[0] < len(arena) and 0 <= pos[1] < len(arena[0])) and arena[
                pos[0]
            ][pos[1]] == "?":
                return pos
    # PROUCRANDO [?] O MAIS PERTO DO ROBO
    nextZone = None
    for row in range(len(arena)):
        for column in range(len(arena[0])):
            if arena[row][column] == "?":
                path = a_stars((row, column))
                if path:
                    if nextZone:
                        if len(path) < nextZone[0]:
                            nextZone = (len(path), (row, column))
                    else:
                        nextZone = (len(path), (row, column))
    if nextZone:
        return nextZone[1]

    for row in range(len(arena)):
        for column in range(len(arena[0])):
            if arena[row][column] == " ":
                arena[row][column] = "?"
    return next_zone()


# Caminha até uma determinada posição no mapa indicada
async def walk(destiny):
    global steps_cont
    if robo == destiny:
        return
    path = a_stars(destiny)
    if path:
        path.pop(0)
        for position in path:
            # show_arena()
            if steps_cont >= 10 and (robo != zone_green or robo not in zone_red):
                await can_aling()
            if not await move_position(position):
                await walk(destiny)
                break
            await stop()
            steps_cont += 1


def phar():
    for phar in pharmacies:
        for movement in movements:
            pos = (phar[0] + movement[0], phar[1] + movement[1])
            if robo == pos:
                return ref_m[movement]


# Procura uma dos quadrados das farmácia.. para calcular o restante
async def findPharmacy():
    global arena, pharmacies, ref_zone
    loading()
    while not pharmacies:
        await walk(next_zone())
    await sound.beep(1024, 500, 100)
    phar = pharmacies[0]
    if robo:
        for movement in movements:
            pos = (phar[0] + movement[0], phar[1] + movement[1])
            if (
                0 <= pos[0] < len(arena) and 0 <= pos[1] < len(arena[0])
            ) and pos != robo:
                for movement in movements:
                    pos_ = (pos[0] + movement[0], pos[1] + movement[1])
                    if not (
                        (0 <= pos_[0] < len(arena)) and (0 <= pos_[1] < len(arena[0]))
                    ):
                        arena[pos[0]][pos[1]] = "F"
                        pharmacies.append(pos)
                        await walk(findPharmacyPos())
                        return


# Entrar na farmacia e pegar os cubos
async def takeCube():
    port_phar = phar()
    if port_phar:
        await gyro_angle(adjust_angle(port_phar + 1800))
    await aling("f")  # alinha na porta
    await move(-0.3)  # volta pra trás
    await gyro_angle(edge_arena)  # vira pra borda
    await aling("f")  # se alinha com a borda
    await move(-0.35)  # vai pra tras
    await gyro_angle(phar())  # vira pra portafarm
    actuator("push")
    await move(-2)  # vai pra frente 3 red
    await gyro_angle(adjust_angle(direction + 1800))
    await aling("f")
    await move(-0.68)  # vai pro meio
    await gyro_angle(ref_m[opposite[ref_m[edge_arena]]])  # vira pro verde
    await move(-0.5)  # pega o verde
    await move(0.5)  # vai pra tras
    await gyro_angle(ref_m[opposite[ref_m[phar()]]])  # direcao oposta da porta da farm
    actuator("stop")
    await move(-1)  # vai pra frente
    await aling("t")  # alinha
    await move(-0.3)  # vai pra frente
    await gyro_angle(edge_arena)
    await move(0.2)
    await aling("f")  # alinha
    await move(-0.3)  # vai pra frente


# Deixar o cubo
async def leave_cube():
    await gyro_angle(adjust_angle(direction + 1800))
    movement = ref_m[direction]
    if robo:
        update_robo_position((robo[0] + movement[0], robo[1] + movement[1]))
        motor_pair.move(motor_pair.PAIR_1, 0, velocity=-200)
        await runloop.sleep_ms(150)
        actuator("empurre")
        await runloop.sleep_ms(1300)
        actuator("push")
        await runloop.sleep_ms(500)
        actuator("stop")
        await move(0.4)


async def delivery_cube():
    global arena
    while not zone_green:
        await walk(next_zone())
    await walk(zone_green)
    await leave_cube()
    arena[zone_green[0]][zone_green[1]] = "X"
    for i in range(3):
        while not zone_red:
            await walk(next_zone())
        pos = zone_red.pop(0)
        await walk(pos)
        loading()
        await leave_cube()
        arena[pos[0]][pos[1]] = "X"


# Loop principal =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
async def main():
    await findPosition()
    await findPharmacy()
    await takeCube()
    await delivery_cube()


runloop.run(main())


# =-=-=-=-=-=-=- CÓPIA DE SEGURANÇA DA NEW STRATEGY =-=-=-=-=--=

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
