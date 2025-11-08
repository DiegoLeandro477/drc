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
    await stop()
    angle = adjust_angle(angle)
    cont = 0
    while gyroSensor() != angle and cont < 1200:
        res = ((((gyroSensor() - angle) + 1800) % 3600) - 1800) * 0.6
        motor_pair.move_tank(motor_pair.PAIR_1, int(res), int(-res))
        cont += 1
        await runloop.sleep_ms(2)
    await stop()
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
