# PythonECS - Entity Component System

# ================================================================================================ #
# Imports

from enum import Enum, auto
from typing import Any, Callable, Optional, Type, TypeVar

# ================================================================================================ #
# Constants

T = TypeVar("T")

# ================================================================================================ #
# Stage Enum

class Stage(Enum):
	STARTUP = auto()
	PRE_UPDATE = auto()
	UPDATE = auto()
	POST_UPDATE = auto()
	RENDER = auto()
	CLEANUP = auto()

# ================================================================================================ #
# Event Manager Class

class EventManager:
	def __init__(self):
		self._events: dict[Type, list[Any]] = {}

	def send(self, event: Any) -> None:
		event_type = type(event)
		if event_type not in self._events:
			self._events[event_type] = []
		self._events[event_type].append(event)

	def read(self, event_type: Type[T]) -> list[T]:
		return self._events.get(event_type, [])

	def clear(self) -> None:
		self._events.clear()

# ================================================================================================ #
# Component Registry Class

class ComponentRegistry:
	def __init__(self):
		self._masks: dict[Type, int] = {}
		self._next_bit = 0

	def get_mask(self, component_type: Type) -> int:
		if component_type not in self._masks:
			self._masks[component_type] = 1 << self._next_bit
			self._next_bit += 1
		return self._masks[component_type]

	def get_query_mask(self, *component_types: Type) -> int:
		query_mask = 0
		for c_type in component_types:
			query_mask |= self.get_mask(c_type)
		return query_mask

# ================================================================================================ #
# Parent Class

class Parent:
	def __init__(self, entity_id: int):
		self.entity_id = entity_id

# ================================================================================================ #
# Child Class

class Children:
	def __init__(self):
		self.entities: set[int] = set()

# ================================================================================================ #
# Entity Component System Class

