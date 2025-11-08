# Constante para representar o Robô
ROBO = "R"
# Constante para representar um espaço vazio na matriz
VAZIO = "."


def criar_matriz_com_robo():
    # Inicializa a matriz 1x1 com um espaço vazio
    matriz = [[VAZIO]]
    # Posição inicial do Robô (linha, coluna) - Começa no índice (0, 0)
    posicao_robo = (0, 0)
    # Coloca o Robô na matriz inicial
    matriz[0][0] = ROBO
    # Retorna a matriz e a posição do robô
    return matriz, posicao_robo


def exibir_matriz(matriz):
    # Imprime um cabeçalho para a exibição da matriz
    print("\n--- Campo de Visão do Robô ---")
    # Itera sobre cada linha da matriz
    for linha in matriz:
        # Imprime os elementos da linha, separados por espaços, para melhor visualização
        print(" ".join(map(str, linha)))
    # Imprime o formato atual (dimensões)
    print(f"Formato: {len(matriz)} linhas x {len(matriz[0])} colunas")
    print("------------------------------")


def mover_robo(matriz, pos_atual, direcao):
    # Desempacota a posição atual do robô
    linha_atual, coluna_atual = pos_atual
    # Obtém as dimensões atuais da matriz
    linhas_atuais = len(matriz)
    colunas_atuais = len(matriz[0])

    # Inicializa as variáveis para a nova posição (por padrão, é a posição atual)
    nova_linha, nova_coluna = linha_atual, coluna_atual

    # Dicionário mapeando a direção para a mudança de coordenada (dl=delta linha, dc=delta coluna)
    movimentos = {
        "W": (-1, 0),  # Cima (Up)
        "S": (1, 0),  # Baixo (Down)
        "A": (0, -1),  # Esquerda (Left)
        "D": (0, 1),  # Direita (Right)
    }

    # Verifica se a direção é válida
    if direcao in movimentos:
        # Calcula a mudança de linha e coluna
        dl, dc = movimentos[direcao]
        # Calcula a nova posição
        nova_linha = linha_atual + dl
        nova_coluna = coluna_atual + dc
    else:
        # Se a direção for inválida, informa o erro e retorna sem mover
        print("Direção inválida. Use W/A/S/D.")
        return matriz, pos_atual

    # --- Lógica de Expansão e Movimento ---

    # 💥 CORREÇÃO DO ERRO: Inicializa os offsets com 0 (zero)
    # Eles só serão alterados se houver expansão para CIMA ou ESQUERDA.
    offset_linha = 0
    offset_coluna = 0
    # Fim da correção

    # Variáveis que indicam as novas dimensões necessárias (por padrão, as atuais)
    nova_linhas_matriz = linhas_atuais
    nova_colunas_matriz = colunas_atuais

    # 1. Checagem de Expansão

    # Se a nova linha for menor que 0 (mover para fora do limite superior)
    if nova_linha < 0:
        # A matriz precisa de uma nova linha no topo, aumentando o número total de linhas
        nova_linhas_matriz += 1
        # O Robô se moverá para a linha de índice 0 na nova matriz
        nova_linha = 0
    # Se a nova linha for maior ou igual ao número de linhas atuais (mover para fora do limite inferior)
    elif nova_linha >= linhas_atuais:
        # A matriz precisa de uma nova linha no rodapé
        nova_linhas_matriz = nova_linha + 1

    # Se a nova coluna for menor que 0 (mover para fora do limite esquerdo)
    if nova_coluna < 0:
        # A matriz precisa de uma nova coluna à esquerda
        nova_colunas_matriz += 1
        # O Robô se moverá para a coluna de índice 0 na nova matriz
        nova_coluna = 0
    # Se a nova coluna for maior ou igual ao número de colunas atuais (mover para fora do limite direito)
    elif nova_coluna >= colunas_atuais:
        # A matriz precisa de uma nova coluna à direita
        nova_colunas_matriz = nova_coluna + 1

    # 2. Execução da Expansão, se necessário

    # Verifica se houve necessidade de expansão (se as novas dimensões são diferentes das atuais)
    if nova_linhas_matriz > linhas_atuais or nova_colunas_matriz > colunas_atuais:
        print(f"\nMatriz se expandiu para {nova_linhas_matriz}x{nova_colunas_matriz}!")
        # Cria uma nova matriz vazia com as novas dimensões
        nova_matriz = []

        # Determina o deslocamento (offset) da linha e coluna
        # Se houve expansão para CIMA (nova_linha == 0 e veio de cima), o conteúdo antigo desloca 1 linha para baixo
        offset_linha = 1 if direcao == "W" and linha_atual == 0 else 0
        # Se houve expansão para ESQUERDA (nova_coluna == 0 e veio da esquerda), o conteúdo antigo desloca 1 coluna para direita
        offset_coluna = 1 if direcao == "A" and coluna_atual == 0 else 0

        # Preenche a nova matriz
        for r in range(nova_linhas_matriz):
            # Cria uma nova linha cheia de VAZIO
            nova_linha_list = [VAZIO] * nova_colunas_matriz
            nova_matriz.append(nova_linha_list)

            # Se a linha atual (r) corresponde a uma linha da matriz antiga (considerando o offset)
            if 0 <= r - offset_linha < linhas_atuais:
                # Preenche a parte correspondente da nova linha com o conteúdo da matriz antiga
                for c in range(colunas_atuais):
                    # O conteúdo da matriz antiga é copiado com o deslocamento de coluna
                    nova_matriz[r][c + offset_coluna] = matriz[r - offset_linha][c]

        # Atualiza a referência da matriz para a nova matriz expandida
        matriz = nova_matriz

        # Se a matriz expandiu para CIMA/ESQUERDA, a nova posição do robô é a coordenada 0
        # Ajusta a posição final do Robô (se expandiu, a nova posição é 0, caso contrário é a coordenada calculada)
        if direcao == "W" and linha_atual == 0:
            nova_linha = 0
        elif direcao == "A" and coluna_atual == 0:
            nova_coluna = 0
        # Em qualquer outro caso de expansão (S, D), a nova posição já está correta

    # 3. Finaliza o Movimento

    # Limpa a posição antiga do Robô na matriz
    # Agora, offset_linha e offset_coluna sempre terão um valor (0 se não houve expansão para Cima/Esquerda)
    matriz[linha_atual + offset_linha][coluna_atual + offset_coluna] = VAZIO

    # Coloca o Robô na nova posição
    matriz[nova_linha][nova_coluna] = ROBO

    # Atualiza a posição atual do Robô
    nova_posicao = (nova_linha, nova_coluna)

    # Retorna a matriz e a nova posição
    return matriz, nova_posicao


# O restante das funções (criar_matriz_com_robo, exibir_matriz, main) permanece o mesmo.


def main():
    # Cria a matriz inicial com o Robô na posição (0, 0)
    matriz, pos_robo = criar_matriz_com_robo()
    print("Robô ('R') inicializado na matriz 1x1.")

    # Loop principal para interação com o Robô
    while True:
        # Exibe o estado atual da matriz
        exibir_matriz(matriz)

        # Pede a entrada do usuário
        print("\nMover Robô:")
        direcao = input(
            "Use W (Cima), S (Baixo), A (Esquerda), D (Direita) ou 'X' para Sair: "
        ).upper()

        # Verifica a opção de saída
        if direcao == "X":
            print("\nEncerrando simulação.")
            break

        # Move o Robô e obtém a matriz e a posição atualizadas
        matriz, pos_robo = mover_robo(matriz, pos_robo, direcao)


# Bloco de execução principal
if __name__ == "__main__":
    main()
