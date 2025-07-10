import pygame
import random
import sqlite3
import time
import math  # Added for levitating effect

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Magic Sword vs Monsters")
clock = pygame.time.Clock()

WHITE, BLACK, RED = (255, 255, 255), (0, 0, 0), (255, 0, 0)

# Images
background_img = pygame.transform.scale(pygame.image.load("background.png").convert(), (WIDTH, HEIGHT))
player_img_right = pygame.transform.scale(pygame.image.load("player_right.png").convert_alpha(), (96, 96))
player_img_left = pygame.transform.scale(pygame.image.load("player_left.png").convert_alpha(), (96, 96))
sword_img = pygame.transform.scale(pygame.image.load("sword.png").convert_alpha(), (64, 128))
arrow_img = pygame.transform.scale(pygame.image.load("arrow.png").convert_alpha(), (40, 40))

heart_img = pygame.transform.scale(pygame.image.load("heart.png").convert_alpha(), (24, 24))
digit_images = [pygame.transform.scale(pygame.image.load(f"digit_{i}.png").convert_alpha(), (20, 28)) for i in range(10)]

rank_images = {rank: pygame.image.load(f"rank_{rank}.png").convert_alpha() for rank in ["D", "C", "B", "A", "S", "SS", "SSS"]}

monster_textures = [
    pygame.image.load("monster_ghost.png").convert_alpha(),
    pygame.image.load("monster_skull.png").convert_alpha()
]

# Player
player_img = player_img_right
facing = "right"
player_pos = [WIDTH // 2, HEIGHT - 150]
player_speed = 5
lives = 3

# Sword animation
swing_phase, swing_angle, thrust_offset, pivot_drop = "idle", 0, 0, 0
swing_start_ms = 0
swing_duration = 150
rest_duration = 250
retract_duration = 200
max_swing_angle, max_thrust, max_pivot_drop = 100, 25, 30

# Enemies
monster_size = 60
monster_speed = 3
monsters = []
MAX_MONSTERS = 5
last_monster_spawn = 0

# Arrows
falling_objects = []
fall_speed = 4
fall_spawn_chance = 0.002
fall_size = 40

# Score + combo
score = 0
combo = 0
last_kill_time = 0
font = pygame.font.SysFont(None, 36)

# Shockwave
shockwave_active = False
shockwave_time = 0
shockwave_radius = 0
shockwave_center = (0, 0)
shockwave_cooldown = 4000
last_shockwave_time = -shockwave_cooldown
shake_start_time = None
shake_duration = 300
shake_intensity = 5

# Game state
game_over = False

# DB
def init_db():
    with sqlite3.connect("highscore.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS highscores (id INTEGER PRIMARY KEY AUTOINCREMENT, score INTEGER NOT NULL)''')

def get_highscore():
    with sqlite3.connect("highscore.db") as conn:
        return conn.execute('SELECT MAX(score) FROM highscores').fetchone()[0] or 0

def update_highscore(new_score):
    if new_score > get_highscore():
        with sqlite3.connect("highscore.db") as conn:
            conn.execute('INSERT INTO highscores (score) VALUES (?)', (new_score,))

# UI
def get_rank(combo):
    if combo >= 20: return "SSS"
    elif combo >= 15: return "SS"
    elif combo >= 10: return "S"
    elif combo >= 7: return "A"
    elif combo >= 4: return "B"
    elif combo >= 2: return "C"
    return "D"

def get_score_multiplier(rank):
    return {"D": 1, "C": 1, "B": 1, "A": 2, "S": 3, "SS": 4, "SSS": 5}[rank]

def get_spawn_interval(rank):
    return {"D": 1500, "C": 1350, "B": 1200, "A": 1000, "S": 850, "SS": 700, "SSS": 600}[rank]

def show_start_menu():
    highscore = get_highscore()
    title_font = pygame.font.SysFont(None, 72)
    info_font = pygame.font.SysFont(None, 36)
    while True:
        screen.fill(WHITE)
        screen.blit(title_font.render("Magic Sword vs Monsters", True, BLACK), (WIDTH//4, HEIGHT//4))
        screen.blit(info_font.render("Press SPACE to Start", True, BLACK), (WIDTH//3, HEIGHT//2))
        screen.blit(info_font.render(f"Highscore: {highscore}", True, BLACK), (WIDTH//3, HEIGHT//1.7))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: return

# Game helpers
def spawn_monster():
    side = random.choice(["left", "right"])
    y = player_pos[1]
    x = -monster_size if side == "left" else WIDTH
    direction = 1 if side == "left" else -1
    img = pygame.transform.scale(random.choice(monster_textures), (monster_size, monster_size))
    if direction == -1: img = pygame.transform.flip(img, True, False)
    monsters.append({"pos": [x, y], "dir": direction, "img": img, "stun_timer": 0, "knockback": 0})

def spawn_falling_object():
    falling_objects.append([random.randint(0, WIDTH - fall_size), -fall_size])

def draw_player():
    t = pygame.time.get_ticks() / 300.0
    levitate = int(3 * math.sin(t))
    screen.blit(player_img, (player_pos[0], player_pos[1] + levitate))

def draw_sword(angle, thrust, pivot_y):
    flipped = -1 if facing == "left" else 1
    rotated = pygame.transform.rotate(sword_img, -angle * flipped)
    offset_x, offset_y = (90 + int(thrust)) * flipped, -10 + int(pivot_y)
    levitate = int(3 * math.sin(pygame.time.get_ticks() / 300.0))
    rect = rotated.get_rect(center=(player_pos[0] + 48 + offset_x, player_pos[1] + 48 + offset_y + levitate))
    screen.blit(rotated, rect.topleft)
    return rect

def draw_monsters():
    t = pygame.time.get_ticks() / 300.0
    levitate = int(2 * math.sin(t))
    for m in monsters:
        screen.blit(m["img"], (m["pos"][0], m["pos"][1] + levitate))

def move_monsters():
    for m in monsters[:]:
        if m["stun_timer"] > 0: m["stun_timer"] -= 1; continue
        if m["knockback"] > 0: m["pos"][0] += m["dir"] * -3; m["knockback"] -= 1
        else: m["pos"][0] += m["dir"] * monster_speed
        if m["pos"][0] < -monster_size or m["pos"][0] > WIDTH + monster_size:
            monsters.remove(m)

def check_monster_collision():
    global lives, combo, game_over
    player_rect = pygame.Rect(player_pos[0], player_pos[1], 96, 96)
    for m in monsters[:]:
        if pygame.Rect(m["pos"][0], m["pos"][1], monster_size, monster_size).colliderect(player_rect):
            monsters.remove(m)
            lives -= 1; combo = 0
            if lives <= 0: game_over = True

def draw_falling_objects():
    for f in falling_objects:
        screen.blit(arrow_img, (f[0], f[1]))

def move_falling_objects():
    global lives, combo, game_over
    for f in falling_objects[:]:
        f[1] += fall_speed
        if f[1] > HEIGHT: falling_objects.remove(f)
        elif pygame.Rect(f[0], f[1], fall_size, fall_size).colliderect(pygame.Rect(player_pos[0], player_pos[1], 96, 96)):
            falling_objects.remove(f); lives -= 1; combo = 0
            if lives <= 0: game_over = True

def check_collision(sword_rect, now):
    global score, combo, last_kill_time
    if sword_rect and swing_phase == "swing":
        for m in monsters[:]:
            if pygame.Rect(m["pos"][0], m["pos"][1], monster_size, monster_size).colliderect(sword_rect):
                monsters.remove(m)
                combo += 1
                score += get_score_multiplier(get_rank(combo))
                last_kill_time = now

def show_ui():
    for i in range(lives): screen.blit(heart_img, (10 + i * 28, 10))
    for i, digit in enumerate(str(score)): screen.blit(digit_images[int(digit)], (10 + i * 22, 40))
    screen.blit(pygame.transform.scale(rank_images[get_rank(combo)], (100, 100)), (WIDTH - 110, 10))

def show_game_over():
    text = font.render("Game Over - Press R to Restart", True, BLACK)
    screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))

def get_shake_offset(current_time):
    if shake_start_time and (current_time - shake_start_time) < shake_duration:
        return random.randint(-shake_intensity, shake_intensity), random.randint(-shake_intensity, shake_intensity)
    return 0, 0

# --- Start ---
init_db()
show_start_menu()

running = True
while running:
    dt = clock.tick(60)
    now = pygame.time.get_ticks()
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    if game_over:
        screen.blit(background_img, (0, 0))
        show_game_over()
        pygame.display.flip()
        if score > get_highscore(): update_highscore(score)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                lives = 3; score = 0; combo = 0
                monsters.clear(); falling_objects.clear()
                swing_phase = "idle"; game_over = False
        continue

    if now - last_kill_time > 3000: combo = 0

    if swing_phase == "idle":
        if keys[pygame.K_LEFT]: player_pos[0] -= player_speed; facing, player_img = "left", player_img_left
        if keys[pygame.K_RIGHT]: player_pos[0] += player_speed; facing, player_img = "right", player_img_right
        if keys[pygame.K_LSHIFT] and (now - last_shockwave_time >= shockwave_cooldown):
            shockwave_active = True
            shockwave_time = now
            shockwave_radius = 0
            shockwave_center = (player_pos[0] + 48, player_pos[1] + 48)
            last_shockwave_time = now
            shake_start_time = now

    if keys[pygame.K_SPACE] and swing_phase == "idle":
        swing_phase = "swing"; swing_start_ms = now

    elapsed = now - swing_start_ms
    if swing_phase == "swing":
        t = min(elapsed / swing_duration, 1)
        swing_angle, thrust_offset, pivot_drop = t * max_swing_angle, t * max_thrust, t * max_pivot_drop
        if elapsed >= swing_duration: swing_phase, swing_start_ms = "rest", now
    elif swing_phase == "rest":
        if elapsed >= rest_duration: swing_phase, swing_start_ms = "retract", now
    elif swing_phase == "retract":
        t = 1 - min(elapsed / retract_duration, 1)
        swing_angle, thrust_offset, pivot_drop = t * max_swing_angle, t * max_thrust, t * max_pivot_drop
        if elapsed >= retract_duration: swing_phase = "idle"; swing_angle = thrust_offset = pivot_drop = 0

    if shockwave_active:
        shockwave_radius += 10
        if shockwave_radius > 300: shockwave_active = False
        for m in monsters:
            dist = pygame.math.Vector2(m["pos"][0] + 30 - shockwave_center[0], m["pos"][1] + 30 - shockwave_center[1]).length()
            if dist < shockwave_radius:
                m["stun_timer"] = int(1.5 * 60)
                m["knockback"] = 12

    # --- Drawing ---
    shake_x, shake_y = get_shake_offset(now)
    screen.blit(background_img, (shake_x, shake_y))
    draw_player()
    sword_rect = draw_sword(swing_angle, thrust_offset, pivot_drop)
    draw_monsters()
    draw_falling_objects()

    if shockwave_active:
        pygame.draw.circle(screen, RED, (shockwave_center[0] + shake_x, shockwave_center[1] + shake_y), shockwave_radius, 2)

    move_monsters()
    move_falling_objects()
    check_monster_collision()
    check_collision(sword_rect, now)

    if now - last_monster_spawn > get_spawn_interval(get_rank(combo)) and len(monsters) < MAX_MONSTERS:
        spawn_monster(); last_monster_spawn = now

    if random.random() < fall_spawn_chance: spawn_falling_object()

    show_ui()
    pygame.display.flip()

pygame.quit()
