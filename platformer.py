# Platformer

# ================================================================================================ #
# Imports

import pygame as pg

from dataclasses import dataclass
from enum import auto, IntEnum
from time import time

from EntityComponentSystem import *

# ================================================================================================ #
# Constants

COLORS = {
	'dirt': (131, 61, 0),
	'grass': (70, 110, 60),
	'sky': (80, 160, 230)
}

# ================================================================================================ #
# ECS Resources

@dataclass(slots = True)
class DeltaTime:
	dt: float
	last_frame_time: float

	def __init__(self):
		self.dt = 0
		self.last_frame_time = time()

	def update(self, *kwargs):
		now = time()
		self.dt = now - self.last_frame_time
		self.last_frame_time = now

@dataclass(slots = True)
class Window:
	surf: pg.Surface
	rect: pg.FRect

	def __init__(self, caption: str):
		self.surf = pg.display.set_mode((500, 500), pg.RESIZABLE)
		self.rect = self.surf.get_frect()

		pg.display.set_caption(caption)

	def resize(self):
		self.rect = self.surf.get_frect()
		print(f'Window has been resized to: {self.rect.size}')

# ================================================================================================ #
# ECS Components

class TILE_TYPES(IntEnum):
	GRASS = auto()
	DIRT = auto()

TILE_WIDTH: int = 32
TILE_HEIGHT: int = 32
TILE_SIZE: tuple[int, int] = (TILE_WIDTH, TILE_HEIGHT)

TILE_SURFACES = {
	TILE_TYPES.GRASS: pg.surface.Surface(TILE_SIZE),
	TILE_TYPES.DIRT: pg.surface.Surface(TILE_SIZE)
}

TILE_SURFACES[TILE_TYPES.GRASS].fill(COLORS['grass'])
TILE_SURFACES[TILE_TYPES.DIRT].fill(COLORS['dirt'])

@dataclass(slots = True)
class Tile:
	tile_type: TILE_TYPES
	surf: pg.Surface
	rect: pg.FRect
	z: float

	def __init__(self, tile_type: TILE_TYPES, x: float, y: float, z: float = 1.0):
		self.tile_type = tile_type
		self.surf = TILE_SURFACES[self.tile_type]
		self.rect = self.surf.get_frect(bottomleft = (x, y))
		self.z = z

	def update(self, **kwargs):
		pass

@dataclass(slots = True)
class SolidBody:
	rect_list: list[pg.FRect]

	def __init__(self, *rects: pg.FRect):
		self.rect_list = list(rects)

def create_ecs_tile(ecs: EntityComponentSystem, tile_type: TILE_TYPES, col: int, row: float):
	x = col * TILE_WIDTH
	y = ecs.get_resource(Window).rect.h - row * TILE_HEIGHT
	ecs.create_entity_with(
		Tile(tile_type, x, y),
		SolidBody(pg.FRect(x, y, TILE_WIDTH, TILE_HEIGHT))
	)

# ================================================================================================ #

class Platformer:
	def __init__(self):
		pg.init()

		self.ecs = EntityComponentSystem()
		self.ecs.set_resource(pg.Clock())
		self.ecs.set_resource(DeltaTime())
		self.ecs.set_resource(Window('Platformer'))

		create_ecs_tile(self.ecs, TILE_TYPES.GRASS, 0, 1)
		create_ecs_tile(self.ecs, TILE_TYPES.DIRT, 1, 0)

	# ================================================== #
	# ECS Resource Shortcuts

	@property
	def clock(self) -> pg.Clock:
		return self.ecs.get_resource(pg.Clock)

	@property
	def delta_time(self) -> float:
		return self.ecs.get_resource(DeltaTime).dt

	@property
	def window(self) -> Window:
		return self.ecs.get_resource(Window)

	# ================================================== #
	# Main Game Loop

	def run(self):
		self.flag_run = True
		while self.flag_run:
			self.clock.tick(60)
			self.user_input()
			self.update()
			self.display()

		pg.quit()

	# ================================================== #
	# User Input

	def user_input(self):
		for event in pg.event.get():
			self.handle_quit(event)
			self.handle_window_resize(event)

	def handle_quit(self, event):
		if not event.type == pg.QUIT: return

		self.flag_run = False

	def handle_window_resize(self, event):
		if not event.type == pg.VIDEORESIZE: return

		self.window.resize()
	
	# ================================================== #
	# Update

	def update(self):
		self.ecs.update()

	# ================================================== #
	# Display

	def display(self):
		self.window.surf.fill(COLORS['sky'])
		self.display_tiles()
		pg.display.flip()

	def display_tiles(self):
		all_tiles = self.ecs.query(Tile)
		visible_tiles = all_tiles
		for entity, tile in visible_tiles:
			self.window.surf.blit(tile.surf, tile.rect)

# ================================================================================================ #

if __name__ == '__main__':
	game = Platformer()
	game.run()