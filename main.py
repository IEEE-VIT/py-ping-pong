import pygame
import sys
import random
import json
import os
import math
from array import array
from datetime import datetime

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    AUDIO_AVAILABLE = True
except pygame.error:
    AUDIO_AVAILABLE = False
BASE_WIDTH, BASE_HEIGHT = 800, 400
WIDTH, HEIGHT = BASE_WIDTH, BASE_HEIGHT
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Pixel Ping Pong - Space Edition (With Leaderboard)")
FPS = 60

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
STAR_COLOR = (200, 200, 255)
NEON_BLUE = (0, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

LEADERBOARD_FILE = "high_scores.json"
MAX_LEADERBOARD_ITEMS = 10

# ---------- Controls Configuration ----------
CONTROLS_FILE = "controls.json"

controls = {
    "P1_UP": pygame.K_w,
    "P1_DOWN": pygame.K_s,
    "P2_UP": pygame.K_UP,
    "P2_DOWN": pygame.K_DOWN,
}

KEY_NAMES = {
    pygame.K_w: "W",
    pygame.K_s: "S",
    pygame.K_UP: "UP",
    pygame.K_DOWN: "DOWN",
    pygame.K_a: "A",
    pygame.K_d: "D",
    pygame.K_q: "Q",
    pygame.K_e: "E",
    pygame.K_i: "I",
    pygame.K_k: "K",
    pygame.K_j: "J",
    pygame.K_l: "L",
    pygame.K_SPACE: "SPACE",
}

def get_key_name(key_code):
    if key_code in KEY_NAMES:
        return KEY_NAMES[key_code]
    name = pygame.key.name(key_code).upper()
    return name if len(name) <= 6 else name[:6]

def load_controls():
    global controls
    if os.path.exists(CONTROLS_FILE):
        try:
            with open(CONTROLS_FILE, "r") as f:
                saved = json.load(f)
                controls.update(saved)
        except Exception:
            pass

def save_controls():
    try:
        with open(CONTROLS_FILE, "w") as f:
            json.dump(controls, f, indent=2)
    except Exception as e:
        print("Error saving controls:", e)

try:
    FONT = pygame.font.Font("PressStart2P.ttf", 30)
    MENU_FONT = pygame.font.Font("PressStart2P.ttf", 20)
    POWERUP_FONT = pygame.font.Font("PressStart2P.ttf", 10)
except:
    FONT = pygame.font.SysFont("Courier", 30)
    MENU_FONT = pygame.font.SysFont("Courier", 20)
    POWERUP_FONT = pygame.font.SysFont("Courier", 10)

PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10
DIFFICULTY_SPEED = {"E": 5, "C": 8, "A": 5}

stars = [(random.randint(0, BASE_WIDTH), random.randint(0, BASE_HEIGHT)) for _ in range(150)]

# ---------- Synthesized Sound Effects ----------
def make_sound(notes, volume=0.35):
    if not AUDIO_AVAILABLE:
        return None

    sample_rate, sample_format, channels = pygame.mixer.get_init()
    if sample_format != -16:
        return None

    samples = array("h")
    for frequency, duration in notes:
        count = int(sample_rate * duration)
        for index in range(count):
            fade = min(1, index / max(1, sample_rate * 0.008),
                       (count - index - 1) / max(1, sample_rate * 0.012))
            value = int(32767 * volume * fade * (1 if math.sin(2 * math.pi * frequency * index / sample_rate) >= 0 else -1))
            samples.extend([value] * channels)
    return pygame.mixer.Sound(buffer=samples.tobytes())

SOUNDS = {
    "paddle": make_sound([(740, 0.055)], 0.28),
    "wall": make_sound([(420, 0.045)], 0.20),
    "score": make_sound([(330, 0.08), (220, 0.12)], 0.30),
    "win": make_sound([(523, 0.09), (659, 0.09), (784, 0.18)], 0.36),
    "high_score": make_sound([(659, 0.08), (784, 0.08), (988, 0.08), (1319, 0.22)], 0.40),
    "menu": make_sound([(600, 0.035)], 0.18),
    "bind": make_sound([(880, 0.06), (1174, 0.08)], 0.25),
}

def play_sound(name):
    sound = SOUNDS.get(name)
    if sound is not None:
        sound.play()

# ---------- Scaling Utilities ----------
def get_scale_factors():
    return WIDTH / BASE_WIDTH, HEIGHT / BASE_HEIGHT

def scale_rect(rect):
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
        self.base_x = x
        self.base_y = y
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.base_speed = 7
        self.speed = 7

    def reset_size(self):
        center_y = self.rect.centery
        self.rect.height = PADDLE_HEIGHT
        self.rect.centery = center_y

    def set_height(self, height):
        center_y = self.rect.centery
        self.rect.height = height
        self.rect.centery = center_y
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > BASE_HEIGHT:
            self.rect.bottom = BASE_HEIGHT

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
        self.last_hitter = None
        self.speed_multiplier = 1.0
        self.reset()

    def reset(self):
        self.rect.center = (BASE_WIDTH // 2, BASE_HEIGHT // 2)
        self.speed_x = 0
        self.speed_y = 0
        self.base_speed = DIFFICULTY_SPEED[self.difficulty]
        self.ready_to_move = False
        self.last_hitter = None
        self.speed_multiplier = 1.0

    def start_movement(self):
        self.speed_x = random.choice([-1, 1]) * random.randint(4, 6)
        self.speed_y = random.choice([-1, 1]) * random.randint(2, 4)
        self.ready_to_move = True

    def draw(self):
        pygame.draw.rect(WIN, GREEN, scale_rect(self.rect))

    def move(self):
        if not self.ready_to_move:
            return False
        self.rect.x += int(self.speed_x * self.speed_multiplier)
        self.rect.y += int(self.speed_y * self.speed_multiplier)
        if self.rect.top <= 0 or self.rect.bottom >= BASE_HEIGHT:
            self.speed_y *= -1
            wall_bounce = True
        else:
            wall_bounce = False
        if self.difficulty == "A":
            if abs(self.speed_x) < 15:
                self.speed_x *= 1.001
            if abs(self.speed_y) < 15:
                self.speed_y *= 1.001
        return wall_bounce

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

    if active_effects:
        if active_effects[1].get("shield"):
            p1_shield = pygame.Rect(paddle1.rect.right + 2, 0, 4, BASE_HEIGHT)
            pygame.draw.rect(WIN, PURPLE, scale_rect(p1_shield))
        if active_effects[2].get("shield"):
            p2_shield = pygame.Rect(paddle2.rect.left - 6, 0, 4, BASE_HEIGHT)
            pygame.draw.rect(WIN, PURPLE, scale_rect(p2_shield))

    paddle1.draw()
    paddle2.draw()
    ball.draw()

    if powerup:
        powerup.draw()

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
                    play_sound("menu")
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
                    play_sound("menu")
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
                    play_sound("menu")
                    paused = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

# ---------- Controls Settings Menu ----------
def controls_menu():
    global WIDTH, HEIGHT, WIN
    clock = pygame.time.Clock()
    selected_idx = 0
    actions = ["P1_UP", "P1_DOWN", "P2_UP", "P2_DOWN"]
    labels = ["P1 Move Up", "P1 Move Down", "P2 Move Up", "P2 Move Down"]
    remapping = False
    error_msg = ""
    error_time = 0

    while True:
        clock.tick(FPS)
        WIN.fill((0, 0, 0))

        for star in stars:
            x, y = scale_pos(star[0], star[1])
            pygame.draw.circle(WIN, STAR_COLOR, (x, y), 1)

        render_centered_text("CONTROLS SETTINGS", FONT, 30)

        start_y = 110
        for i, act in enumerate(actions):
            key_code = controls[act]
            key_str = get_key_name(key_code)

            if remapping and i == selected_idx:
                display_str = f"{labels[i]}: [PRESS ANY KEY]"
            elif i == selected_idx:
                display_str = f"> {labels[i]}: {key_str} <"
            else:
                display_str = f"{labels[i]}: {key_str}"

            render_centered_text(display_str, MENU_FONT, start_y + i * 40)

        now = pygame.time.get_ticks()
        if error_msg and now - error_time < 2000:
            err_surf = MENU_FONT.render(error_msg, True, (255, 80, 80))
            WIN.blit(err_surf, (WIDTH // 2 - err_surf.get_width() // 2, start_y + 180))
        else:
            if remapping:
                hint_str = "Press key to assign (ESC to cancel)"
            else:
                hint_str = "UP/DOWN select | ENTER change | ESC exit"
            render_centered_text(hint_str, MENU_FONT, start_y + 180)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if remapping:
                    if event.key == pygame.K_ESCAPE:
                        remapping = False
                        play_sound("menu")
                        continue

                    # Reserved system keys check
                    if event.key in (pygame.K_p, pygame.K_q, pygame.K_r):
                        error_msg = f"Key '{get_key_name(event.key)}' reserved!"
                        error_time = pygame.time.get_ticks()
                        play_sound("wall")
                        remapping = False
                        continue

                    # Conflict check (prevent assigning same key twice)
                    conflict_action = None
                    for act_key, code in controls.items():
                        if code == event.key and act_key != actions[selected_idx]:
                            conflict_action = act_key
                            break

                    if conflict_action:
                        error_msg = f"Conflict with {conflict_action.replace('_', ' ')}!"
                        error_time = pygame.time.get_ticks()
                        play_sound("wall")
                    else:
                        controls[actions[selected_idx]] = event.key
                        save_controls()
                        play_sound("bind")
                    remapping = False

                else:
                    if event.key == pygame.K_UP:
                        selected_idx = (selected_idx - 1) % len(actions)
                        play_sound("menu")
                    elif event.key == pygame.K_DOWN:
                        selected_idx = (selected_idx + 1) % len(actions)
                        play_sound("menu")
                    elif event.key == pygame.K_RETURN:
                        remapping = True
                        play_sound("menu")
                    elif event.key == pygame.K_ESCAPE:
                        play_sound("menu")
                        return
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

    current_powerup = None
    next_powerup_time = pygame.time.get_ticks() + random.randint(5000, 10000)
    active_effects = {1: {}, 2: {}}

    ball.start_movement()

    while run:
        clock.tick(FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                pause_menu("RESIZED - GAME PAUSED")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    pause_menu()
# --- AFTER ---
        keys = pygame.key.get_pressed()
        if not pause_after_score:
            if keys[controls["P1_UP"]]:
                paddle1.move(up=True)
            if keys[controls["P1_DOWN"]]:
                paddle1.move(up=False)
            if two_player:
                if keys[controls["P2_UP"]]:
                    paddle2.move(up=True)
                if keys[controls["P2_DOWN"]]:
                    paddle2.move(up=False)
            else:
                if paddle2.rect.centery < ball.rect.centery:
                    paddle2.move(up=False)
                elif paddle2.rect.centery > ball.rect.centery:
                    paddle2.move(up=True)

            if ball.move():
                play_sound("wall")

            if ball.rect.colliderect(paddle1.rect):
                ball.speed_x *= -1
                ball.rect.left = paddle1.rect.right
                ball.last_hitter = 1
                play_sound("paddle")
            if ball.rect.colliderect(paddle2.rect):
                ball.speed_x *= -1
                ball.rect.right = paddle2.rect.left
                ball.last_hitter = 2
                play_sound("paddle")

            if current_powerup:
                collector = None
                if ball.rect.colliderect(current_powerup.rect):
                    collector = ball.last_hitter or random.choice([1, 2])
                elif paddle1.rect.colliderect(current_powerup.rect):
                    collector = 1
                elif paddle2.rect.colliderect(current_powerup.rect):
                    collector = 2

                if collector:
                    apply_powerup(current_powerup.type, collector, paddle1, paddle2, ball, active_effects, current_time)
                    current_powerup = None
                    next_powerup_time = current_time + random.randint(7000, 12000)

            if ball.rect.left <= 0:
                if active_effects[1].get("shield", 0) > current_time:
                    ball.speed_x *= -1
                    ball.rect.left = 1
                    play_sound("wall")
                else:
                    score2 += 1
                    ball.reset()
                    current_powerup = None
                    active_effects = {1: {}, 2: {}}
                    play_sound("score")
                    pause_after_score = True
                    pause_start_time = pygame.time.get_ticks()
            if ball.rect.right >= BASE_WIDTH:
                if active_effects[2].get("shield", 0) > current_time:
                    ball.speed_x *= -1
                    ball.rect.right = BASE_WIDTH - 1
                    play_sound("wall")
                else:
                    score1 += 1
                    ball.reset()
                    current_powerup = None
                    active_effects = {1: {}, 2: {}}
                    play_sound("score")
                    pause_after_score = True
                    pause_start_time = pygame.time.get_ticks()
        else:
            current_time = pygame.time.get_ticks()
            if current_time - pause_start_time >= pause_duration:
                pause_after_score = False
                ball.start_movement()
                next_powerup_time = current_time + random.randint(3000, 7000)

        draw_window(paddle1, paddle2, ball, score1, score2, powerup=current_powerup, active_effects=active_effects, show_ready=pause_after_score)

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
    play_sound("win")
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
            play_sound("high_score")
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
    global WIDTH, HEIGHT, WIN
    run = True
    difficulty = "E"
    max_points = 5
    two_player = True

    while run:
        WIN.fill((0, 0, 0))
        title = FONT.render("PIXEL PING PONG", True, GREEN)
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        diff_text = MENU_FONT.render(f"Difficulty: {difficulty} (E/C/A/R)", True, WHITE)
        WIN.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, 150))

        points_text = MENU_FONT.render(f"Max Points: {max_points} (UP/DOWN)", True, WHITE)
        WIN.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, 200))

        mode_text = MENU_FONT.render(f"Mode: {'2 Player' if two_player else 'Single Player'} (M to toggle)", True, WHITE)
        WIN.blit(mode_text, (WIDTH // 2 - mode_text.get_width() // 2, 250))

        start_text = MENU_FONT.render("Press ENTER to Start", True, GREEN)
        WIN.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, 300))

leader_text = MENU_FONT.render("Press L for Leaderboard", True, WHITE)
        WIN.blit(leader_text, (WIDTH // 2 - leader_text.get_width() // 2, 330))

        controls_text = MENU_FONT.render("Press C for Controls Settings", True, WHITE)
        WIN.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, 355))

        pause_text = MENU_FONT.render("Press P to Pause in-game", True, GREEN)
        WIN.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, 380))    
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
                    play_sound("menu")
                    selected_difficulty = difficulty
                    if difficulty == "R":
                        selected_difficulty = random.choice(["E", "C", "A"])
                    main_game(selected_difficulty, max_points, two_player)
                if event.key == pygame.K_e:
                    play_sound("menu")
                    difficulty = "E"
                if event.key == pygame.K_c:
                    play_sound("menu")
                    difficulty = "C"
                if event.key == pygame.K_a:
                    play_sound("menu")
                    difficulty = "A"
                if event.key == pygame.K_r:
                    play_sound("menu")
                    difficulty = "R"
                if event.key == pygame.K_m:
                    play_sound("menu")
                    two_player = not two_player
                if event.key == pygame.K_UP:
                    if max_points < 20:
                        max_points += 1
                        play_sound("menu")
                if event.key == pygame.K_DOWN:
                    if max_points > 1:
                        max_points -= 1
                        play_sound("menu")
                if event.key == pygame.K_l:
                    play_sound("menu")
                    show_leaderboard_screen()
                if event.key == pygame.K_c:
                    play_sound("menu")
                    controls_menu()

if __name__ == "__main__":
    load_controls()  # Loads custom saved keys from controls.json on startup
    if not os.path.exists(LEADERBOARD_FILE):
        save_leaderboard([])
    main_menu()


