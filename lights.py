# Lights

# ================================================================================================ #
# Imports

from math import sin, tau
from random import randint, uniform
from time import time

import pygame as pg

# ================================================================================================ #

class ColorSource:
	def __init__(self, bounding_rect: pg.FRect):
		self.bounding_rect: pg.FRect = bounding_rect
		self.position: pg.math.Vector2 = pg.math.Vector2(
			uniform(0, self.bounding_rect.w),
			uniform(0, self.bounding_rect.h)
		)
		self.velocity: pg.math.Vector2 = pg.math.Vector2(
			uniform(-1.0, 1.0),
			uniform(-1.0, 1.0)
		).normalize()
		self.velocity *= 100

	def update(self, *args, **kwargs):
		delta_time = kwargs.get('delta_time')
		if delta_time is None: return

		# Update position
		self.position += self.velocity * delta_time

		# Reflect off of bounding walls
		if self.position.x < 0:
			self.position.x *= -1
			self.velocity.x *= -1
		elif self.position.x > self.bounding_rect.w:
			self.position.x = 2 * self.bounding_rect.w - self.position.x
			self.velocity *= -1
		if self.position.y < 0:
			self.position.y *= -1
			self.velocity.y *= -1
		elif self.position.y > self.bounding_rect.h:
			self.position.y = 2 * self.bounding_rect.h - self.position.y
			self.velocity.y *= -1

# ================================================================================================ #

class Light:
	def __init__(self, x: float, y: float):
		self.x: float = x
		self.y: float = y
		self.radius: int = 10
		self.opacity: float = 1.0
		self.period: float = tau / randint(2, 10)
		self.offset: int = randint(0, 100)
		self.color: tuple[int, int, int] = (255, 255, 255)

	def update(self, *args, **kwargs):
		target_rect = kwargs.get('target_rect')
		if target_rect is None: return

		self.opacity = .5 * sin(self.period * time() + self.offset) + .5
		self.color = (
			int((self.x / target_rect.w) * 255),	# r
			int((self.y / target_rect.h) * 255),	# g
			int(((target_rect.w - self.x) / target_rect.w + self.y / target_rect.h) * 255 / 2)	# b
		)

	def display(self, *args, **kwargs):
		target_surf = kwargs.get('target_surf')
		if target_surf is None: return

		surf = pg.surface.Surface((self.radius * 2, self.radius * 2), pg.SRCALPHA)
		try:
			pg.draw.circle(surf, self.color, (self.radius, self.radius), self.radius)
			surf.set_alpha(int(self.opacity * 255))
			rect = surf.get_frect(center = (self.x, self.y))
			target_surf.blit(surf, rect)
		except:
			pass

class LightGroup:
	def __init__(self, window_rect: pg.FRect):
		self.lights: list[Light] = []
		self.fill_rect(window_rect)

	def fill_rect(self, rect: pg.FRect):
		self.lights = []
		light_radius = 10
		light_spacing = 2
		light_columns = int((rect.width - light_spacing) / (2 * light_radius + light_spacing))
		light_rows = int((rect.height - light_spacing) / (2 * light_radius + light_spacing))
		for c in range(light_columns + 1):
			for r in range(light_rows + 1):
				x = c * (2 * light_radius + light_spacing) + (light_radius + light_spacing)
				y = r * (2 * light_radius + light_spacing) + (light_radius + light_spacing)
				self.lights.append(Light(x, y))

	def update(self, *args, **kwargs):
		for light in self.lights:
			light.update(*args, **kwargs)

	def display(self, *args, **kwargs):
		for light in self.lights:
			light.display(*args, **kwargs)

# ================================================================================================ #

class Lights:
	def __init__(self):
		pg.init()

		self.clock = pg.Clock()
		self.fps = 60
		self.last_frame_time = time()
		self.delta_time = 0

		self.window_surf = pg.display.set_mode((1600, 900), pg.RESIZABLE)
		self.window_rect = self.window_surf.get_frect()

		self.light_group: LightGroup = LightGroup(self.window_rect)
		self.color_source: ColorSource = ColorSource(self.window_rect)

	# ================================================== #

	def run(self):
		self.flag_run = True
		while self.flag_run:
			self.user_input()
			self.update()
			self.display()

		pg.quit()

	# ================================================== #

	def user_input(self):
		for event in pg.event.get():
			self.handle_quit(event)
			self.handle_window_resize(event)

	def handle_quit(self, event):
		if event.type == pg.QUIT:
			self.flag_run = False

	def handle_window_resize(self, event):
		if event.type == pg.VIDEORESIZE:
			self.window_rect = self.window_surf.get_frect()
			self.light_group.fill_rect(self.window_rect)

	# ================================================== #

	def update(self):
		self.clock.tick(self.fps)
		self.update_delta_time()

		self.light_group.update(target_rect = self.window_rect)
		self.color_source.update(delta_time = self.delta_time)

	def update_delta_time(self):
		now = time()
		self.delta_time = now - self.last_frame_time
		self.last_frame_time = now

	# ================================================== #

	def display(self):
		self.window_surf.fill((0, 0, 0))
		self.light_group.display(target_surf = self.window_surf)
		pg.draw.circle(self.window_surf, (255, 255, 255), self.color_source.position.xy, 10)
		pg.display.flip()

# ================================================================================================ #

if __name__ == '__main__':
	game = Lights()
	game.run()