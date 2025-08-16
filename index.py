import pygame
import random
import sys

# -----------------------------
# Simple Car Dodger (Pygame)
# Controls: ← → to move, P to pause, R to restart after crash, ESC to quit
# No external assets required – everything is drawn with shapes.
# -----------------------------

WIDTH, HEIGHT = 480, 700
FPS = 60
LANE_COUNT = 3
ROAD_MARGIN = 60
LANE_WIDTH = (WIDTH - ROAD_MARGIN * 2) // LANE_COUNT

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Dodger • Pygame")
clock = pygame.time.Clock()

# Fonts
FONT = pygame.font.SysFont("arial", 24)
BIG = pygame.font.SysFont("arial", 44, bold=True)

# Colors
BG = (20, 20, 20)
ROAD = (40, 40, 40)
LINE = (220, 220, 220)
PLAYER = (80, 200, 255)
ENEMY = (250, 100, 100)
SHADOW = (0, 0, 0)

# Utility

def lane_x(lane_index: int) -> int:
    """Return the x coordinate (left) for a given lane index."""
    return ROAD_MARGIN + lane_index * LANE_WIDTH + LANE_WIDTH // 8

# Entities

class Player:
    def __init__(self):
        self.width = LANE_WIDTH // 2
        self.height = 80
        self.lane = LANE_COUNT // 2
        self.x = lane_x(self.lane) + (LANE_WIDTH // 2 - self.width // 2)
        self.y = HEIGHT - self.height - 40
        self.speed = 8
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.move_dir = 0  # -1 left, +1 right

    def update(self):
        # Smooth movement inside road bounds
        self.rect.x += self.move_dir * self.speed
        left_bound = ROAD_MARGIN + 10
        right_bound = WIDTH - ROAD_MARGIN - 10 - self.rect.width
        self.rect.x = max(left_bound, min(right_bound, self.rect.x))

    def draw(self, surf):
        # Simple car shape with windshield
        pygame.draw.rect(surf, SHADOW, self.rect.move(0, 4), border_radius=10)
        pygame.draw.rect(surf, PLAYER, self.rect, border_radius=10)
        windshield = pygame.Rect(self.rect.x + 8, self.rect.y + 10, self.rect.width - 16, 18)
        pygame.draw.rect(surf, (200, 240, 255), windshield, border_radius=6)
        # Wheels
        w = 10
        pygame.draw.rect(surf, (30, 30, 30), (self.rect.left - 6, self.rect.top + 12, w, 18), border_radius=4)
        pygame.draw.rect(surf, (30, 30, 30), (self.rect.right - 4, self.rect.top + 12, w, 18), border_radius=4)
        pygame.draw.rect(surf, (30, 30, 30), (self.rect.left - 6, self.rect.bottom - 30, w, 18), border_radius=4)
        pygame.draw.rect(surf, (30, 30, 30), (self.rect.right - 4, self.rect.bottom - 30, w, 18), border_radius=4)

class Enemy:
    def __init__(self, lane: int, speed: float):
        self.width = LANE_WIDTH // 2
        self.height = 80
        self.rect = pygame.Rect(0, -self.height, self.width, self.height)
        self.rect.x = lane_x(lane) + (LANE_WIDTH // 2 - self.width // 2)
        self.rect.y = -self.height
        self.speed = speed

    def update(self):
        self.rect.y += self.speed

    def offscreen(self) -> bool:
        return self.rect.top > HEIGHT + 10

    def draw(self, surf):
        pygame.draw.rect(surf, SHADOW, self.rect.move(0, 4), border_radius=10)
        pygame.draw.rect(surf, ENEMY, self.rect, border_radius=10)
        grill = pygame.Rect(self.rect.x + 10, self.rect.y + 8, self.rect.width - 20, 10)
        pygame.draw.rect(surf, (80, 20, 20), grill, border_radius=4)

# Road stripe manager
class Road:
    def __init__(self):
        self.stripes = []
        self.gap = 32
        self.len = 24
        self.speed = 6
        # Pre-fill stripes
        for y in range(-100, HEIGHT + 100, self.gap * 2):
            for i in range(1, LANE_COUNT):
                x = ROAD_MARGIN + i * LANE_WIDTH
                self.stripes.append(pygame.Rect(x - 4, y, 8, self.len))

    def update(self, speed_scale=1.0):
        for s in self.stripes:
            s.y += int(self.speed * speed_scale)
        # recycle
        for s in self.stripes:
            if s.top > HEIGHT:
                s.y = -self.len

    def draw(self, surf):
        # Road background
        pygame.draw.rect(surf, ROAD, (ROAD_MARGIN, 0, WIDTH - ROAD_MARGIN * 2, HEIGHT))
        # Edge lines
        pygame.draw.rect(surf, LINE, (ROAD_MARGIN - 6, 0, 6, HEIGHT))
        pygame.draw.rect(surf, LINE, (WIDTH - ROAD_MARGIN, 0, 6, HEIGHT))
        # Lane stripes
        for s in self.stripes:
            pygame.draw.rect(surf, LINE, s)

# Game logic helpers

def spawn_enemy(enemies, difficulty_speed):
    # Choose a lane not currently occupied at the very top to reduce instant collisions
    occupied = {min(max((e.rect.centerx - ROAD_MARGIN) // LANE_WIDTH, 0), LANE_COUNT - 1) for e in enemies if e.rect.top < 120}
    lanes = [i for i in range(LANE_COUNT) if i not in occupied]
    if not lanes:
        return
    lane = random.choice(lanes)
    enemies.append(Enemy(lane, difficulty_speed))


def draw_hud(surf, score, high, paused, speed_mult):
    txt = FONT.render(f"Score: {score}", True, (230, 230, 230))
    surf.blit(txt, (12, 10))
    hi = FONT.render(f"Best: {high}", True, (230, 230, 230))
    surf.blit(hi, (WIDTH - hi.get_width() - 12, 10))
    sp = FONT.render(f"x{speed_mult:.2f}", True, (180, 180, 180))
    surf.blit(sp, (12, 36))
    if paused:
        p = BIG.render("PAUSED", True, (255, 255, 255))
        surf.blit(p, (WIDTH // 2 - p.get_width() // 2, HEIGHT // 2 - p.get_height() // 2))


def draw_game_over(surf, score, high):
    title = BIG.render("CRASH!", True, (255, 255, 255))
    msg = FONT.render("Press R to restart or ESC to quit", True, (230, 230, 230))
    sc = FONT.render(f"Score: {score}   Best: {high}", True, (230, 230, 230))
    surf.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 90))
    surf.blit(sc, (WIDTH // 2 - sc.get_width() // 2, HEIGHT // 2 - 30))
    surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 + 20))


def main():
    player = Player()
    road = Road()
    enemies = []

    score = 10000
    high_score = 12000
    state = "RUN"
    paused = False

    # Timers
    spawn_timer = 0
    spawn_interval = 900  # ms, will reduce with difficulty
    difficulty_timer = 0
    base_enemy_speed = 6

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit()
                if state == "RUN":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        player.move_dir = -1
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        player.move_dir = 1
                    elif event.key == pygame.K_p:
                        paused = not paused
                elif state == "OVER":
                    if event.key == pygame.K_r:
                        # restart
                        player = Player()
                        enemies.clear()
                        score = 0
                        spawn_timer = 0
                        spawn_interval = 900
                        difficulty_timer = 0
                        base_enemy_speed = 6
                        state = "RUN"
                        paused = False
            elif event.type == pygame.KEYUP and state == "RUN":
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    player.move_dir = 0

        # Update
        if state == "RUN" and not paused:
            # Difficulty ramp over time
            difficulty_timer += dt
            speed_mult = 1.0 + (difficulty_timer // 5000) * 0.1  # +0.1 every 5s
            speed_mult = min(speed_mult, 2.2)

            road.update(speed_mult)
            player.update()

            # Spawn enemies
            spawn_timer += dt
            current_interval = max(320, int(spawn_interval / speed_mult))
            if spawn_timer >= current_interval:
                spawn_timer = 0
                spawn_enemy(enemies, base_enemy_speed * speed_mult)

            # Update enemies
            for e in enemies:
                e.update()
            enemies = [e for e in enemies if not e.offscreen()]

            # Collision
            for e in enemies:
                if e.rect.colliderect(player.rect):
                    state = "OVER"
                    high_score = max(high_score, score)
                    break

            # Scoring: time survived
            score += int(10 * (dt / 1000.0) * speed_mult)

        # Draw
        screen.fill(BG)
        road.draw(screen)
        for e in enemies:
            e.draw(screen)
        player.draw(screen)

        speed_mult = 1.0 + (difficulty_timer // 5000) * 0.1 if state == "RUN" else 1.0
        draw_hud(screen, score, max(high_score, score), paused, speed_mult)

        if state == "OVER":
            draw_game_over(screen, score, high_score)

        pygame.display.flip()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        pygame.quit()
        raise

