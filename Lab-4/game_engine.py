import random
import pygame
from game.basket import Basket
from game.fruit import Fruit, Hazard
from game.particle import Particle

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.basket = Basket(width, height)
        self.fruits = []
        self.particles = []

        self.score = 0
        self.lives = 3
        self.spawn_delay = 750
        self.last_spawn_time = pygame.time.get_ticks()
        self.game_state = "PLAYING"

        self.font_big = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 28)

    def handle_event(self, event):
        if self.game_state == "GAME_OVER":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()

    def update(self):
        self.particles = [particle for particle in self.particles if particle.update()]
        if self.game_state != "PLAYING":
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.basket.move_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.basket.move_right()

        self.spawn_delay = max(400, 750 - self.score * 7)
        speed_bonus = min(1.5, self.score * 0.03)
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.spawn_delay:
            item_type = Hazard if random.random() < 0.15 else Fruit
            self.fruits.append(item_type(self.width, speed_bonus))
            self.last_spawn_time = now

        basket_rect = self.basket.rect
        for fruit in self.fruits[:]:
            fruit.update()

            if basket_rect.colliderect(fruit.rect):
                if isinstance(fruit, Hazard):
                    self.lives -= 1
                    if self.lives == 0:
                        self.game_state = "GAME_OVER"
                else:
                    self.score += 1
                    self._create_splash(fruit.x, fruit.y, fruit.color)

                self.fruits.remove(fruit)
                if self.game_state == "GAME_OVER":
                    break
                continue

            if fruit.is_missed(self.height):
                self._create_splash(fruit.x, self.height - 25, fruit.color)
                if not isinstance(fruit, Hazard):
                    self.lives -= 1
                self.fruits.remove(fruit)
                if self.lives == 0:
                    self.game_state = "GAME_OVER"
                    break

    def _create_splash(self, x, y, color):
        for _ in range(8):
            self.particles.append(Particle(x, y, color))

    def reset(self):
        self.basket = Basket(self.width, self.height)
        self.fruits.clear()
        self.particles.clear()
        self.score = 0
        self.lives = 3
        self.spawn_delay = 750
        self.last_spawn_time = pygame.time.get_ticks()
        self.game_state = "PLAYING"

    def render(self, screen):
        screen.fill((28, 32, 40))

        ground_y = self.height - 25
        pygame.draw.rect(screen, (45, 50, 60), (0, ground_y, self.width, 25))

        self.basket.render(screen)
        for fruit in self.fruits:
            fruit.render(screen)
        for particle in self.particles:
            particle.render(screen)

        score_surf = self.font_medium.render(f"Score: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (25, 20))

        lives_surf = self.font_medium.render(f"Lives: {self.lives}", True, (240, 80, 80))
        screen.blit(lives_surf, (self.width - lives_surf.get_width() - 25, 20))

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("GAME OVER", True, (235, 70, 70))
            screen.blit(over_surf, (self.width // 2 - over_surf.get_width() // 2, self.height // 2 - 40))

            final_surf = self.font_medium.render(f"Final Score: {self.score}", True, (255, 255, 255))
            screen.blit(final_surf, (self.width // 2 - final_surf.get_width() // 2, self.height // 2 + 10))

            restart_surf = self.font_medium.render("Press [R] to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 50))
