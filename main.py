import pygame
import sys
import random
import json
import os
import math
from array import array
from collections import deque
from datetime import datetime

# ---------- Configuration ----------
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    AUDIO_AVAILABLE = True
except pygame.error:
    # Audio is optional so the game still runs on systems without a sound device.
    AUDIO_AVAILABLE = False
BASE_WIDTH, BASE_HEIGHT = 800, 400  # Base resolution
WIDTH, HEIGHT = BASE_WIDTH, BASE_HEIGHT
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Pixel Ping Pong - Space Edition (With Leaderboard)")
FPS = 60

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 80, 80)
STAR_COLOR = (200, 200, 255)
NEON_BLUE = (0, 255, 255)

LEADERBOARD_FILE = "high_scores.json"
MAX_LEADERBOARD_ITEMS = 10

# Default Keybindings
DEFAULT_KEYS = {
    "P1_UP": pygame.K_w,
    "P1_DOWN": pygame.K_s,
    "P2_UP": pygame.K_UP,
    "P2_DOWN": pygame.K_DOWN,
}

# Session Keybindings State
controls = DEFAULT_KEYS.copy()

try:
    FONT = pygame.font.Font("PressStart2P.ttf", 30)
    MENU_FONT = pygame.font.Font("PressStart2P.ttf", 20)
except:
    FONT = pygame.font.SysFont("Courier", 30)
    MENU_FONT = pygame.font.SysFont("Courier", 20)

PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10
DIFFICULTY_SPEED = {"E": 5, "C": 8, "A": 5}

POWER_UP_TYPES = {
    "speed": {"label": "SPEED", "color": (255, 230, 0)},
    "grow": {"label": "GROW", "color": (0, 255, 130)},
    "shrink": {"label": "SHRINK", "color": (255, 90, 180)},
    "ball_slow": {"label": "SLOW", "color": (110, 180, 255)},
    "ball_fast": {"label": "FAST", "color": (255, 105, 50)},
    "shield": {"label": "SHIELD", "color": (150, 100, 255)},
}
POWER_UP_SIZE = 22
POWER_UP_LIFETIME = 7000
POWER_UP_EFFECT_TIME = 7000

stars = [(random.randint(0, BASE_WIDTH), random.randint(0, BASE_HEIGHT)) for _ in range(150)]


# ---------- Synthesized Sound Effects ----------
def make_sound(notes, volume=0.35):
    """Create a small square-wave sound without requiring external assets."""
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
    "powerup": make_sound([(440, 0.05), (660, 0.08)], 0.28),
}


