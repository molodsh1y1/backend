from django.db import connection
from django.db import reset_queries
import time
import functools


# Decorator for query logging
def query_debugger(func):
    @functools.wraps(func)
    def inner_func(*args, **kwargs):
        reset_queries()

        start_queries = len(connection.queries)
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        end_queries = len(connection.queries)

        # Output query details
        for index, query in enumerate(connection.queries):
            print(f"Query #{index + 1}: {query['sql']}")
            print(f"Time: {query['time']}s\n")

        print(f"Function: {func.__name__}")
        print(f"Number of queries: {end_queries - start_queries}")
        print(f"Execution time: {(end - start):.3f}s")

        return result

    return inner_func
