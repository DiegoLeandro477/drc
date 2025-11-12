UP = "w"
DOWN = "s"
LEFT = "a"
RIGHT = "d"

# Dicionário de mapeamento
OPPOSITE_DIRECTION = {
    UP: DOWN,
    DOWN: UP,
    LEFT: RIGHT,
    RIGHT: LEFT,
}

# --- Exemplo de Uso ---
current_direction = RIGHT  # Ex: "d"
opposite = OPPOSITE_DIRECTION[current_direction]

print(f"A direção oposta a {current_direction} é {opposite}")
# Saída: A direção oposta a d é a
