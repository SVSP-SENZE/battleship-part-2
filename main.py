import pygame
import random
from shipnew import SHIP_TYPES_LIST, SHIP_SIZES, update_ship_status_on_hit, reset_ship_status, create_ship_record
from boardnew import can_place, place_ship, auto_place_with_records, check_win
from gamemanager import process_attack
import filemanager   # NEW

pygame.init()
screen = pygame.display.set_mode((1000, 800))
pygame.display.set_caption('BATTLESHIP')
clock = pygame.time.Clock()

# Fonts
font1 = pygame.font.Font(None, 50)
font2 = pygame.font.Font(None, 30)

# Input box setup
input_box = pygame.Rect(350, 350, 300, 60)
active = False
text = ""
p1 = ""
p2 = ""
current = "p1"

# Background image or fallback
try:
    bg1 = pygame.image.load(r"C:\Users\srika\OneDrive\Desktop\random.jpg").convert()
    bg1 = pygame.transform.scale(bg1, (1000, 800))
except:
    bg1 = pygame.Surface((1000, 800))
    bg1.fill((20, 50, 80))

# Ship icon fallback
try:
    ship_image = pygame.image.load(r"C:\Users\srika\OneDrive\Desktop\ship.jpg").convert_alpha()
    ship_image = pygame.transform.scale(ship_image, (35, 35))
except:
    ship_image = pygame.Surface((35, 35), pygame.SRCALPHA)
    pygame.draw.circle(ship_image, (200, 200, 200), (17, 17), 15)

# Buttons
manual_button = pygame.Rect(300, 300, 400, 80)
automatic_button = pygame.Rect(300, 420, 400, 80)
resume_button = pygame.Rect(300, 540, 400, 60)
restart_button = pygame.Rect(720, 50, 200, 40)   # NEW

# Game variables
game_state = "input"
gridsize = 10
board_topleft = (300, 200)
ships_placed = 0

# Boards and attempts
p1board = [[0] * gridsize for _ in range(gridsize)]
p2board = [[0] * gridsize for _ in range(gridsize)]
p1_attempts = [[0] * gridsize for _ in range(gridsize)]
p2_attempts = [[0] * gridsize for _ in range(gridsize)]

current_player = "p1"
winner = None

# Colors
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
RED = (220, 50, 50)
BLUE = (50, 120, 220)

# Ship placement
ship_index = 0
ship_dir = "H"

# Per-player ship records
p1_ships = []
p2_ships = []

ship_status_p1 = {name: False for name, _ in SHIP_TYPES_LIST}
ship_status_p2 = {name: False for name, _ in SHIP_TYPES_LIST}

# Does save file exist?
has_saved = filemanager.has_save()


# --------------------------------------------------
# SAVE / LOAD HELPERS
# --------------------------------------------------

def make_save_dict():
    return {
        'game_state': game_state,
        'gridsize': gridsize,
        'board_topleft': board_topleft,
        'p1board': p1board,
        'p2board': p2board,
        'p1_attempts': p1_attempts,
        'p2_attempts': p2_attempts,
        'current_player': current_player,
        'winner': winner,
        'ship_index': ship_index,
        'ship_dir': ship_dir,
        'ships_placed': ships_placed,
        'p1_ships': p1_ships,
        'p2_ships': p2_ships,
        'ship_status_p1': ship_status_p1,
        'ship_status_p2': ship_status_p2,
        'p1': p1,
        'p2': p2
    }


def load_state_dict(state):
    global game_state, gridsize, board_topleft
    global p1board, p2board, p1_attempts, p2_attempts
    global current_player, winner
    global ship_index, ship_dir, ships_placed
    global p1_ships, p2_ships, ship_status_p1, ship_status_p2
    global p1, p2

    if not state:
        return False

    game_state = state['game_state']
    gridsize = state['gridsize']
    board_topleft = state['board_topleft']
    p1board = state['p1board']
    p2board = state['p2board']
    p1_attempts = state['p1_attempts']
    p2_attempts = state['p2_attempts']
    current_player = state['current_player']
    winner = state['winner']
    ship_index = state['ship_index']
    ship_dir = state['ship_dir']
    ships_placed = state['ships_placed']
    p1_ships = state['p1_ships']
    p2_ships = state['p2_ships']
    ship_status_p1 = state['ship_status_p1']
    ship_status_p2 = state['ship_status_p2']
    p1 = state['p1']
    p2 = state['p2']
    return True


# --------------------------------------------------
# DRAW HELPERS
# --------------------------------------------------

def drawboard(board, top_left):
    for r in range(gridsize):
        for c in range(gridsize):
            rect = pygame.Rect(top_left[0] + c * 35, top_left[1] + r * 35, 35, 35)
            pygame.draw.rect(screen, WHITE, rect, 2)
            if board[r][c] == 1:
                screen.blit(ship_image, rect.topleft)


