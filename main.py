import pygame
import sys
import random

pygame.init()
WIDTH, HEIGHT = 800, 400
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixel Ping Pong - Space Edition")
FPS = 60

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
STAR_COLOR = (200, 200, 255)
NEON_BLUE = (0, 255, 255)

try:
    FONT = pygame.font.Font("PressStart2P.ttf", 30)
    MENU_FONT = pygame.font.Font("PressStart2P.ttf", 20)
except:
    FONT = pygame.font.SysFont("Courier", 30)
    MENU_FONT = pygame.font.SysFont("Courier", 20)

PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10
DIFFICULTY_SPEED = {"E": 5, "C": 8, "A": 5}

stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(150)]

# --- Power-up constants and class ---
POWER_UP_SIZE = 15
POWER_UP_DURATION = 300  # frames (~5 sec)
POWER_UP_TYPES = ["speed_boost", "paddle_grow", "ball_speed", "shield"]

class PowerUp:
    def __init__(self):
        self.type = random.choice(POWER_UP_TYPES)
        self.rect = pygame.Rect(random.randint(50, WIDTH-50),
                                random.randint(50, HEIGHT-50),
                                POWER_UP_SIZE, POWER_UP_SIZE)
        self.active = True
        self.timer = 0

    def draw(self):
        color_map = {
            "speed_boost": (255, 255, 0),
            "paddle_grow": (0, 255, 0),
            "ball_speed": (255, 0, 0),
            "shield": (0, 255, 255)
        }
        pygame.draw.rect(WIN, color_map[self.type], self.rect)

    def update_timer(self):
        self.timer += 1
        if self.timer > POWER_UP_DURATION:
            self.active = False

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 7
        self.shield = 0  # for shield power-up

    def draw(self):
        pygame.draw.rect(WIN, NEON_BLUE, self.rect)

    def move(self, up=True):
        self.rect.y -= self.speed if up else -self.speed
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT

class Ball:
    def __init__(self, difficulty="E"):
        self.rect = pygame.Rect(WIDTH//2, HEIGHT//2, BALL_SIZE, BALL_SIZE)
        self.difficulty = difficulty
        self.reset()

    def reset(self):
        self.rect.center = (WIDTH//2, HEIGHT//2)
        self.speed_x = random.choice([-1, 1]) * random.randint(4, 6)
        self.speed_y = random.choice([-1, 1]) * random.randint(2, 4)
        self.base_speed = DIFFICULTY_SPEED[self.difficulty]

    def draw(self):
        pygame.draw.rect(WIN, GREEN, self.rect)

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.speed_y *= -1
        if self.difficulty == "A":
            if abs(self.speed_x) < 15: self.speed_x *= 1.001
            if abs(self.speed_y) < 15: self.speed_y *= 1.001

def draw_window(paddle1, paddle2, ball, score1, score2, powerups):
    WIN.fill((0, 0, 0))
    for star in stars:
        pygame.draw.circle(WIN, STAR_COLOR, star, 1)
    for y in range(0, HEIGHT, 20):
        pygame.draw.rect(WIN, WHITE, (WIDTH//2 - 1, y, 2, 10))
    paddle1.draw()
    paddle2.draw()
    ball.draw()
    for pu in powerups:
        if pu.active:
            pu.draw()
    score_text = FONT.render(f"{score1}  |  {score2}", True, WHITE)
    WIN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 10))
    pygame.display.update()

def main_game(difficulty="E", max_points=5, two_player=True):
    clock = pygame.time.Clock()
    paddle1 = Paddle(20, HEIGHT//2 - PADDLE_HEIGHT//2)
    paddle2 = Paddle(WIDTH - 30, HEIGHT//2 - PADDLE_HEIGHT//2)
    ball = Ball(difficulty)
    powerups = []
    powerup_timer = 0

    score1, score2 = 0, 0
    run = True

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Spawn power-ups randomly
        powerup_timer += 1
        if powerup_timer > random.randint(300, 600):
            powerups.append(PowerUp())
            powerup_timer = 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: paddle1.move(up=True)
        if keys[pygame.K_s]: paddle1.move(up=False)
        if two_player:
            if keys[pygame.K_UP]: paddle2.move(up=True)
            if keys[pygame.K_DOWN]: paddle2.move(up=False)
        else:
            if paddle2.rect.centery < ball.rect.centery: paddle2.move(up=False)
            elif paddle2.rect.centery > ball.rect.centery: paddle2.move(up=True)

        ball.move()

        # Ball collision with paddles
        if ball.rect.colliderect(paddle1.rect): ball.speed_x *= -1
        if ball.rect.colliderect(paddle2.rect): ball.speed_x *= -1

        # Check power-up collision
        for pu in powerups:
            if not pu.active: continue
            if paddle1.rect.colliderect(pu.rect):
                pu.active = False
                if pu.type == "speed_boost": paddle1.speed += 4
                elif pu.type == "paddle_grow": paddle1.rect.height += 20
                elif pu.type == "ball_speed": ball.speed_x *= 0.8; ball.speed_y *= 0.8
                elif pu.type == "shield": paddle1.shield = 120
            if paddle2.rect.colliderect(pu.rect):
                pu.active = False
                if pu.type == "speed_boost": paddle2.speed += 4
                elif pu.type == "paddle_grow": paddle2.rect.height += 20
                elif pu.type == "ball_speed": ball.speed_x *= 0.8; ball.speed_y *= 0.8
                elif pu.type == "shield": paddle2.shield = 120

            pu.update_timer()

        # Score update
        if ball.rect.left <= 0:
            if paddle1.shield <= 0: score2 += 1
            ball.reset()
        if ball.rect.right >= WIDTH:
            if paddle2.shield <= 0: score1 += 1
            ball.reset()

        # Reset effects gradually
        if paddle1.rect.height > PADDLE_HEIGHT: paddle1.rect.height -= 0.2
        if paddle2.rect.height > PADDLE_HEIGHT: paddle2.rect.height -= 0.2
        if paddle1.shield > 0: paddle1.shield -= 1
        if paddle2.shield > 0: paddle2.shield -= 1

        draw_window(paddle1, paddle2, ball, score1, score2, powerups)

        if score1 >= max_points:
            winner_text = "PLAYER 1 WINS!"
            run = False
        elif score2 >= max_points:
            winner_text = "PLAYER 2 WINS!" if two_player else "AI WINS!"
            run = False

    WIN.fill((0, 0, 0))
    text = FONT.render(winner_text, True, GREEN)
    WIN.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
    pygame.display.update()
    pygame.time.delay(3000)

def main_menu():
    run = True
    difficulty = "E"
    max_points = 5
    two_player = True

    while run:
        WIN.fill((0, 0, 0))
        title = FONT.render("PIXEL PING PONG", True, GREEN)
        WIN.blit(title, (WIDTH//2 - title.get_width()//2, 50))

        diff_text = MENU_FONT.render(f"Difficulty: {difficulty} (E/C/A)", True, WHITE)
        WIN.blit(diff_text, (WIDTH//2 - diff_text.get_width()//2, 150))

        points_text = MENU_FONT.render(f"Max Points: {max_points} (UP/DOWN)", True, WHITE)
        WIN.blit(points_text, (WIDTH//2 - points_text.get_width()//2, 200))

        mode_text = MENU_FONT.render(f"Mode: {'2 Player' if two_player else 'Single Player'} (M to toggle)", True, WHITE)
        WIN.blit(mode_text, (WIDTH//2 - mode_text.get_width()//2, 250))

        start_text = MENU_FONT.render("Press ENTER to Start", True, GREEN)
        WIN.blit(start_text, (WIDTH//2 - start_text.get_width()//2, 300))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    main_game(difficulty, max_points, two_player)
                if event.key == pygame.K_e: difficulty = "E"
                if event.key == pygame.K_c: difficulty = "C"
                if event.key == pygame.K_a: difficulty = "A"
                if event.key == pygame.K_m: two_player = not two_player
                if event.key == pygame.K_UP and max_points < 20: max_points += 1
                if event.key == pygame.K_DOWN and max_points > 1: max_points -= 1

main_menu()
