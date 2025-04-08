from abc import ABC, abstractmethod
from typing import Dict, List, Callable, TypeVar, Generic
import copy

TEnvironmentState = TypeVar('TEnvironmentState')
TMovementPermissions = TypeVar('TMovementPermissions', bound='BetterEnum')
TSensorPermissions = TypeVar('TSensorPermissions', bound='BetterEnum')

class ISensorData:
    pass

class BetterEnum(ABC):
    @property
    def max_value(self) -> int:
        return self.max_value

    @max_value.setter
    def max_value(self, value):
        self.max_value = value
        
    @property
    def value(self) -> int:
        return self.value
    
    @value.setter
    def value(self, value):
        if(value <= self.max_value):
            self.value = value

    def and_op(self, val: int) -> 'BetterEnum':
        v = copy.deepcopy(self)
        v.value = v.value & val
        return v

    def has_flag(self, v: 'BetterEnum') -> bool:
        return (self.value & v.value) == v.value

class MoveReturn:
    def __init__(self, move_id: int, chance: float):
        self.move_id = move_id
        self.chance = chance

class AIEnvironment(ABC, Generic[TEnvironmentState, TMovementPermissions, TSensorPermissions]):
    def __init__(self, movement_count: int = 3, sensor_count: int = 3):
        self.agent_id_to_sensor_capabilities: Dict[int, TSensorPermissions] = {}
        self.agent_id_to_movement_capabilities: Dict[int, TMovementPermissions] = {}
        self.agent_ids: set[int] = set()
        self.agent_id_to_state: Dict[int, TEnvironmentState] = {}
        self.sensor_count = sensor_count
        self.movement_count = movement_count
    class AIMove:
        def __init__(self, from_permission: BetterEnum, chance: float, move: Callable[[TEnvironmentState], TEnvironmentState]):
            self.from_permissions = from_permission
            self.chance = chance
            self.invoke_move = move
    @property
    @abstractmethod
    def sensor_capabilities(self) -> Dict[TSensorPermissions, Callable[[TEnvironmentState], ISensorData]]:
        pass

    @property
    @abstractmethod
    def movement_capabilities(self) -> Dict[TMovementPermissions, List['AIMove']]:
        pass

    @property
    @abstractmethod
    def id_to_move(self) -> Dict[int, 'AIMove']:
        pass

    @property
    @abstractmethod
    def move_to_id(self) -> Dict['AIMove', int]:
        pass

    @property
    @abstractmethod
    def is_static(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_deterministic(self) -> bool:
        pass

    @property
    @abstractmethod
    def default_state(self) -> TEnvironmentState:
        pass

    @property
    @abstractmethod
    def reset_state(self) -> TEnvironmentState:
        pass

    @abstractmethod
    def get_moves_from_state(self, state: TEnvironmentState) -> List['AIMove']:
        pass

    def get_moves(self, state: TEnvironmentState, agent_id: int) -> List[MoveReturn]:
        if agent_id not in self.agent_id_to_movement_capabilities:
            raise ValueError("Movements are not registered for the ID")
        
        movement_permissions = self.agent_id_to_movement_capabilities[agent_id]
        permission_moves = []
        
        for i in range(self.movement_count):
            permission = movement_permissions.and_op(1 << i)
            if permission != 0:
                permission_moves.extend(self.movement_capabilities[permission])
        
        all_moves = self.get_moves_from_state(state)
        result = [MoveReturn(self.move_to_id[move], move.chance) for move in all_moves if move in permission_moves]
        return result

    def get_moves_by_agent(self, agent_id: int) -> List[MoveReturn]:
        if agent_id in self.agent_id_to_state:
            return self.get_moves(self.agent_id_to_state[agent_id], agent_id)
        raise Exception("agentID not in AgentIDToState")

    def get_sensor_data(self, agent_id: int, sensor_permission: TSensorPermissions) -> ISensorData:
        return self.sensor_capabilities[sensor_permission](self.agent_id_to_state[agent_id])

    @abstractmethod
    def is_terminal_move(self, state: TEnvironmentState) -> bool:
        pass

    def make_move(self, move_id: int, agent_id: int) -> bool:
        if self.is_terminal_move(self.agent_id_to_state[agent_id]):
            self.agent_id_to_state[agent_id] = self.reset_state
            return False
        
        move = self.id_to_move[move_id]
        state = self.agent_id_to_state[agent_id]
        self.agent_id_to_state[agent_id] = move.invoke_move(state)
        return True

    def register_agent(self) -> int:
        new_id = max(self.agent_ids, default=-1) + 1
        self.agent_ids.add(new_id)
        self.agent_id_to_state[new_id] = self.default_state
        return new_id

    def register_agent_sensor_permission(self, agent_id: int, sensor_permissions: TSensorPermissions):
        if agent_id in self.agent_id_to_sensor_capabilities:
            self.agent_id_to_sensor_capabilities[agent_id].value |= sensor_permissions.value
        else:
            self.agent_id_to_sensor_capabilities[agent_id] = sensor_permissions

    def register_agent_movement_permission(self, agent_id: int, movement_permissions: TMovementPermissions):
        if agent_id in self.agent_id_to_movement_capabilities:
            self.agent_id_to_movement_capabilities[agent_id].value |= movement_permissions.value
        else:
            self.agent_id_to_movement_capabilities[agent_id] = movement_permissions

    def get_movement_permissions(self, agent_id: int) -> TMovementPermissions | None:
        return self.agent_id_to_movement_capabilities.get(agent_id)

    def get_sensor_permissions(self, agent_id: int) -> TSensorPermissions | None:
        return self.agent_id_to_sensor_capabilities.get(agent_id)