class EntityComponentSystem:
	def __init__(self):
		self._next_entity_id = 0
		self._free_entities: list[int] = []

		self._registry = ComponentRegistry()
		self._entity_masks: dict[int, int] = {}
		self._components: dict[Type, dict[int, Any]] = {}

		# Observer tracking (Added / Removed this frame)
		self._added_components: dict[Type, set[int]] = {}
		self._removed_components: dict[Type, set[int]] = {}

		# Resources & Events
		self._resources: dict[Type, Any] = {}
		self.events = EventManager()

		# System Scheduler
		self._stages: dict[Stage, list[Callable]] = {stage: [] for stage in Stage}
		self._has_started = False

	# ================================================== #
	# Entity Management

	def create_entity(self) -> int:
		if self._free_entities:
			entity = self._free_entities.pop()
		else:
			entity = self._next_entity_id
			self._next_entity_id += 1

		self._entity_masks[entity] = 0
		return entity

	def create_entity_with(self, *components: Any) -> int:
		entity = self.create_entity()
		self.add_components(entity, *components)
		return entity

	def destroy_entity(self, entity: int) -> None:
		if entity not in self._entity_masks:
			return

		# Destroy children recursively if any
		if Children in self._components and entity in self._components[Children]:
			children = list(self._components[Children][entity].entities)
			for child in children:
				self.destroy_entity(child)

		# Unlink from parent
		if Parent in self._components and entity in self._components[Parent]:
			parent_id = self._components[Parent][entity].entity_id
			if Children in self._components and parent_id in self._components[Children]:
				self._components[Children][parent_id].entities.discard(entity)

		# Clear components
		entity_mask = self._entity_masks.pop(entity)
		for c_type, pool in list(self._components.items()):
			c_mask = self._registry.get_mask(c_type)
			if entity_mask & c_mask:
				pool.pop(entity, None)
				self._track_removal(c_type, entity)

		self._free_entities.append(entity)

	def set_parent(self, child: int, parent: int) -> None:
		self.add_component(child, Parent(parent))
		if not self.has_component(parent, Children):
			self.add_component(parent, Children())
		component = self.get_component(parent, Children)
		if component is not None:
			component.entities.add(child)

	# ================================================== #
	# Component Management

	def add_component(self, entity: int, component: Any) -> None:
		c_type = type(component)
		c_mask = self._registry.get_mask(c_type)

		if c_type not in self._components:
			self._components[c_type] = {}

		self._components[c_type][entity] = component
		self._entity_masks[entity] |= c_mask
		self._track_addition(c_type, entity)

	def add_components(self, entity: int, *components: Any) -> None:
		for component in components:
			self.add_component(entity, component)

	def remove_component(self, entity: int, component_type: Type) -> None:
		c_mask = self._registry.get_mask(component_type)
		if self._entity_masks.get(entity, 0) & c_mask:
			self._entity_masks[entity] &= ~c_mask
			self._components[component_type].pop(entity, None)
			self._track_removal(component_type, entity)

	def has_component(self, entity: int, component_type: Type) -> bool:
		c_mask = self._registry.get_mask(component_type)
		return bool(self._entity_masks.get(entity, 0) & c_mask)

	def get_component(self, entity: int, component_type: Type[T]) -> Optional[T]:
		result = self._components.get(component_type, None)
		if result is None: return None
		return result.get(entity, None)

	# ================================================== #
	#  Queries & Observers

	def query(self, *component_types: Type):
		"""Yields (entity_id, comp1, comp2...) for all matching entities via bitmask."""
		query_mask = self._registry.get_query_mask(*component_types)
		if query_mask == 0:
			return

		pools = [self._components[c] for c in component_types if c in self._components]
		if len(pools) < len(component_types):
			return  # One of the components has never been registered

		for entity, mask in self._entity_masks.items():
			if (mask & query_mask) == query_mask:
				yield entity, *(pool[entity] for pool in pools)

	def query_first(self, *component_types: Type):
		"""Returns the first entity found with the matching component types."""
		query_mask = self._registry.get_query_mask(*component_types)
		if query_mask == 0: return

		pools = [self._components[c] for c in component_types if c in self._components]
		if len(pools) < len(component_types): return

		for entity, mask in self._entity_masks.items():
			if (mask & query_mask) == query_mask:
				return entity, *(pool[entity] for pool in pools)

	def get_added(self, component_type: Type) -> set[int]:
		"""Returns entity IDs that gained this component type THIS frame."""
		return self._added_components.get(component_type, set())

	def get_removed(self, component_type: Type) -> set[int]:
		"""Returns entity IDs that lost this component type THIS frame."""
		return self._removed_components.get(component_type, set())

	def _track_addition(self, c_type: Type, entity: int) -> None:
		if c_type not in self._added_components:
			self._added_components[c_type] = set()
		self._added_components[c_type].add(entity)

	def _track_removal(self, c_type: Type, entity: int) -> None:
		if c_type not in self._removed_components:
			self._removed_components[c_type] = set()
		self._removed_components[c_type].add(entity)

	# ================================================== #
	# Resource Management

	def set_resource(self, resource: Any) -> None:
		self._resources[type(resource)] = resource

	def get_resource(self, resource_type: Type[T]) -> T:
		return self._resources[resource_type]

	# ================================================== #
	# Systems & Scheduler

	def add_system(self, system: Callable, stage: Stage = Stage.UPDATE) -> None:
		if system not in self._stages[stage]:
			self._stages[stage].append(system)

	def add_systems(self, stage: Stage, *systems: Callable) -> None:
		for system in systems:
			self.add_system(system, stage)

	def startup(self) -> None:
		if not self._has_started:
			for system in self._stages[Stage.STARTUP]:
				system(self)
			self._has_started = True

	def update(self) -> None:
		"""Executes the standard frame loop across scheduled stages."""
		if not self._has_started:
			self.startup()

		loop_stages = [
			Stage.PRE_UPDATE,
			Stage.UPDATE,
			Stage.POST_UPDATE,
			Stage.RENDER,
			Stage.CLEANUP,
		]

		for stage in loop_stages:
			for system in self._stages[stage]:
				system(self)

		# Clear frame-scoped state during cleanup stage
		self.events.clear()
		self._added_components.clear()
		self._removed_components.clear()

# ================================================================================================ #