import collections
from typing import Union

# from loguru import logger


class SimpleGraph:
    def __init__(self):
        self.edges = {}

    def neighbors(self, number):
        return self.edges[number]


class Queue:
    def __init__(self):
        self.elements = collections.deque()

    def empty(self):
        return len(self.elements) == 0

    def put(self, number):
        self.elements.append(number)

    def get(self):
        return self.elements.popleft()


def up(coord_x: int, coord_y: int) -> str:
    coord_y -= 1
    return f"{coord_x}{coord_y}"


def right(coord_x: int, coord_y: int) -> str:
    coord_x += 1
    return f"{coord_x}{coord_y}"


def down(coord_x: int, coord_y: int) -> str:
    coord_y += 1
    return f"{coord_x}{coord_y}"


def left(coord_x: int, coord_y: int) -> str:
    coord_x -= 1
    return f"{coord_x}{coord_y}"


def create_neighbors_dict(js_obj: object) -> dict:
    neighbors_dict = {}
    neighbors = {
        "u": up,
        "r": right,
        "d": down,
        "l": left,
    }
    key = False
    if js_obj['s']['own']:
        key = True
    for num_row, row in enumerate(js_obj['s']['map']):
        for num_cell, cell in enumerate(row):
            if cell:
                if cell['p']:
                    doors = cell.get('doors')
                    if doors:
                        for way in "urdl":
                            dell_way = doors.get(way)
                            if dell_way:
                                if not key:
                                    cell['p'] = cell['p'].replace(way, "")
                    for i in cell['p']:
                        position = f"{num_row}{num_cell}"
                        condition = neighbors_dict.get(position)
                        coord_x = num_row
                        coord_y = num_cell
                        if condition:
                            neighbors_dict[position].append(
                                neighbors[i](coord_x, coord_y))
                        else:
                            neighbors_dict[position] = [
                                neighbors[i](coord_x, coord_y)]
    return neighbors_dict


def get_graph(js_obj: object) -> SimpleGraph:
    graph = SimpleGraph()
    graph.edges = create_neighbors_dict(js_obj)
    return graph


def breadth_first_search(graph: object, start: str, goal: str) -> dict:
    frontier = Queue()
    frontier.put(start)
    came_from = {}
    came_from[start] = None
    not_visited = []
    while not frontier.empty():
        current = frontier.get()
        if current == goal:
            break
        try:
            condition = graph.neighbors(current)
        except Exception:
            came_from.pop(current)
            not_visited.append(current)
        else:
            for next_step in condition:
                if next_step not in came_from and next_step not in not_visited:
                    frontier.put(next_step)
                    came_from[next_step] = current
    return came_from


def breadth_first_search_2(graph: SimpleGraph, start: str) -> list:
    frontier = Queue()
    frontier.put(start)
    came_from = {}
    came_from[start] = True
    not_visited = []
    while not frontier.empty():
        current = frontier.get()
        try:
            condition = graph.neighbors(current)
        except Exception:
            came_from.pop(current)
            not_visited.append(current)
        else:
            for next_step in condition:
                if next_step not in came_from and next_step not in not_visited:
                    frontier.put(next_step)
                    came_from[next_step] = True
    return not_visited


def uncharted_path(js_obj: object) -> list:
    start = f"{js_obj['s']['x']}{js_obj['s']['y']}"
    graph = get_graph(js_obj)
    not_visited = breadth_first_search_2(graph, start)
    return not_visited


def reconstruct_path(came_from: dict, start: str, goal: str) -> list:
    current = goal
    path = [current]
    while current != start:
        current = came_from[current]
        path.append(current)
    path.remove(start)
    path.reverse()
    return path


def find_near_way(js_obj: object, stop: list) -> list:
    """
    Find nearest way
    """
    start = f"{js_obj['s']['x']}{js_obj['s']['y']}"
    graph = get_graph(js_obj)
    ways = []
    lenth = 25
    go_to = ''
    for step in stop:
        came_from = breadth_first_search(graph, start, step)
        ways.append(reconstruct_path(came_from, start, step))
    for way in ways:
        if len(way) <= lenth:
            lenth = len(way)
            go_to = way
    return go_to


def find_way_to(js_obj: object, step: str) -> list[str]:
    """
    Create ways list
    """
    start = f"{js_obj['s']['x']}{js_obj['s']['y']}"
    graph = get_graph(js_obj)
    came_from = breadth_first_search(graph, start, step)
    ways = reconstruct_path(came_from, start, step)
    return ways


def check_move(start_x: int, start_y: int, coord_x: int, coord_y: int) -> str:
    """
    Return way
    :return: str like "moveDown"
    """
    if start_x > coord_x:
        go = "moveLeft"
    elif start_x < coord_x:
        go = "moveRight"
    elif start_y < coord_y:
        go = "moveDown"
    elif start_y > coord_y:
        go = "moveUp"
    return go


def create_right_way(js_obj: object, go_to: Union[str, list[str]]) -> list:
    """
    Create list ways
    """
    move_list = []
    start_x = js_obj['s']['x']
    start_y = js_obj['s']['y']
    if isinstance(go_to, str):
        coord_x = int(go_to[0])
        coord_y = int(go_to[1])
        go = check_move(start_x, start_y, coord_x, coord_y)
        move_list.append(go)
    else:
        for move in go_to:
            coord_x = int(move[0])
            coord_y = int(move[1])
            go = check_move(start_x, start_y, coord_x, coord_y)
            start_x = coord_x
            start_y = coord_y
            move_list.append(go)
    return move_list
