import pygame
import sys
import random

pygame.init()
BASE_WIDTH, BASE_HEIGHT = 800, 400
WIDTH, HEIGHT = BASE_WIDTH, BASE_HEIGHT
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
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
DIFFICULTY_SPEED = {"E": 4, "C": 6, "A": 6}

stars = [(random.randint(0, BASE_WIDTH), random.randint(0, BASE_HEIGHT)) for _ in range(150)]

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 7

    def draw(self, surface):
        pygame.draw.rect(surface, NEON_BLUE, self.rect)

    def move(self, up=True):
        if up:
            self.rect.y -= self.speed
        else:
            self.rect.y += self.speed
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > BASE_HEIGHT: self.rect.bottom = BASE_HEIGHT

class Ball:
    def __init__(self, difficulty="E"):
        self.rect = pygame.Rect(BASE_WIDTH//2, BASE_HEIGHT//2, BALL_SIZE, BALL_SIZE)
        self.difficulty = difficulty
        self.reset()

    def reset(self):
        self.rect.center = (BASE_WIDTH//2, BASE_HEIGHT//2)
        self.speed_x = random.choice([-1, 1]) * random.randint(4, 6)
        self.speed_y = random.choice([-1, 1]) * random.randint(2, 4)
        self.base_speed = DIFFICULTY_SPEED[self.difficulty]

    def draw(self, surface):
        pygame.draw.rect(surface, GREEN, self.rect)

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.top <= 0 or self.rect.bottom >= BASE_HEIGHT:
            self.speed_y *= -1
        if self.difficulty == "A":  # Accelerating mode
            if abs(self.speed_x) < 15:
                self.speed_x *= 1.001
            if abs(self.speed_y) < 15:
                self.speed_y *= 1.001

def draw_window(surface, paddle1, paddle2, ball, score1, score2):
    surface.fill((0, 0, 0))  # Black background
    for star in stars:
        pygame.draw.circle(surface, STAR_COLOR, star, 1)
    for y in range(0, BASE_HEIGHT, 20):
        pygame.draw.rect(surface, WHITE, (BASE_WIDTH//2 - 1, y, 2, 10))
    paddle1.draw(surface)
    paddle2.draw(surface)
    ball.draw(surface)
    score_text = FONT.render(f"{score1}  |  {score2}", True, WHITE)
    surface.blit(score_text, (BASE_WIDTH//2 - score_text.get_width()//2, 10))

def main_game(difficulty="E", max_points=5, two_player=True):
    global WIDTH, HEIGHT, WIN
    clock = pygame.time.Clock()
    base_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

    paddle1 = Paddle(20, BASE_HEIGHT//2 - PADDLE_HEIGHT//2)
    paddle2 = Paddle(BASE_WIDTH - 30, BASE_HEIGHT//2 - PADDLE_HEIGHT//2)
    ball = Ball(difficulty)

    score1, score2 = 0, 0
    run = True
    paused = False

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                paused = True
            if event.type == pygame.KEYDOWN and paused:
                if event.key == pygame.K_RETURN:
                    paused = False

        if paused:
            base_surface.fill((0, 0, 0))
            pause_text = FONT.render("RESIZED - Press ENTER to Resume", True, GREEN)
            base_surface.blit(pause_text, (BASE_WIDTH//2 - pause_text.get_width()//2,
                                           BASE_HEIGHT//2 - pause_text.get_height()//2))
        else:
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

            if ball.rect.colliderect(paddle1.rect): ball.speed_x *= -1
            if ball.rect.colliderect(paddle2.rect): ball.speed_x *= -1

            if ball.rect.left <= 0:
                score2 += 1
                ball.reset()
            if ball.rect.right >= BASE_WIDTH:
                score1 += 1
                ball.reset()

            draw_window(base_surface, paddle1, paddle2, ball, score1, score2)

            if score1 >= max_points:
                winner_text = "PLAYER 1 WINS!"
                run = False
            elif score2 >= max_points:
                winner_text = "PLAYER 2 WINS!" if two_player else "AI WINS!"
                run = False

        # Scale everything to window size
        scaled_surface = pygame.transform.smoothscale(base_surface, (WIDTH, HEIGHT))
        WIN.blit(scaled_surface, (0, 0))
        pygame.display.update()

    # Display winner
    base_surface.fill((0, 0, 0))
    text = FONT.render(winner_text, True, GREEN)
    base_surface.blit(text, (BASE_WIDTH//2 - text.get_width()//2, BASE_HEIGHT//2 - text.get_height()//2))
    scaled_surface = pygame.transform.smoothscale(base_surface, (WIDTH, HEIGHT))
    WIN.blit(scaled_surface, (0, 0))
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