def play_sound(name):
    sound = SOUNDS.get(name)
    if sound is not None:
        sound.play()


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
        self.base_speed = 7
        self.speed = self.base_speed

    def set_height(self, height):
        center_y = self.rect.centery
        self.rect.height = height
        self.rect.centery = center_y
        self.rect.clamp_ip(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT))

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
        self.trail = deque(maxlen=8)
        self.reset()

    def reset(self):
        self.rect.center = (BASE_WIDTH // 2, BASE_HEIGHT // 2)
        self.trail.clear()
        self.speed_x = 0
        self.speed_y = 0
        self.base_speed = DIFFICULTY_SPEED[self.difficulty]
        self.ready_to_move = False
        self.trail = []
        self.trail_length = 10
        self.last_hitter = None
        self.speed_multiplier = 1.0
        self.last_touch = 1

    def start_movement(self):
        self.speed_x = random.choice([-1, 1]) * random.randint(4, 6)
        self.speed_y = random.choice([-1, 1]) * random.randint(2, 4)
        self.ready_to_move = True

    def draw(self):
        if self.trail:
            trail_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            scale_x, scale_y = get_scale_factors()
            base_radius = max(2, int(BALL_SIZE * min(scale_x, scale_y) / 2))
            trail_length = len(self.trail)
            for index, position in enumerate(self.trail):
                progress = (index + 1) / trail_length
                radius = max(1, int(base_radius * progress))
                alpha = int(25 + 150 * progress)
                pygame.draw.circle(trail_layer, (*GREEN, alpha),
                                   scale_pos(*position), radius)
            WIN.blit(trail_layer, (0, 0))
        pygame.draw.rect(WIN, GREEN, scale_rect(self.rect))

    def move(self):
        if not self.ready_to_move:
            return
        self.trail.append(self.rect.copy())
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
            return False
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        self.trail.append(self.rect.center)
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


class PowerUp:
    def __init__(self, kind, created_at):
        self.kind = kind
        self.rect = pygame.Rect(
            random.randint(BASE_WIDTH // 4, BASE_WIDTH * 3 // 4),
            random.randint(40, BASE_HEIGHT - 40),
            POWER_UP_SIZE,
            POWER_UP_SIZE,
        )
        self.created_at = created_at


class Asteroid:
    def __init__(self, x):
        self.x = x
        self.y = random.randint(45, BASE_HEIGHT - 45)
        self.radius = random.randint(14, 20)
        self.speed_y = random.choice((-1, 1)) * random.uniform(0.35, 0.8)

    def move(self):
        self.y += self.speed_y
        if self.y - self.radius > BASE_HEIGHT:
            self.y = -self.radius
        elif self.y + self.radius < 0:
            self.y = BASE_HEIGHT + self.radius

    def draw(self):
        center = scale_pos(self.x, self.y)
        scale_x, scale_y = get_scale_factors()
        radius = max(2, int(self.radius * min(scale_x, scale_y)))
        pygame.draw.circle(WIN, (115, 120, 135), center, radius)
        pygame.draw.circle(WIN, (175, 180, 195), center, radius, 1)
        pygame.draw.circle(WIN, (75, 80, 95),
                           (center[0] - radius // 3, center[1] - radius // 4),
                           max(1, radius // 4))
        pygame.draw.circle(WIN, (85, 90, 105),
                           (center[0] + radius // 3, center[1] + radius // 4),
                           max(1, radius // 6))


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
    entries = load_leaderboard() #comment
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
def draw_power_up(power_up):
    if power_up is None:
        return
    color = POWER_UP_TYPES[power_up.kind]["color"]
    rect = scale_rect(power_up.rect)
    center = rect.center
    points = [(center[0], rect.top), (rect.right, center[1]),
              (center[0], rect.bottom), (rect.left, center[1])]
    pygame.draw.polygon(WIN, color, points)
    pygame.draw.polygon(WIN, WHITE, points, 1)
    label = MENU_FONT.render(POWER_UP_TYPES[power_up.kind]["label"], True, color)
    WIN.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT - 28))


def draw_effect_indicators(effects, current_time):
    for player, x in ((1, 20), (2, WIDTH - 145)):
        active = [name.upper() for name, end in effects[player].items()
                  if end > current_time and name != "size"]
        if effects[player]["size"] > current_time:
            active.append("SIZE")
        if active:
            indicator = MENU_FONT.render(" ".join(active), True, POWER_UP_TYPES["shield"]["color"])
            WIN.blit(indicator, (x, 45))


def draw_window(paddle1, paddle2, ball, score1, score2, power_up=None,
                asteroids=None, effects=None, current_time=0, show_ready=False):
    WIN.fill((0, 0, 0))
    for star in stars:
        x, y = scale_pos(star[0], star[1])
        pygame.draw.circle(WIN, STAR_COLOR, (x, y), 1)
    for y in range(0, BASE_HEIGHT, 20):
        pygame.draw.rect(WIN, WHITE, scale_rect(pygame.Rect(BASE_WIDTH // 2 - 1, y, 2, 10)))
    paddle1.draw()
    paddle2.draw()
    for asteroid in asteroids or []:
        asteroid.draw()
    ball.draw()
    draw_power_up(power_up)
    score_text = FONT.render(f"{score1}  |  {score2}", True, WHITE)
    WIN.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 10))
    if show_ready:
        ready_text = FONT.render("GET READY!", True, GREEN)
        WIN.blit(ready_text, (WIDTH // 2 - ready_text.get_width() // 2,
                              HEIGHT // 2 - ready_text.get_height() // 2))
    if effects is not None:
        draw_effect_indicators(effects, current_time)
    pygame.display.update()


def render_centered_text(text, font, y, color=WHITE):
    surf = font.render(text, True, color)
    WIN.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))


# ---------- Controls Customization Menu ----------
def controls_menu():
    global WIDTH, HEIGHT, WIN
    clock = pygame.time.Clock()
    selected_index = 0
    actions = [("P1 Up", "P1_UP"), ("P1 Down", "P1_DOWN"), ("P2 Up", "P2_UP"), ("P2 Down", "P2_DOWN")]
    listening = False
    message = "Use UP/DOWN to navigate, ENTER to change"
    message_color = WHITE

    while True:
        clock.tick(FPS)
        WIN.fill((0, 0, 0))
        render_centered_text("CUSTOMIZE CONTROLS", FONT, 30)

        y = 110
        for i, (label, key_name) in enumerate(actions):
            key_str = pygame.key.name(controls[key_name]).upper()
            if listening and i == selected_index:
                text = f"{label}: [ PRESS ANY KEY ]"
                color = GREEN
            else:
                text = f"{label}: {key_str}"
                color = GREEN if i == selected_index else WHITE
            render_centered_text(text, MENU_FONT, y, color)
            y += 40

        render_centered_text("Press R to Reset Defaults", MENU_FONT, y + 20, WHITE)
        render_centered_text("Press ESC to Return", MENU_FONT, y + 50, WHITE)
        render_centered_text(message, MENU_FONT, HEIGHT - 40, message_color)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

            if listening:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_p):
                        message = "System keys (ESC/ENTER/P) cannot be assigned!"
                        message_color = RED
                        listening = False
                        play_sound("wall")
                    else:
                        target_action = actions[selected_index][1]
                        conflict = any(k_val == event.key for k_act, k_val in controls.items() if k_act != target_action)
                        if conflict:
                            message = "Key conflict! Already assigned to another control."
                            message_color = RED
                            play_sound("wall")
                        else:
                            controls[target_action] = event.key
                            message = f"Rebound {actions[selected_index][0]}!"
                            message_color = GREEN
                            play_sound("menu")
                        listening = False
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        play_sound("menu")
                        return
                    elif event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(actions)
                        play_sound("menu")
                    elif event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(actions)
                        play_sound("menu")
                    elif event.key == pygame.K_RETURN:
                        listening = True
                        message = "Press the new key for this action..."
                        message_color = GREEN
                        play_sound("menu")
                    elif event.key == pygame.K_r:
                        controls.update(DEFAULT_KEYS)
                        message = "Controls reset to default!"
                        message_color = GREEN
                        play_sound("menu")


# ---------- Power-up Effects ----------
def update_power_up_effects(paddle1, paddle2, effects, current_time):
    for player, paddle in ((1, paddle1), (2, paddle2)):
        player_effects = effects[player]
        paddle.speed = 11 if player_effects["speed"] > current_time else paddle.base_speed
        size = player_effects["size"]
        if size > current_time:
            paddle.set_height(player_effects["size_value"])
        elif paddle.rect.height != PADDLE_HEIGHT:
            paddle.set_height(PADDLE_HEIGHT)


def apply_power_up(power_up, player, ball, effects, current_time, ball_effect):
    kind = power_up.kind
    player_effects = effects[player]
    if kind == "speed":
        player_effects["speed"] = current_time + POWER_UP_EFFECT_TIME
    elif kind in ("grow", "shrink"):
        player_effects["size"] = current_time + POWER_UP_EFFECT_TIME
        player_effects["size_value"] = 95 if kind == "grow" else 35
    elif kind == "shield":
        player_effects["shield"] = current_time + POWER_UP_EFFECT_TIME
    else:
        if ball_effect["until"] > current_time:
            ball.speed_x /= ball_effect["factor"]
            ball.speed_y /= ball_effect["factor"]
        factor = 0.70 if kind == "ball_slow" else 1.35
        ball.speed_x *= factor
        ball.speed_y *= factor
        ball_effect = {"factor": factor, "until": current_time + POWER_UP_EFFECT_TIME}
    play_sound("powerup")
    return ball_effect


def bounce_ball_off_asteroid(ball, asteroid):
    ball_x, ball_y = ball.rect.center
    delta_x = ball_x - asteroid.x
    delta_y = ball_y - asteroid.y
    ball_radius = BALL_SIZE / 2
    if delta_x * delta_x + delta_y * delta_y > (asteroid.radius + ball_radius) ** 2:
        return False

    if abs(delta_x) >= abs(delta_y):
        direction = 1 if delta_x >= 0 else -1
        ball.speed_x = abs(ball.speed_x) * direction
        ball.rect.centerx = int(asteroid.x + direction * (asteroid.radius + ball_radius))
    else:
        direction = 1 if delta_y >= 0 else -1
        ball.speed_y = abs(ball.speed_y) * direction
        ball.rect.centery = int(asteroid.y + direction * (asteroid.radius + ball_radius))
    return True


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


# ---------- Main Game Loop ----------
def main_game(difficulty="E", max_points=5, two_player=True):
    global WIDTH, HEIGHT, WIN
    clock = pygame.time.Clock()
    paddle1 = Paddle(20, BASE_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    paddle2 = Paddle(BASE_WIDTH - 30, BASE_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    ball = Ball(difficulty)
    asteroid_count = random.randint(1, 2)
    asteroid_x_positions = (BASE_WIDTH // 2 - 55, BASE_WIDTH // 2 + 55)
    asteroids = [Asteroid(asteroid_x_positions[index]) for index in range(asteroid_count)]

    score1, score2 = 0, 0
    run = True
    pause_after_score = False
    pause_start_time = 0
    pause_duration = 2500
    power_up = None
    next_power_up = pygame.time.get_ticks() + random.randint(4000, 7000)
    effects = {
        1: {"speed": 0, "size": 0, "size_value": PADDLE_HEIGHT, "shield": 0},
        2: {"speed": 0, "size": 0, "size_value": PADDLE_HEIGHT, "shield": 0},
    }
    ball_effect = {"factor": 1, "until": 0}

    ball.start_movement()

    while run:
        clock.tick(FPS)
        current_time = pygame.time.get_ticks()
        for asteroid in asteroids:
            asteroid.move()
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
        update_power_up_effects(paddle1, paddle2, effects, current_time)

        if ball_effect["until"] and ball_effect["until"] <= current_time:
            ball.speed_x /= ball_effect["factor"]
            ball.speed_y /= ball_effect["factor"]
            ball_effect = {"factor": 1, "until": 0}

        if power_up is None and current_time >= next_power_up:
            power_up = PowerUp(random.choice(list(POWER_UP_TYPES)), current_time)
        elif power_up is not None and current_time - power_up.created_at >= POWER_UP_LIFETIME:
            power_up = None
            next_power_up = current_time + random.randint(4000, 7000)

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

            for asteroid in asteroids:
                if bounce_ball_off_asteroid(ball, asteroid):
                    play_sound("wall")

            if ball.rect.colliderect(paddle1.rect):
                ball.speed_x *= -1
                ball.rect.left = paddle1.rect.right
                ball.last_touch = 1
                play_sound("paddle")
            if ball.rect.colliderect(paddle2.rect):
                ball.speed_x *= -1
                ball.rect.right = paddle2.rect.left
                ball.last_touch = 2
                play_sound("paddle")

            if power_up is not None:
                collector = None
                if paddle1.rect.colliderect(power_up.rect):
                    collector = 1
                elif paddle2.rect.colliderect(power_up.rect):
                    collector = 2
                elif ball.rect.colliderect(power_up.rect):
                    collector = ball.last_touch
                if collector is not None:
                    ball_effect = apply_power_up(power_up, collector, ball, effects,
                                                  current_time, ball_effect)
                    power_up = None
                    next_power_up = current_time + random.randint(4000, 7000)

            if ball.rect.left <= 0:
                if effects[1]["shield"] > current_time:
                    play_sound("wall")
                else:
                    score2 += 1
                    play_sound("score")
                ball.reset()
                pause_after_score = True
                pause_start_time = pygame.time.get_ticks()
            if ball.rect.right >= BASE_WIDTH:
                if effects[2]["shield"] > current_time:
                    play_sound("wall")
                else:
                    score1 += 1
                    play_sound("score")
                ball.reset()
                pause_after_score = True
                pause_start_time = pygame.time.get_ticks()
        else:
            if current_time - pause_start_time >= pause_duration:
                pause_after_score = False
                ball.start_movement()
                if ball_effect["until"] > current_time:
                    ball.speed_x *= ball_effect["factor"]
                    ball.speed_y *= ball_effect["factor"]

        draw_window(paddle1, paddle2, ball, score1, score2, power_up, asteroids, effects,
                    current_time, show_ready=pause_after_score)

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
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        diff_text = MENU_FONT.render(f"Difficulty: {difficulty} (E/C/A/R)", True, WHITE)
        WIN.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, 110))

        points_text = MENU_FONT.render(f"Max Points: {max_points} (UP/DOWN)", True, WHITE)
        WIN.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, 150))

        mode_text = MENU_FONT.render(f"Mode: {'2 Player' if two_player else 'Single Player'} (M to toggle)", True, WHITE)
        WIN.blit(mode_text, (WIDTH // 2 - mode_text.get_width() // 2, 190))

        controls_text = MENU_FONT.render("Press C to Customize Controls", True, GREEN)
        WIN.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, 230))

        start_text = MENU_FONT.render("Press ENTER to Start", True, GREEN)
        WIN.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, 270))

        leader_text = MENU_FONT.render("Press L to view Leaderboard", True, WHITE)
        WIN.blit(leader_text, (WIDTH // 2 - leader_text.get_width() // 2, 310))

        pause_text = MENU_FONT.render("Press P to Pause in-game", True, GREEN)
        WIN.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, 350))

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
                elif event.key == pygame.K_e:
                    play_sound("menu")
                    difficulty = "E"
                elif event.key == pygame.K_c:
                    play_sound("menu")
                    controls_menu()
                elif event.key == pygame.K_a:
                    play_sound("menu")
                    difficulty = "A"
                elif event.key == pygame.K_r:
                    play_sound("menu")
                    difficulty = "R"
                elif event.key == pygame.K_m:
                    play_sound("menu")
                    two_player = not two_player
                elif event.key == pygame.K_UP:
                    if max_points < 20:
                        max_points += 1
                        play_sound("menu")
                elif event.key == pygame.K_DOWN:
                    if max_points > 1:
                        max_points -= 1
                        play_sound("menu")
                elif event.key == pygame.K_l:
                    play_sound("menu")
                    show_leaderboard_screen()


# ---------- Entry Point ----------
if __name__ == "__main__":
    if not os.path.exists(LEADERBOARD_FILE):
        save_leaderboard([])
    main_menu()