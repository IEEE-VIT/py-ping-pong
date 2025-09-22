import pygame
import sys
import random
import json
import os
from datetime import datetime

# ---------- Configuration ----------
pygame.init()
BASE_WIDTH, BASE_HEIGHT = 800, 400  # Base resolution
WIDTH, HEIGHT = BASE_WIDTH, BASE_HEIGHT
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Pixel Ping Pong - Space Edition (With Leaderboard)")
FPS = 60

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
STAR_COLOR = (200, 200, 255)
NEON_BLUE = (0, 255, 255)

LEADERBOARD_FILE = "high_scores.json"
MAX_LEADERBOARD_ITEMS = 10

try:
    FONT = pygame.font.Font("PressStart2P.ttf", 30)
    MENU_FONT = pygame.font.Font("PressStart2P.ttf", 20)
except:
    FONT = pygame.font.SysFont("Courier", 30)
    MENU_FONT = pygame.font.SysFont("Courier", 20)

PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10
DIFFICULTY_SPEED = {"E": 5, "C": 8, "A": 5}

stars = [(random.randint(0, BASE_WIDTH), random.randint(0, BASE_HEIGHT)) for _ in range(150)]


# ---------- Scaling Utilities ----------
def get_scale_factors():
    return WIDTH / BASE_WIDTH, HEIGHT / BASE_HEIGHT


def scale_rect(rect):
    """Return a scaled copy of a rect for rendering"""
    scale_x, scale_y = get_scale_factors()
    return pygame.Rect(
        int(rect.x * scale_x),
        int(rect.y * scale_y),
        int(rect.width * scale_x),
        int(rect.height * scale_y),
    )


def scale_pos(x, y):
    scale_x, scale_y = get_scale_factors()
    return int(x * scale_x), int(y * scale_y)


# ---------- Game Objects ----------
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 7

    def draw(self):
        pygame.draw.rect(WIN, NEON_BLUE, scale_rect(self.rect))

    def move(self, up=True):
        if up:
            self.rect.y -= self.speed
        else:
            self.rect.y += self.speed

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > BASE_HEIGHT:
            self.rect.bottom = BASE_HEIGHT


