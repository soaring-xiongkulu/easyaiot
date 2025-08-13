from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Iterable, Optional, Union, Any

thread_pool = ThreadPoolExecutor()

def wait_muti_run(fn: Callable, args_list: Optional[Iterable[Union[dict, list, Any]]] = None,
                  count: Optional[int] = None) -> Iterable:
    fs = []
    def submit(arg: Any) -> Future:
        if type(arg) == dict:
            return thread_pool.submit(fn, **arg)
        elif type(arg) == list:
            return thread_pool.submit(fn, *arg)
        return thread_pool.submit(fn, arg)

    fs += [submit(arg) for arg in args_list]
    if count:
        fs += [thread_pool.submit(fn) for _ in range(count)]

    return [fs.result() for fs in fs]
