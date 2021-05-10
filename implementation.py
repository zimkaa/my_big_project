import collections
import json


class SimpleGraph:
    def __init__(self):
        self.edges = {}

    def neighbors(self, id):
        return self.edges[id]


class Queue:
    def __init__(self):
        self.elements = collections.deque()

    def empty(self):
        return len(self.elements) == 0

    def put(self, x):
        self.elements.append(x)

    def get(self):
        return self.elements.popleft()


# def create_actual_graph(js_obj):
#     for num_row, row in enumerate(js_obj['s']['map']):
#         if row:
#             for num_cell, cell in enumerate(row):
#                 if cell:
#                     if cell['v'] == 11:
#                         port = f"{num_row}{num_cell}"
#     start = f"{js_obj['s']['x']}{js_obj['s']['y']}"
#     goal = port

#     def up(x, y):
#         y -= 1
#         return f"{x}{y}"

#     def right(x, y):
#         x += 1
#         return f"{x}{y}"

#     def down(x, y):
#         y += 1
#         return f"{x}{y}"

#     def left(x, y):
#         x -= 1
#         return f"{x}{y}"

#     new_cell = {}
#     neighbors = {
#         "u": up,
#         "r": right,
#         "d": down,
#         "l": left,
#     }
#     for num_row, row in enumerate(js_obj['s']['map']):
#         for num_cell, cell in enumerate(row):
#             if cell['p']:
#                 for i in cell['p']:
#                     position = f"{num_row}{num_cell}"
#                     condition = new_cell.get(position)
#                     x = num_row
#                     y = num_cell
#                     if condition:
#                         new_cell[position].append(neighbors[i](x, y))
#                     else:
#                         new_cell[position] = [neighbors[i](x, y)]
#     return new_cell

#     class SimpleGraph:
#         def __init__(self):
#             self.edges = {}

#         def neighbors(self, id):
#             return self.edges[id]


#     class Queue:
#         def __init__(self):
#             self.elements = collections.deque()

#         def empty(self):
#             return len(self.elements) == 0

#         def put(self, x):
#             self.elements.append(x)

#         def get(self):
#             return self.elements.popleft()

#     graph = SimpleGraph()
#     graph.edges = new_cell

#     def breadth_first_search_3(graph, start, goal):
#         # печать того, что мы нашли
#         frontier = Queue()
#         frontier.put(start)
#         came_from = {}
#         came_from[start] = None

#         while not frontier.empty():
#             current = frontier.get()
#             if current == goal:
#                 print("break")
#                 break
#             for next_step in graph.neighbors(current):
#                 if next_step not in came_from:
#                     frontier.put(next_step)
#                     came_from[next_step] = current
#         return came_from

#     def reconstruct_path(came_from, start, goal):
#         current = goal
#         path = [current]
#         while current != start:
#             current = came_from[current]
#             path.append(current)
#         path.reverse() # необязательно
#         return path

#     came_from = breadth_first_search_3(graph, start, goal)
#     may_be_go = reconstruct_path(came_from, start, goal)
#     return may_be_go


def breadth_first_search(graph, start, goal):
    frontier = Queue()
    frontier.put(start)
    came_from = {}
    came_from[start] = None
    not_visited = []
    while not frontier.empty():
        current = frontier.get()
        if current == goal:
            print("break")
            break
        try:
            condition = graph.neighbors(current)
        except Exception:
            print(f"go_to_new_cell {current}")
            came_from.pop(current)
            not_visited.append(current)
        else:
            for next_step in condition:
                if next_step not in came_from and next_step not in not_visited:
                    frontier.put(next_step)
                    came_from[next_step] = current
    return came_from


def breadth_first_search_2(graph, start):
    frontier = Queue()
    frontier.put(start)
    came_from = {}
    came_from[start] = True
    not_visited = []
    while not frontier.empty():
        current = frontier.get()
        # if current == goal:
        #     print("break")
        #     break
        try:
            condition = graph.neighbors(current)
        except Exception:
            print(f"go_to_new_cell {current}")
            came_from.pop(current)
            not_visited.append(current)
        else:
            for next_step in condition:
                if next_step not in came_from and next_step not in not_visited:
                    frontier.put(next_step)
                    came_from[next_step] = True
    return {"came_from": came_from, "not_visited": not_visited}


def reconstruct_path(came_from, start, goal):
    current = goal
    path = [current]
    print(f"current  ---  {current}")
    while current != start:
        current = came_from[current]
        path.append(current)
    path.remove(start)  # необязательно
    path.reverse()  # необязательно
    return path


def up(x, y):
    y -= 1
    return f"{x}{y}"


def right(x, y):
    x += 1
    return f"{x}{y}"


def down(x, y):
    y += 1
    return f"{x}{y}"


def left(x, y):
    x -= 1
    return f"{x}{y}"


def create_neighbors_dict(js_obj):
    neighbors_dict = {}
    neighbors = {
        "u": up,
        "r": right,
        "d": down,
        "l": left,
    }
    for num_row, row in enumerate(js_obj['s']['map']):
        for num_cell, cell in enumerate(row):
            if cell:
                if cell['p']:
                    for i in cell['p']:
                        position = f"{num_row}{num_cell}"
                        condition = neighbors_dict.get(position)
                        x = num_row
                        y = num_cell
                        if condition:
                            neighbors_dict[position].append(neighbors[i](x, y))
                        else:
                            neighbors_dict[position] = [neighbors[i](x, y)]
    return neighbors_dict


def get_graph(js_obj):
    graph = SimpleGraph()
    graph.edges = create_neighbors_dict(js_obj)
    return graph


def get_port_cell(js_obj):
    for num_row, row in enumerate(js_obj['s']['map']):
        if row:
            for num_cell, cell in enumerate(row):
                if cell:
                    # print(cell)
                    # print(type(cell))
                    if cell['v'] == 11:
                        port_cell = f"{num_row}{num_cell}"
                        return port_cell


def main(js_obj):
    print(js_obj)
    port = get_port_cell(js_obj)
    print(f"port {port}")
    start = f"{js_obj['s']['x']}{js_obj['s']['y']}"
    print(f"start {start}")
    graph = get_graph(js_obj)
    came_from = breadth_first_search(graph, start, port)
    way = reconstruct_path(came_from, start, port)
    print(f"way {way} len(way) {len(way)}")
    if len(way) <= 4:
        print("go_to_door")


def uncharted_path(js_obj):
    print(js_obj)
    # port = get_port_cell(js_obj)
    # print(f"port {port}")
    start = f"{js_obj['s']['x']}{js_obj['s']['y']}"
    print(f"start {start}")
    graph = get_graph(js_obj)
    data = breadth_first_search_2(graph, start)
    came_from = data["came_from"]
    not_visited = data["not_visited"]
    print(f"came_from {came_from}")
    print(f"not_visited {not_visited}")
    # way = reconstruct_path(came_from, start, port)
    return


if __name__ == '__main__':
    with open('my_map.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    main(data)
    # uncharted_path(data)
