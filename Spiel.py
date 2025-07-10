import pygame
import random
import sqlite3

# --- Initialization ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Magic Sword vs Monsters")
clock = pygame.time.Clock()

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --- Images ---
background_img = pygame.image.load("background.png").convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

player_img_right = pygame.transform.scale(pygame.image.load("player_right.png").convert_alpha(), (96, 96))
player_img_left = pygame.transform.scale(pygame.image.load("player_left.png").convert_alpha(), (96, 96))
sword_img = pygame.transform.scale(pygame.image.load("sword.png").convert_alpha(), (64, 128))

# Load rank images
rank_images = {
    "D": pygame.image.load("rank_D.png").convert_alpha(),
    "C": pygame.image.load("rank_C.png").convert_alpha(),
    "B": pygame.image.load("rank_B.png").convert_alpha(),
    "A": pygame.image.load("rank_A.png").convert_alpha(),
    "S": pygame.image.load("rank_S.png").convert_alpha(),
    "SS": pygame.image.load("rank_SS.png").convert_alpha(),
    "SSS": pygame.image.load("rank_SSS.png").convert_alpha(),
}

# Load hearts and digits
heart_img = pygame.transform.scale(pygame.image.load("heart.png").convert_alpha(), (24, 24))
digit_images = []
for i in range(10):
    digit = pygame.image.load(f"digit_{i}.png").convert_alpha()
    digit = pygame.transform.scale(digit, (20, 28))
    digit_images.append(digit)

# --- Player ---
player_img = player_img_right
facing = "right"
player_pos = [WIDTH // 2, HEIGHT - 150]
player_speed = 5
lives = 3

# --- Sword Animation ---
swing_phase = "idle"
swing_angle = 0
thrust_offset = 0
pivot_drop = 0
swing_start_ms = 0
swing_duration = 150
rest_duration = 250
retract_duration = 400
max_swing_angle = 100
max_thrust = 25
max_pivot_drop = 30

# --- Enemies ---
monster_size = 50
monster_speed = 3
monsters = []
MAX_MONSTERS = 5
last_monster_spawn = 0

# --- Falling Objects ---
falling_objects = []
fall_speed = 4
fall_spawn_chance = 0.002
fall_size = 40

# --- Score and Ranks ---
score = 0
combo = 0
last_kill_time = 0
font = pygame.font.SysFont(None, 36)

# --- Game State ---
game_over = False

# --- Database setup ---
def init_db():
    conn = sqlite3.connect("highscore.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS highscores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_highscore():
    conn = sqlite3.connect("highscore.db")
    c = conn.cursor()
    c.execute('SELECT MAX(score) FROM highscores')
    result = c.fetchone()
    conn.close()
    return result[0] if result[0] is not None else 0

def update_highscore(new_score):
    current = get_highscore()
    if new_score > current:
        conn = sqlite3.connect("highscore.db")
        c = conn.cursor()
        c.execute('INSERT INTO highscores (score) VALUES (?)', (new_score,))
        conn.commit()
        conn.close()

# --- Menu ---
def show_start_menu():
    highscore = get_highscore()
    title_font = pygame.font.SysFont(None, 72)
    info_font = pygame.font.SysFont(None, 36)
    while True:
        screen.fill(WHITE)
        title_text = title_font.render("Magic Sword vs Monsters", True, BLACK)
        prompt_text = info_font.render("Press SPACE to Start", True, BLACK)
        highscore_text = info_font.render(f"Highscore: {highscore}", True, BLACK)
        screen.blit(title_text, title_text.get_rect(center=(WIDTH//2, HEIGHT//3)))
        screen.blit(highscore_text, highscore_text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        screen.blit(prompt_text, prompt_text.get_rect(center=(WIDTH//2, HEIGHT//1.5)))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return

# --- Helper functions ---
def get_rank(combo):
    if combo >= 20:
        return "SSS"
    elif combo >= 15:
        return "SS"
    elif combo >= 10:
        return "S"
    elif combo >= 7:
        return "A"
    elif combo >= 4:
        return "B"
    elif combo >= 2:
        return "C"
    else:
        return "D"

def get_score_multiplier(rank):
    return {
        "D": 1, "C": 1, "B": 1, "A": 2, "S": 3, "SS": 4, "SSS": 5
    }.get(rank, 1)

def get_spawn_interval(rank):
    intervals = {
        "D": 1500,
        "C": 1350,
        "B": 1200,
        "A": 1000,
        "S": 850,
        "SS": 700,
        "SSS": 600
    }
    return intervals.get(rank, 1500)

def spawn_monster():
    side = random.choice(["left", "right"])
    y = player_pos[1]
    x = -monster_size if side == "left" else WIDTH
    direction = 1 if side == "left" else -1
    monsters.append({"pos": [x, y], "dir": direction})

def spawn_falling_object():
    x = random.randint(0, WIDTH - fall_size)
    y = -fall_size
    falling_objects.append([x, y])

def draw_player():
    screen.blit(player_img, player_pos)

def draw_sword(angle, thrust, pivot_offset_y):
    flipped = -1 if facing == "left" else 1
    rotated = pygame.transform.rotate(sword_img, -angle * flipped)
    offset_x = (90 + int(thrust)) * flipped
    offset_y = -10 + int(pivot_offset_y)
    center = (player_pos[0] + 48 + offset_x, player_pos[1] + 48 + offset_y)
    rect = rotated.get_rect(center=center)
    screen.blit(rotated, rect.topleft)
    return rect

def draw_monsters():
    for m in monsters:
        pygame.draw.rect(screen, (200, 50, 50), (m["pos"][0], m["pos"][1], monster_size, monster_size))

def move_monsters():
    for m in monsters[:]:
        m["pos"][0] += m["dir"] * monster_speed
        if m["pos"][0] < -monster_size or m["pos"][0] > WIDTH + monster_size:
            monsters.remove(m)

def check_monster_collision():
    global lives, combo, game_over
    player_rect = pygame.Rect(player_pos[0], player_pos[1], 96, 96)
    for m in monsters[:]:
        monster_rect = pygame.Rect(m['pos'][0], m['pos'][1], monster_size, monster_size)
        if monster_rect.colliderect(player_rect):
            monsters.remove(m)
            lives -= 1
            combo = 0
            if lives <= 0:
                game_over = True

def draw_falling_objects():
    for f in falling_objects:
        pygame.draw.rect(screen, (100, 100, 100), (f[0], f[1], fall_size, fall_size))

def move_falling_objects():
    global lives, combo, game_over
    for f in falling_objects[:]:
        f[1] += fall_speed
        player_rect = pygame.Rect(player_pos[0], player_pos[1], 96, 96)
        fall_rect = pygame.Rect(f[0], f[1], fall_size, fall_size)
        if f[1] > HEIGHT:
            falling_objects.remove(f)
        elif fall_rect.colliderect(player_rect):
            falling_objects.remove(f)
            lives -= 1
            combo = 0
            if lives <= 0:
                game_over = True

def check_collision(sword_rect, now):
    global score, combo, last_kill_time
    if sword_rect and swing_phase == "swing":
        for m in monsters[:]:
            monster_rect = pygame.Rect(m["pos"][0], m["pos"][1], monster_size, monster_size)
            if sword_rect.colliderect(monster_rect):
                monsters.remove(m)
                combo += 1
                rank = get_rank(combo)
                score += get_score_multiplier(rank)
                last_kill_time = now

def show_ui():
    rank = get_rank(combo)

    # Lives (hearts)
    for i in range(lives):
        screen.blit(heart_img, (10 + i * 28, 10))

    # Score (numbers)
    score_str = str(score)
    for i, digit_char in enumerate(score_str):
        digit = int(digit_char)
        screen.blit(digit_images[digit], (10 + i * 22, 40))

    # Rank (top-right)
    icon = pygame.transform.scale(rank_images[rank], (100, 100))
    icon_rect = icon.get_rect(topright=(WIDTH - 10, 10))
    screen.blit(icon, icon_rect.topleft)

def show_game_over():
    game_over_text = font.render("Game Over", True, BLACK)
    restart_text = font.render("R: Neustart", True, BLACK)
    menu_text = font.render("M: Hauptmenü", True, BLACK)

    screen.blit(game_over_text, game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
    screen.blit(restart_text, restart_text.get_rect(center=(WIDTH//2, HEIGHT//2)))
    screen.blit(menu_text, menu_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))

# --- Initialize database ---
init_db()

# --- Show start menu ---
show_start_menu()

# --- Game Loop ---
running = True
while running:
    dt = clock.tick(60)
    now = pygame.time.get_ticks()
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if game_over:
        screen.blit(background_img, (0, 0))
        show_game_over()
        pygame.display.flip()

        # Highscore prüfen und ggf. aktualisieren
        if score > get_highscore():
            update_highscore(score)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Neustart
                    lives = 3
                    score = 0
                    combo = 0
                    monsters.clear()
                    falling_objects.clear()
                    swing_phase = "idle"
                    game_over = False
                elif event.key == pygame.K_m:
                    # Zurück ins Hauptmenü
                    show_start_menu()
                    lives = 3
                    score = 0
                    combo = 0
                    monsters.clear()
                    falling_objects.clear()
                    swing_phase = "idle"
                    game_over = False
        continue

    if now - last_kill_time > 3000:
        combo = 0

    if swing_phase == "idle":
        if keys[pygame.K_LEFT]:
            player_pos[0] -= player_speed
            facing, player_img = "left", player_img_left
        if keys[pygame.K_RIGHT]:
            player_pos[0] += player_speed
            facing, player_img = "right", player_img_right

    if keys[pygame.K_SPACE] and swing_phase == "idle":
        swing_phase = "swing"
        swing_start_ms = now

    elapsed = now - swing_start_ms
    if swing_phase == "swing":
        t = min(elapsed / swing_duration, 1.0)
        swing_angle = t * max_swing_angle
        thrust_offset = t * max_thrust
        pivot_drop = t * max_pivot_drop
        if elapsed >= swing_duration:
            swing_phase = "rest"
            swing_start_ms = now
    elif swing_phase == "rest":
        swing_angle = max_swing_angle
        thrust_offset = max_thrust
        pivot_drop = max_pivot_drop
        if elapsed >= rest_duration:
            swing_phase = "retract"
            swing_start_ms = now
    elif swing_phase == "retract":
        t = 1 - min(elapsed / retract_duration, 1.0)
        swing_angle = t * max_swing_angle
        thrust_offset = t * max_thrust
        pivot_drop = t * max_pivot_drop
        if elapsed >= retract_duration:
            swing_phase = "idle"
            swing_angle = 0
            thrust_offset = 0
            pivot_drop = 0

    screen.blit(background_img, (0, 0))
    draw_player()
    sword_rect = draw_sword(swing_angle, thrust_offset, pivot_drop)
    draw_monsters()
    draw_falling_objects()
    move_monsters()
    move_falling_objects()
    check_monster_collision()
    check_collision(sword_rect, now)

    # Monster spawn
    rank = get_rank(combo)
    spawn_interval = get_spawn_interval(rank)
    if now - last_monster_spawn > spawn_interval and len(monsters) < MAX_MONSTERS:
        spawn_monster()
        last_monster_spawn = now

    # Falling objects spawn
    if random.random() < fall_spawn_chance:
        spawn_falling_object()

    show_ui()

    pygame.display.flip()

pygame.quit()