class Ball:
    def __init__(self, difficulty="E"):
        self.rect = pygame.Rect(BASE_WIDTH // 2, BASE_HEIGHT // 2, BALL_SIZE, BALL_SIZE)
        self.difficulty = difficulty
        self.reset()

    def reset(self):
        self.rect.center = (BASE_WIDTH // 2, BASE_HEIGHT // 2)
        self.speed_x = 0
        self.speed_y = 0
        self.base_speed = DIFFICULTY_SPEED[self.difficulty]
        self.ready_to_move = False

    def start_movement(self):
        self.speed_x = random.choice([-1, 1]) * random.randint(4, 6)
        self.speed_y = random.choice([-1, 1]) * random.randint(2, 4)
        self.ready_to_move = True

    def draw(self):
        pygame.draw.rect(WIN, GREEN, scale_rect(self.rect))

    def move(self):
        if not self.ready_to_move:
            return
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.top <= 0 or self.rect.bottom >= BASE_HEIGHT:
            self.speed_y *= -1
        if self.difficulty == "A":
            if abs(self.speed_x) < 15:
                self.speed_x *= 1.001
            if abs(self.speed_y) < 15:
                self.speed_y *= 1.001


# ---------- Leaderboard Utilities ----------
def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_leaderboard(entries):
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(entries, f, indent=2)
    except Exception as e:
        print("Error saving leaderboard:", e)


def add_score_to_leaderboard(name, points, mode):
    entries = load_leaderboard()
    entry = {
        "name": name,
        "points": points,
        "mode": mode,
        "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    entries.append(entry)
    entries = sorted(entries, key=lambda x: x["points"], reverse=True)
    entries = entries[:MAX_LEADERBOARD_ITEMS]
    save_leaderboard(entries)


# ---------- UI Helpers ----------
def draw_window(paddle1, paddle2, ball, score1, score2, show_ready=False):
    WIN.fill((0, 0, 0))
    for star in stars:
        x, y = scale_pos(star[0], star[1])
        pygame.draw.circle(WIN, STAR_COLOR, (x, y), 1)
    for y in range(0, BASE_HEIGHT, 20):
        pygame.draw.rect(WIN, WHITE, scale_rect(pygame.Rect(BASE_WIDTH // 2 - 1, y, 2, 10)))
    paddle1.draw()
    paddle2.draw()
    ball.draw()
    score_text = FONT.render(f"{score1}  |  {score2}", True, WHITE)
    WIN.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 10))
    if show_ready:
        ready_text = FONT.render("GET READY!", True, GREEN)
        WIN.blit(ready_text, (WIDTH // 2 - ready_text.get_width() // 2,
                              HEIGHT // 2 - ready_text.get_height() // 2))
    pygame.display.update()


def render_centered_text(text, font, y):
    surf = font.render(text, True, WHITE)
    WIN.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))


# ---------- Text Input ----------
def text_input(prompt, max_chars=10):
    input_text = ""
    clock = pygame.time.Clock()
    active = True

    while active:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if len(input_text) < max_chars and event.unicode.isprintable():
                        input_text += event.unicode
        WIN.fill((0, 0, 0))
        for star in stars:
            x, y = scale_pos(star[0], star[1])
            pygame.draw.circle(WIN, STAR_COLOR, (x, y), 1)
        render_centered_text(prompt, MENU_FONT, HEIGHT // 2 - 40)
        box = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 5, 300, 40)
        pygame.draw.rect(WIN, WHITE, box, 2)
        txt_surf = MENU_FONT.render(input_text, True, WHITE)
        WIN.blit(txt_surf, (box.x + 8, box.y + 6))
        hint = MENU_FONT.render("Press ENTER to confirm", True, GREEN)
        WIN.blit(hint, (WIDTH // 2 - hint.get_width() // 2, box.y + 50))
        pygame.display.update()
    return input_text.strip() or "---"


# ---------- Leaderboard Screen ----------
def show_leaderboard_screen():
    entries = load_leaderboard()
    run = True
    clock = pygame.time.Clock()

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    run = False

        WIN.fill((0, 0, 0))
        render_centered_text("LEADERBOARD", FONT, 20)
        if entries:
            y = 80
            for i, e in enumerate(entries):
                line = f"{i+1}. {e['name']} - {e['points']} pts ({e['mode']})"
                surf = MENU_FONT.render(line, True, WHITE)
                WIN.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
                y += 28
        else:
            render_centered_text("No high scores yet.", MENU_FONT, HEIGHT // 2 - 10)
        hint = MENU_FONT.render("Press ESC/ENTER to return", True, GREEN)
        WIN.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 50))
        pygame.display.update()


# ---------- Pause Menu ----------
def pause_menu(custom_message="GAME PAUSED"):
    paused = True
    while paused:
        WIN.fill((0, 0, 0))
        render_centered_text(custom_message, FONT, 100)
        render_centered_text("Press R to Resume", MENU_FONT, 180)
        render_centered_text("Press Q to Quit", MENU_FONT, 220)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    paused = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()


# ---------- Main Game Loop ----------
def main_game(difficulty="E", max_points=5, two_player=True):
    global WIDTH, HEIGHT, WIN
    clock = pygame.time.Clock()
    paddle1 = Paddle(20, BASE_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    paddle2 = Paddle(BASE_WIDTH - 30, BASE_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    ball = Ball(difficulty)

    score1, score2 = 0, 0
    run = True
    pause_after_score = False
    pause_start_time = 0
    pause_duration = 2500

    ball.start_movement()

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                pause_menu("RESIZED - GAME PAUSED")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # Press P to pause
                    pause_menu()

        keys = pygame.key.get_pressed()
        if not pause_after_score:
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
                ball.rect.left = paddle1.rect.right
            if ball.rect.colliderect(paddle2.rect):
                ball.speed_x *= -1
                ball.rect.right = paddle2.rect.left

            if ball.rect.left <= 0:
                score2 += 1
                ball.reset()
                pause_after_score = True
                pause_start_time = pygame.time.get_ticks()
            if ball.rect.right >= BASE_WIDTH:
                score1 += 1
                ball.reset()
                pause_after_score = True
                pause_start_time = pygame.time.get_ticks()
        else:
            current_time = pygame.time.get_ticks()
            if current_time - pause_start_time >= pause_duration:
                pause_after_score = False
                ball.start_movement()

        draw_window(paddle1, paddle2, ball, score1, score2, show_ready=pause_after_score)

        if score1 >= max_points:
            winner_text = "PLAYER 1 WINS!"
            winner = 1
            run = False
        elif score2 >= max_points:
            winner_text = "PLAYER 2 WINS!" if two_player else "AI WINS!"
            winner = 2
            run = False

    WIN.fill((0, 0, 0))
    text = FONT.render(winner_text, True, GREEN)
    WIN.blit(text, (WIDTH // 2 - text.get_width() // 2,
                    HEIGHT // 2 - text.get_height() // 2 - 30))
    pygame.display.update()
    pygame.time.delay(1200)

    if (not two_player and winner == 1) or (two_player and winner in (1, 2)):
        player_points = score1 if winner == 1 else score2
        entries = load_leaderboard()
        qualifies = False
        if len(entries) < MAX_LEADERBOARD_ITEMS:
            qualifies = True
        else:
            if any(player_points > e['points'] for e in entries):
                qualifies = True

        if qualifies:
            prompt = "NEW HIGH SCORE! Enter name:"
            name = text_input(prompt, max_chars=10)
            mode = "2P" if two_player else "1P"
            add_score_to_leaderboard(name, player_points, mode)
            WIN.fill((0, 0, 0))
            msg = MENU_FONT.render("Score saved to leaderboard!", True, GREEN)
            WIN.blit(msg, (WIDTH // 2 - msg.get_width() // 2,
                           HEIGHT // 2 - msg.get_height() // 2))
            pygame.display.update()
            pygame.time.delay(1000)

    pygame.time.delay(600)


# ---------- Main Menu ----------
def main_menu():
    global WIDTH, HEIGHT, WIN   # ✅ FIXED: declare global at top
    run = True
    difficulty = "E"
    max_points = 5
    two_player = True

    while run:
        WIN.fill((0, 0, 0))
        title = FONT.render("PIXEL PING PONG", True, GREEN)
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        diff_text = MENU_FONT.render(f"Difficulty: {difficulty} (E/C/A)", True, WHITE)
        WIN.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, 150))

        points_text = MENU_FONT.render(f"Max Points: {max_points} (UP/DOWN)", True, WHITE)
        WIN.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, 200))

        mode_text = MENU_FONT.render(f"Mode: {'2 Player' if two_player else 'Single Player'} (M to toggle)", True, WHITE)
        WIN.blit(mode_text, (WIDTH // 2 - mode_text.get_width() // 2, 250))

        start_text = MENU_FONT.render("Press ENTER to Start", True, GREEN)
        WIN.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, 300))

        leader_text = MENU_FONT.render("Press L to view Leaderboard", True, WHITE)
        WIN.blit(leader_text, (WIDTH // 2 - leader_text.get_width() // 2, 330))

        pause_text = MENU_FONT.render("Press P to Pause in-game", True, GREEN)
        WIN.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, 360))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
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
                if event.key == pygame.K_l:
                    show_leaderboard_screen()


# ---------- Entry Point ----------
if __name__ == "__main__":
    if not os.path.exists(LEADERBOARD_FILE):
        save_leaderboard([])
    main_menu()
