import pygame
import math
import os

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Magic Sword Swing")

clock = pygame.time.Clock()

# Load images
player_right = pygame.image.load("player_right.png").convert_alpha()
player_left = pygame.image.load("player_left.png").convert_alpha()
sword_img = pygame.image.load("sword.png").convert_alpha()

# Resize if needed
PLAYER_SIZE = (96, 96)
SWORD_SIZE = (96, 128)
player_right = pygame.transform.scale(player_right, PLAYER_SIZE)
player_left = pygame.transform.scale(player_left, PLAYER_SIZE)
sword_img = pygame.transform.scale(sword_img, SWORD_SIZE)

# Player settings
player_pos = [WIDTH // 2, HEIGHT // 2]
player_speed = 6
facing = "right"

# Sword settings
swinging = False
swing_duration = 400  # ms
swing_start_time = 0
max_angle = 120

score = 0
font = pygame.font.SysFont(None, 36)

# Enemies
enemy_size = 50
enemy_speed = 3
enemies = []

def spawn_enemy():
    x = -enemy_size if facing == "right" else WIDTH
    y = player_pos[1]
    direction = 1 if x < WIDTH // 2 else -1
    enemies.append({'pos': [x, y], 'dir': direction})

def draw_player():
    if facing == "right":
        screen.blit(player_right, player_pos)
    else:
        screen.blit(player_left, player_pos)

def draw_enemies():
    for e in enemies:
        pygame.draw.rect(screen, (200, 50, 50), (*e['pos'], enemy_size, enemy_size))

def move_enemies():
    for e in enemies[:]:
        e['pos'][0] += e['dir'] * enemy_speed
        if e['pos'][0] < -enemy_size or e['pos'][0] > WIDTH + enemy_size:
            enemies.remove(e)

def draw_sword(angle):
    # Sword pivot point is offset from player
    offset_x = 60 if facing == "right" else -60
    pivot = (player_pos[0] + PLAYER_SIZE[0] // 2 + offset_x, player_pos[1] + PLAYER_SIZE[1] // 2)

    # Create rotated sword
    rotated_sword = pygame.transform.rotate(sword_img, -angle if facing == "right" else angle)
    sword_rect = rotated_sword.get_rect(center=pivot)
    screen.blit(rotated_sword, sword_rect.topleft)
    return sword_rect

def check_collision(sword_rect):
    global score
    for e in enemies[:]:
        enemy_rect = pygame.Rect(*e['pos'], enemy_size, enemy_size)
        if sword_rect.colliderect(enemy_rect):
            enemies.remove(e)
            score += 1

def show_score():
    text = font.render(f"Punkte: {score}", True, (0, 0, 0))
    screen.blit(text, (10, 10))

running = True
while running:
    dt = clock.tick(60)
    screen.fill((230, 230, 230))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # Movement
    if keys[pygame.K_LEFT]:
        player_pos[0] -= player_speed
        facing = "left"
    if keys[pygame.K_RIGHT]:
        player_pos[0] += player_speed
        facing = "right"

    # Sword swing
    now = pygame.time.get_ticks()
    if keys[pygame.K_SPACE] and not swinging:
        swinging = True
        swing_start_time = now

    # Animate sword
    angle = 0
    if swinging:
        elapsed = now - swing_start_time
        if elapsed < swing_duration:
            progress = elapsed / swing_duration
            angle = max_angle * math.sin(progress * math.pi)  # smooth swing curve
        else:
            swinging = False

    # Game logic
    if pygame.time.get_ticks() % 1000 < 20:
        spawn_enemy()

    move_enemies()
    draw_enemies()
    draw_player()
    sword_rect = draw_sword(angle)
    check_collision(sword_rect)
    show_score()
    pygame.display.flip()

pygame.quit()
