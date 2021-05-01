import time


def my_timer(name):
    def my_timer_decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            # print(f"start {start}")
            result = func(*args, **kwargs)
            stop = time.perf_counter() - start
            print(f"function '{name.upper()}' worked for {stop} seconds")
            return result
        return wrapper
    return my_timer_decorator
