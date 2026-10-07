import random
import pygame


class Particle:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.velocity_x = random.uniform(-3.0, 3.0)
        self.velocity_y = random.uniform(-4.5, -1.0)
        self.radius = random.randint(2, 4)
        self.life = 24
        self.max_life = self.life

    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.18
        self.life -= 1
        return self.life > 0

    def render(self, surface):
        radius = max(1, int(self.radius * self.life / self.max_life))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius)