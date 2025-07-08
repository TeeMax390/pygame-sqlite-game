import pygame
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Schwert vs Monster")

clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)

player_pos = [WIDTH // 2, HEIGHT - 80]
player_size = 50
player_speed = 7

sword_length = 40
sword_width = 20
sword_cooldown = 500  # ms
last_swing = 0

monster_size = 50
monster_speed = 3
monsters = []

score = 0
font = pygame.font.SysFont(None, 36)

# Spieler blickrichtung (startet nach rechts)
facing = "right"

def spawn_monster():
    side = random.choice(['left', 'right'])
    y = player_pos[1]
    if side == 'left':
        x = -monster_size
        direction = 1
    else:
        x = WIDTH
        direction = -1
    monsters.append({'pos': [x, y], 'dir': direction})

def draw_player():
    pygame.draw.rect(screen, BLUE, (player_pos[0], player_pos[1], player_size, player_size))

def draw_sword(swinging):
    if swinging:
        if facing == "right":
            # Schwert rechts vom Spieler
            sword_rect = pygame.Rect(player_pos[0] + player_size, player_pos[1] + player_size//4, sword_length, sword_width)
        else:
            # Schwert links vom Spieler
            sword_rect = pygame.Rect(player_pos[0] - sword_length, player_pos[1] + player_size//4, sword_length, sword_width)
        pygame.draw.rect(screen, GREEN, sword_rect)
        return sword_rect
    return None

def draw_monsters():
    for m in monsters:
        pygame.draw.rect(screen, RED, (m['pos'][0], m['pos'][1], monster_size, monster_size))

def move_monsters():
    for m in monsters[:]:
        m['pos'][0] += m['dir'] * monster_speed
        if m['pos'][0] < -monster_size or m['pos'][0] > WIDTH + monster_size:
            monsters.remove(m)

def check_collision(sword_rect):
    global score
    if sword_rect:
        for m in monsters[:]:
            monster_rect = pygame.Rect(m['pos'][0], m['pos'][1], monster_size, monster_size)
            if sword_rect.colliderect(monster_rect):
                monsters.remove(m)
                score += 1

def show_score():
    text = font.render(f"Punkte: {score}", True, BLACK)
    screen.blit(text, (10, 10))

running = True
while running:
    dt = clock.tick(60)
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    moved = False
    if keys[pygame.K_LEFT] and player_pos[0] > 0:
        player_pos[0] -= player_speed
        facing = "left"
        moved = True
    if keys[pygame.K_RIGHT] and player_pos[0] < WIDTH - player_size:
        player_pos[0] += player_speed
        facing = "right"
        moved = True

    # Monster seltener spawnen lassen
    if random.random() < 0.01:
        spawn_monster()

    move_monsters()
    draw_monsters()

    current_time = pygame.time.get_ticks()
    swinging = False
    if keys[pygame.K_SPACE] and current_time - last_swing > sword_cooldown:
        swinging = True
        last_swing = current_time

    sword_rect = draw_sword(swinging)
    draw_player()

    check_collision(sword_rect)
    show_score()

    pygame.display.flip()

pygame.quit()
