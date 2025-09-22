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
DIFFICULTY_SPEED = {"E": 5, "C": 8, "A": 10}

stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(150)]

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 7

    def draw(self):
        pygame.draw.rect(WIN, NEON_BLUE, self.rect)

    def move(self, up=True):
        if up:
            self.rect.y -= self.speed
        else:
            self.rect.y += self.speed
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT

class Ball:
    def __init__(self, difficulty="E"):
        self.rect = pygame.Rect(WIDTH//2, HEIGHT//2, BALL_SIZE, BALL_SIZE)
        self.difficulty = difficulty
        self.reset(start_moving=False)

    def reset(self, start_moving=True):
        self.rect.center = (WIDTH//2, HEIGHT//2)
        if start_moving:
            self.speed_x = random.choice([-1, 1]) * random.randint(4, 6)
            self.speed_y = random.choice([-1, 1]) * random.randint(2, 4)
        else:
            self.speed_x = 0
            self.speed_y = 0
        self.base_speed = DIFFICULTY_SPEED[self.difficulty]

    def draw(self):
        pygame.draw.rect(WIN, GREEN, self.rect)

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.speed_y *= -1
        # Accelerate for "A" difficulty
        if self.difficulty == "A":
            if abs(self.speed_x) < 15:  # Limit max speed
                self.speed_x *= 1.001
            if abs(self.speed_y) < 15:
                self.speed_y *= 1.001

def draw_window(paddle1, paddle2, ball, score1, score2, message=None):
    WIN.fill((0, 0, 0))  # Black background
    # Draw stars
    for star in stars:
        pygame.draw.circle(WIN, STAR_COLOR, star, 1)
    # Middle dashed line
    for y in range(0, HEIGHT, 20):
        pygame.draw.rect(WIN, WHITE, (WIDTH//2 - 1, y, 2, 10))
    paddle1.draw()
    paddle2.draw()
    ball.draw()
    # Draw scores
    score_text = FONT.render(f"{score1}  |  {score2}", True, WHITE)
    WIN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 10))
    # Optional message (like "Get Ready!")
    if message:
        msg_text = FONT.render(message, True, GREEN)
        WIN.blit(msg_text, (WIDTH//2 - msg_text.get_width()//2, HEIGHT//2 - msg_text.get_height()//2))
    pygame.display.update()

def main_game(difficulty="E", max_points=5, two_player=True):
    clock = pygame.time.Clock()
    paddle1 = Paddle(20, HEIGHT//2 - PADDLE_HEIGHT//2)
    paddle2 = Paddle(WIDTH - 30, HEIGHT//2 - PADDLE_HEIGHT//2)
    ball = Ball(difficulty)

    score1, score2 = 0, 0
    run = True
    waiting = True  # Start with "Get Ready!"
    wait_timer = pygame.time.get_ticks()

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        # Player 1 movement
        if keys[pygame.K_w]:
            paddle1.move(up=True)
        if keys[pygame.K_s]:
            paddle1.move(up=False)
        # Player 2 movement
        if two_player:
            if keys[pygame.K_UP]:
                paddle2.move(up=True)
            if keys[pygame.K_DOWN]:
                paddle2.move(up=False)
        else:
            # Simple AI
            if paddle2.rect.centery < ball.rect.centery:
                paddle2.move(up=False)
            elif paddle2.rect.centery > ball.rect.centery:
                paddle2.move(up=True)

        # Handle waiting period after scoring
        if waiting:
            draw_window(paddle1, paddle2, ball, score1, score2, "GET READY!")
            if pygame.time.get_ticks() - wait_timer > 2000:  # 2 seconds delay
                waiting = False
                ball.reset(start_moving=True)
            continue

        ball.move()

        # Ball collision with paddles
        if ball.rect.colliderect(paddle1.rect):
            ball.speed_x *= -1
        if ball.rect.colliderect(paddle2.rect):
            ball.speed_x *= -1

        # Score update
        if ball.rect.left <= 0:
            score2 += 1
            ball.reset(start_moving=False)
            waiting = True
            wait_timer = pygame.time.get_ticks()
        if ball.rect.right >= WIDTH:
            score1 += 1
            ball.reset(start_moving=False)
            waiting = True
            wait_timer = pygame.time.get_ticks()

        draw_window(paddle1, paddle2, ball, score1, score2)

        # Win check
        if score1 >= max_points:
            winner_text = "PLAYER 1 WINS!"
            run = False
        elif score2 >= max_points:
            winner_text = "PLAYER 2 WINS!" if two_player else "AI WINS!"
            run = False

    # Display winner
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