def draw_attempts(attempts, top_left):
    for r in range(gridsize):
        for c in range(gridsize):
            rect = pygame.Rect(top_left[0] + c * 35, top_left[1] + r * 35, 35, 35)
            if attempts[r][c] == 2:
                pygame.draw.rect(screen, RED, rect)
            elif attempts[r][c] == 3:
                pygame.draw.rect(screen, BLUE, rect)
            pygame.draw.rect(screen, GRAY, rect, 1)


def draw_ship_status_for_opponent(status_dict, pos=(700, 200)):
    x, y = pos
    title = font1.render("SHIPS", True, (255, 255, 0))
    screen.blit(title, (x, y))
    y += 60
    for name, size in SHIP_TYPES_LIST:
        color = RED if status_dict.get(name) else WHITE
        txt = font2.render(f"{size} - {name}", True, color)
        screen.blit(txt, (x, y))
        y += 40


# --------------------------------------------------
# MAIN GAME LOOP
# --------------------------------------------------
running = True
while running:

    for event in pygame.event.get():

        # Quit → Auto Save
        if event.type == pygame.QUIT:
            filemanager.save_game(make_save_dict())
            running = False

        # Keys
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_r:
                ship_dir = "V" if ship_dir == "H" else "H"

            # Manual save
            if event.key == pygame.K_s:
                filemanager.save_game(make_save_dict())
                print("Game Saved.")

        # ---------------------
        # INPUT STATE (names)
        # ---------------------
        if game_state == "input":

            if event.type == pygame.MOUSEBUTTONDOWN:
                active = input_box.collidepoint(event.pos)

            if event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    if text.strip() != "":
                        if current == "p1":
                            p1 = text.strip()
                            text = ""
                            current = "p2"
                        elif current == "p2":
                            p2 = text.strip()
                            text = ""
                            current = "done"
                            active = False
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    if len(text) < 20:
                        text += event.unicode

            if event.type == pygame.KEYDOWN and current == "done":
                if event.key == pygame.K_SPACE:
                    game_state = "menu"

        # ---------------------
        # MENU
        # ---------------------
        elif game_state == "menu":

            if event.type == pygame.MOUSEBUTTONDOWN:

                # Manual
                if manual_button.collidepoint(event.pos):
                    game_state = "setup_manual_p1"
                    p1_ships.clear()
                    p2_ships.clear()
                    p1board = [[0]*gridsize for _ in range(gridsize)]
                    p2board = [[0]*gridsize for _ in range(gridsize)]
                    p1_attempts = [[0]*gridsize for _ in range(gridsize)]
                    p2_attempts = [[0]*gridsize for _ in range(gridsize)]
                    reset_ship_status(ship_status_p1)
                    reset_ship_status(ship_status_p2)
                    ship_index = 0
                    ship_dir = "H"

                # Automatic
                elif automatic_button.collidepoint(event.pos):
                    p1_ships.clear()
                    p2_ships.clear()
                    p1board = [[0]*gridsize for _ in range(gridsize)]
                    p2board = [[0]*gridsize for _ in range(gridsize)]
                    p1_attempts = [[0]*gridsize for _ in range(gridsize)]
                    p2_attempts = [[0]*gridsize for _ in range(gridsize)]
                    reset_ship_status(ship_status_p1)
                    reset_ship_status(ship_status_p2)
                    auto_place_with_records(p1board, p1_ships, gridsize)
                    auto_place_with_records(p2board, p2_ships, gridsize)
                    game_state = "ready"

                # Resume saved game
                elif resume_button.collidepoint(event.pos) and filemanager.has_save():
                    data = filemanager.load_game()
                    if data:
                        load_state_dict(data)

        # ---------------------
        # MANUAL P1
        # ---------------------
        elif game_state == "setup_manual_p1":
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                gx = (x - board_topleft[0]) // 35
                gy = (y - board_topleft[1]) // 35
                if 0 <= gx < gridsize and 0 <= gy < gridsize:
                    if ship_index < len(SHIP_SIZES):
                        size = SHIP_SIZES[ship_index]
                        if can_place(p1board, gy, gx, size, ship_dir, gridsize):
                            cells = place_ship(p1board, gy, gx, size, ship_dir)
                            name = SHIP_TYPES_LIST[ship_index][0]
                            p1_ships.append(create_ship_record(name, cells))
                            ship_index += 1

                    if ship_index >= len(SHIP_SIZES):
                        ship_index = 0
                        ship_dir = "H"
                        game_state = "setup_manual_p2"

        # ---------------------
        # MANUAL P2
        # ---------------------
        elif game_state == "setup_manual_p2":
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                gx = (x - board_topleft[0]) // 35
                gy = (y - board_topleft[1]) // 35
                if 0 <= gx < gridsize and 0 <= gy < gridsize:
                    if ship_index < len(SHIP_SIZES):
                        size = SHIP_SIZES[ship_index]
                        if can_place(p2board, gy, gx, size, ship_dir, gridsize):
                            cells = place_ship(p2board, gy, gx, size, ship_dir)
                            name = SHIP_TYPES_LIST[ship_index][0]
                            p2_ships.append(create_ship_record(name, cells))
                            ship_index += 1

                    if ship_index >= len(SHIP_SIZES):
                        ship_index = 0
                        ship_dir = "H"
                        game_state = "ready"

        # ---------------------
        # READY
        # ---------------------
        elif game_state == "ready":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_state = "battle"

        # ---------------------
        # BATTLE
        # ---------------------
        elif game_state == "battle":
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                gx = (x - board_topleft[0]) // 35
                gy = (y - board_topleft[1]) // 35
                if 0 <= gx < gridsize and 0 <= gy < gridsize:

                    current_player, winner = process_attack(
                        current_player, gy, gx,
                        p1board, p2board,
                        p1_attempts, p2_attempts,
                        p1_ships, p2_ships,
                        ship_status_p1, ship_status_p2,
                        p1, p2, gridsize
                    )

                    # AUTOSAVE
                    filemanager.save_game(make_save_dict())

                    if winner is not None:
                        game_state = "gameover"

        # ---------------------
        # GAMEOVER
        # ---------------------
        elif game_state == "gameover":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ---------------------
        # RESTART BUTTON
        # ---------------------
        if event.type == pygame.MOUSEBUTTONDOWN:
            if restart_button.collidepoint(event.pos):
                # wipe to menu
                game_state = "menu"
                p1_ships = []
                p2_ships = []
                p1board = [[0]*gridsize for _ in range(gridsize)]
                p2board = [[0]*gridsize for _ in range(gridsize)]
                p1_attempts = [[0]*gridsize for _ in range(gridsize)]
                p2_attempts = [[0]*gridsize for _ in range(gridsize)]
                reset_ship_status(ship_status_p1)
                reset_ship_status(ship_status_p2)


    # --------------------------------------------------
    # DRAW SCREEN
    # --------------------------------------------------

    screen.blit(bg1, (0, 0))

    # INPUT
    if game_state == "input":
        if current == "p1":
            label = font1.render("Enter p1:", True, WHITE)
        elif current == "p2":
            label = font1.render("Enter p2:", True, WHITE)
        else:
            label = font1.render(f"Welcome {p1} & {p2}!", True, WHITE)
            sub = font2.render("Press SPACE to start the game!", True, (255, 200, 0))
            screen.blit(label, (200, 300))
            screen.blit(sub, (250, 380))
            pygame.display.flip()
            clock.tick(60)
            continue

        screen.blit(label, (250, 200))
        pygame.draw.rect(screen, (200, 0, 0), input_box, 5)
        txt_surface = font1.render(text, True, WHITE)
        screen.blit(txt_surface, (input_box.x + 10, input_box.y + 10))

    # MENU
    elif game_state == "menu":
        title = font1.render("Choose set up mode", True, WHITE)
        screen.blit(title, (250, 250))

        pygame.draw.rect(screen, (30, 120, 200), manual_button)
        pygame.draw.rect(screen, (30, 120, 200), automatic_button)

        screen.blit(font2.render("Set board manually", True, WHITE),
                    (manual_button.x + 50, manual_button.y + 35))
        screen.blit(font2.render("Automatic setup", True, WHITE),
                    (automatic_button.x + 35, automatic_button.y + 45))

        if filemanager.has_save():
            pygame.draw.rect(screen, (40, 180, 100), resume_button)
            screen.blit(font2.render("Resume saved game", True, WHITE),
                        (resume_button.x + 60, resume_button.y + 20))

    # MANUAL P1
    elif game_state == "setup_manual_p1":
        screen.blit(font2.render(f"{p1} place ships", True, WHITE), (300, 100))
        drawboard(p1board, board_topleft)

    # MANUAL P2
    elif game_state == "setup_manual_p2":
        screen.blit(font2.render(f"{p2} place ships", True, WHITE), (300, 100))
        drawboard(p2board, board_topleft)

    # READY
    elif game_state == "ready":
        screen.blit(font1.render("Both players ready!", True, (0, 200, 0)),
                    (250, 300))
        screen.blit(font2.render("Press SPACE to start battle!",
                                 True, WHITE), (300, 380))

    # BATTLE
    elif game_state == "battle":

        screen.blit(font1.render(
            f"{p1 if current_player=='p1' else p2}'s turn",
            True, (255, 220, 0)), (300, 130))

        screen.blit(font2.render("Click grid to attack!", True, WHITE),
                    (320, 170))

        if current_player == "p1":
            draw_attempts(p2_attempts, board_topleft)
            draw_ship_status_for_opponent(ship_status_p2)
        else:
            draw_attempts(p1_attempts, board_topleft)
            draw_ship_status_for_opponent(ship_status_p1)

    # GAME OVER
    elif game_state == "gameover":
        screen.blit(font1.render(f"{winner} wins!", True, (0, 200, 0)),
                    (330, 300))
        screen.blit(font2.render("Press ESC to quit", True, WHITE),
                    (370, 370))

    # Draw Restart button
    pygame.draw.rect(screen, (100, 100, 100), restart_button)
    screen.blit(font2.render("Restart (New Game)", True, WHITE),
                (restart_button.x + 20, restart_button.y + 8))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
