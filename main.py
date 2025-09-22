import pygame
import sys
import random

pygame.init()
WIDTH, HEIGHT = 800, 400
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
DIFFICULTY_SPEED = {"E": 5, "C": 8, "A": 5}

stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(150)]

# ----------------------- Scaling Helpers -----------------------
def scale_rect(rect, old_w, old_h, new_w, new_h):
    rect.x = int(rect.x * new_w / old_w)
    rect.y = int(rect.y * new_h / old_h)
    rect.width = int(rect.width * new_w / old_w)
    rect.height = int(rect.height * new_h / old_h)

def scale_ball(ball, old_w, old_h, new_w, new_h):
    ball.rect.x = int(ball.rect.x * new_w / old_w)
    ball.rect.y = int(ball.rect.y * new_h / old_h)

# ----------------------- Paddle Class -----------------------
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 7

    def draw(self):
        pygame.draw.rect(WIN, NEON_BLUE, self.rect)

    def move(self, up=True):
        self.rect.y -= self.speed if up else -self.speed
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT

# ----------------------- Ball Class -----------------------
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
            if abs(self.speed_x) < 15:
                self.speed_x *= 1.001
            if abs(self.speed_y) < 15:
                self.speed_y *= 1.001

# ----------------------- Draw Window -----------------------
def draw_window(paddle1, paddle2, ball, score1, score2):
    WIN.fill((0, 0, 0))
    for star in stars:
        pygame.draw.circle(WIN, STAR_COLOR, star, 1)
    for y in range(0, HEIGHT, 20):
        pygame.draw.rect(WIN, WHITE, (WIDTH//2 - 1, y, 2, 10))
    paddle1.draw()
    paddle2.draw()
    ball.draw()
    score_text = FONT.render(f"{score1}  |  {score2}", True, WHITE)
    WIN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 10))
    pygame.display.update()

# ----------------------- Main Game -----------------------
def main_game(difficulty="E", max_points=5, two_player=True):
    global stars, WIDTH, HEIGHT, WIN
    clock = pygame.time.Clock()
    paddle1 = Paddle(20, HEIGHT//2 - PADDLE_HEIGHT//2)
    paddle2 = Paddle(WIDTH - 30, HEIGHT//2 - PADDLE_HEIGHT//2)
    ball = Ball(difficulty)

    score1, score2 = 0, 0
    run = True

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                old_w, old_h = WIDTH, HEIGHT
                WIDTH, HEIGHT = event.w, event.h
                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

                # Pause game until a key is pressed
                paused = True
                while paused:
                    pause_text = FONT.render("Game Paused - Press any key to continue", True, GREEN)
                    WIN.fill((0, 0, 0))
                    WIN.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2,
                                          HEIGHT//2 - pause_text.get_height()//2))
                    pygame.display.update()
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if e.type == pygame.KEYDOWN:
                            paused = False

                # Scale paddles and ball
                scale_rect(paddle1.rect, old_w, old_h, WIDTH, HEIGHT)
                scale_rect(paddle2.rect, old_w, old_h, WIDTH, HEIGHT)
                scale_ball(ball, old_w, old_h, WIDTH, HEIGHT)

                # Regenerate stars
                stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(150)]

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            paddle1.move(up=True)
        if keys[pygame.K_s]:
            paddle1.move(up=False)
        if two_player:
            if keys[pygame.K_UP]:
                paddle2.move(up=True)
            if keys[pygame.K_DOWN]:
                paddle2.move(up=False)
        else:
            if paddle2.rect.centery < ball.rect.centery:
                paddle2.move(up=False)
            elif paddle2.rect.centery > ball.rect.centery:
                paddle2.move(up=True)

        ball.move()
        if ball.rect.colliderect(paddle1.rect):
            ball.speed_x *= -1
        if ball.rect.colliderect(paddle2.rect):
            ball.speed_x *= -1

        if ball.rect.left <= 0:
            score2 += 1
            ball.reset()
        if ball.rect.right >= WIDTH:
            score1 += 1
            ball.reset()

        draw_window(paddle1, paddle2, ball, score1, score2)

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

# ----------------------- Main Menu -----------------------
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
                if event.key == pygame.K_e:
                    difficulty = "E"
                if event.key == pygame.K_c:
                    difficulty = "C"
                if event.key == pygame.K_a:
                    difficulty = "A"
                if event.key == pygame.K_m:
                    two_player = not two_player
                if event.key == pygame.K_UP:
                    if max_points < 20:
                        max_points += 1
                if event.key == pygame.K_DOWN: 
                    if max_points > 1:
                        max_points -= 1

main_menu()
