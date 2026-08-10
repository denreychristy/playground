# Lights

# ================================================================================================ #
# Imports

from math import sin, tau
from random import randint, uniform
from time import time

import pygame as pg

# ================================================================================================ #

def distance(vector_1: tuple[float, ...], vector_2: tuple[float, ...]) -> float:
	vector_length = len(vector_1)
	cumulative_sum = 0
	for i in range(vector_length):
		cumulative_sum += (vector_1[i] - vector_2[i]) ** 2
	return cumulative_sum ** (1 / vector_length)

# ================================================================================================ #

class ColorSource:
	def __init__(self, bounding_rect: pg.FRect, color: tuple[int, int, int]):
		self.bounding_rect: pg.FRect = bounding_rect
		self.color: tuple[int, int, int] = color
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

class ColorSourceGroup:
	def __init__(self, bounding_rect: pg.FRect):
		self.color_sources: list[ColorSource] = [
			ColorSource(bounding_rect, (255,   0,   0)),
			ColorSource(bounding_rect, (  0, 255,   0)),
			ColorSource(bounding_rect, (  0,   0, 255))
		]

	def update(self, *args, **kwargs):
		for color_source in self.color_sources:
			color_source.update(*args, **kwargs)

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

	@property
	def position(self) -> tuple[float, float]:
		return self.x, self.y

	def update(self, *args, **kwargs):
		target_rect = kwargs.get('target_rect')
		if target_rect is None: return

		color_source_group = kwargs.get('color_source_group')
		if color_source_group is None: return

		r = color_source_group.color_sources[0].position.xy
		g = color_source_group.color_sources[1].position.xy
		b = color_source_group.color_sources[2].position.xy

		max_distance = distance((0, 0), target_rect.size)

		self.opacity = .5 * sin(self.period * time() + self.offset) + .5
		
		self.color = (
			int((distance(self.position, r) / max_distance) * 255),	# r
			int((distance(self.position, g) / max_distance) * 255),	# g
			int((distance(self.position, b) / max_distance) * 255)	# b
		)

		#print(self.position, r, g, b, self.color)

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
		self.color_source_group: ColorSourceGroup = ColorSourceGroup(self.window_rect)

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

		self.color_source_group.update(delta_time = self.delta_time)
		self.light_group.update(
			target_rect = self.window_rect,
			color_source_group = self.color_source_group
		)

	def update_delta_time(self):
		now = time()
		self.delta_time = now - self.last_frame_time
		self.last_frame_time = now

	# ================================================== #

	def display(self):
		self.window_surf.fill((0, 0, 0))
		self.light_group.display(target_surf = self.window_surf)
		#for color_source in self.color_source_group.color_sources:
		#	pg.draw.circle(self.window_surf, color_source.color, color_source.position.xy, 10)
		pg.display.flip()

# ================================================================================================ #

if __name__ == '__main__':
	game = Lights()
	game.run()