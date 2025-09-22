import pygame
import sys
import random
import json

pygame.init()
WIDTH, HEIGHT = 800, 400
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)  # Screen resize support
pygame.display.set_caption("Pixel Ping Pong - Space Edition")
FPS = 60

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
STAR_COLOR = (200, 200, 255)
NEON_BLUE = (0, 255, 255)
POWERUP_COLORS = {"speed": (255, 100, 100), "grow": (100, 255, 100), "ball": (100, 100, 255), "shield": (255, 255, 100)}

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

# Custom control issue: customizable controls
controls = {"p1_up": pygame.K_w, "p1_down": pygame.K_s, "p2_up": pygame.K_UP, "p2_down": pygame.K_DOWN, "pause": pygame.K_p}

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 7
        self.shield = False  # issue: shield powerup

    def draw(self):
        color = NEON_BLUE if not self.shield else (255, 255, 0)  # highlight shield
        pygame.draw.rect(WIN, color, self.rect)

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
        # Accelerate for A difficulty
        if self.difficulty == "A":
            if abs(self.speed_x) < 15:
                self.speed_x *= 1.001
            if abs(self.speed_y) < 15:
                self.speed_y *= 1.001

class PowerUp:  # issue:powerups
    def __init__(self):
        self.type = random.choice(["speed", "grow", "ball", "shield"])
        self.rect = pygame.Rect(random.randint(100, WIDTH-100), random.randint(50, HEIGHT-50), 15, 15)
        self.active = True
        self.duration = 300  # frames (5 seconds)

    def draw(self):
        if self.active:
            pygame.draw.rect(WIN, POWERUP_COLORS[self.type], self.rect)

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
        pu.draw()
    score_text = FONT.render(f"{score1}  |  {score2}", True, WHITE)
    WIN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 10))
    pygame.display.update()

def apply_powerup(paddle, ball, powerup):  # issue: powerup effect
    if powerup.type == "speed":
        paddle.speed += 3
    elif powerup.type == "grow":
        paddle.rect.height += 20
    elif powerup.type == "ball":
        ball.speed_x *= 0.8
        ball.speed_y *= 0.8
    elif powerup.type == "shield":
        paddle.shield = True

def reset_powerup_effects(paddle, ball, powerup):  # issue: reset powerups
    if powerup.type == "speed":
        paddle.speed -= 3
    elif powerup.type == "grow":
        paddle.rect.height -= 20
    elif powerup.type == "ball":
        ball.speed_x /= 0.8
        ball.speed_y /= 0.8
    elif powerup.type == "shield":
        paddle.shield = False

def save_highscore(name, score):  # issue: leaderboard
    try:
        with open("highscores.json", "r") as f:
            data = json.load(f)
    except:
        data = []
    data.append({"name": name, "score": score})
    data = sorted(data, key=lambda x: x["score"], reverse=True)[:5]
    with open("highscores.json", "w") as f:
        json.dump(data, f)

def show_leaderboard():  # issue: leaderboard display
    try:
        with open("highscores.json", "r") as f:
            data = json.load(f)
    except:
        data = []
    WIN.fill((0, 0, 0))
    title = FONT.render("LEADERBOARD", True, GREEN)
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    for i, entry in enumerate(data):
        text = MENU_FONT.render(f"{i+1}. {entry['name']} - {entry['score']}", True, WHITE)
        WIN.blit(text, (WIDTH//2 - text.get_width()//2, 120 + i*40))
    pygame.display.update()
    pygame.time.delay(3000)

def main_game(difficulty="E", max_points=5, two_player=True):
    clock = pygame.time.Clock()
    paddle1 = Paddle(20, HEIGHT//2 - PADDLE_HEIGHT//2)
    paddle2 = Paddle(WIDTH - 30, HEIGHT//2 - PADDLE_HEIGHT//2)
    ball = Ball(difficulty)
    powerups = []

    score1, score2 = 0, 0
    run = True
    point_pause = 0  # issue: score delay

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:  # issue: resize
                global WIDTH, HEIGHT, WIN
                WIDTH, HEIGHT = event.w, event.h
                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

        keys = pygame.key.get_pressed()
        if keys[controls["p1_up"]]: paddle1.move(up=True)
        if keys[controls["p1_down"]]: paddle1.move(up=False)
        if two_player:
            if keys[controls["p2_up"]]: paddle2.move(up=True)
            if keys[controls["p2_down"]]: paddle2.move(up=False)
        else:
            if paddle2.rect.centery < ball.rect.centery: paddle2.move(up=False)
            elif paddle2.rect.centery > ball.rect.centery: paddle2.move(up=True)

        if keys[controls["pause"]]:  # issue: pause
            paused = True
            while paused:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == controls["pause"]:
                            paused = False
                pause_text = FONT.render("PAUSED", True, GREEN)
                WIN.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2))
                pygame.display.update()

        if point_pause > 0:
            point_pause -= 1
            continue  # pause after score

        ball.move()

        # Ball collision with paddles
        if ball.rect.colliderect(paddle1.rect):
            ball.speed_x *= -1
        if ball.rect.colliderect(paddle2.rect):
            ball.speed_x *= -1

        # Powerup collection
        if random.randint(1, 600) == 1:  # once every 10s
            powerups.append(PowerUp())
        for pu in powerups:
            if pu.active and (paddle1.rect.colliderect(pu.rect) or paddle2.rect.colliderect(pu.rect) or ball.rect.colliderect(pu.rect)):
                if paddle1.rect.colliderect(pu.rect):
                    apply_powerup(paddle1, ball, pu)
                if paddle2.rect.colliderect(pu.rect):
                    apply_powerup(paddle2, ball, pu)
                pu.active = False

        # Score update
        if ball.rect.left <= 0:
            if not paddle1.shield: score2 += 1
            ball.reset()
            point_pause = 120  # 2 seconds
        if ball.rect.right >= WIDTH:
            if not paddle2.shield: score1 += 1
            ball.reset()
            point_pause = 120

        # Update powerup durations
        for pu in powerups:
            if not pu.active and pu.duration > 0:
                pu.duration -= 1
                if pu.duration == 0:
                    reset_powerup_effects(paddle1, ball, pu)
                    reset_powerup_effects(paddle2, ball, pu)

        draw_window(paddle1, paddle2, ball, score1, score2, powerups)

        # Win check
        if score1 >= max_points:
            winner_text = "PLAYER 1 WINS!"
            run = False
        elif score2 >= max_points:
            winner_text = "PLAYER 2 WINS!" if two_player else "AI WINS!"
            run = False

    # Display winner and leaderboard
    WIN.fill((0, 0, 0))
    text = FONT.render(winner_text, True, GREEN)
    WIN.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
    pygame.display.update()
    pygame.time.delay(3000)
    save_highscore("P1" if score1 >= score2 else "P2", max(score1, score2))
    show_leaderboard()

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
                if event.key == pygame.K_UP:
                    if max_points < 20: max_points += 1
                if event.key == pygame.K_DOWN:
                    if max_points > 1: max_points -= 1

main_menu()
