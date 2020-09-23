import re

from dataclasses import dataclass
from functools import singledispatch, update_wrapper
from ordered_set import OrderedSet


class Predicate(object):
    def __init__(self, predicate):
        self.predicate = predicate

    def __call__(self, *args, **kwargs):
        return self.predicate(*args, **kwargs)

    def __not__(self):
        return Predicate(lambda *args, **kwargs: not self.predicate(*args, **kwargs))

    def __and__(self, predicate):
        return Predicate(
            lambda *args, **kwargs: self.predicate(*args, **kwargs)
            and predicate(*args, **kwargs)
        )

    def __or__(self, predicate):
        return Predicate(
            lambda *args, **kwargs: self.predicate(*args, **kwargs)
            or predicate(*args, **kwargs)
        )


def predicate(func):
    result = Predicate(func)
    update_wrapper(result, func)
    return result


def everything():
    return predicate(lambda **kwargs: True)


def starts_with(prefix):
    return predicate(lambda name, **kwargs: name.startswith(prefix))


def ends_with(suffix):
    return predicate(lambda name, **kwargs: name.endswith(suffix))


def contains(part):
    return predicate(lambda name, **kwargs: part in name)


def matches(regexp):
    return predicate(lambda name, **kwargs: re.search(regexp, name))


def one_of(*args):
    return predicate(lambda name, **kwargs: name in [*args])


def num_range(prefix, int_range, width=0):
    new_range = [
        str(x).rjust(width, "0")
        for x in list(range(int_range.start, int_range.stop + 1))
    ]
    return predicate(
        lambda name, **kwargs: name.startswith(prefix)
        and name[len(prefix) :] in new_range
    )


def last_col(offset=0):
    return predicate(lambda index, size, **kwargs: size == index - offset + 1)


def int_range(int_range):
    return predicate(
        lambda index, **kwargs: int_range.start <= index & index <= int_range.stop
    )


@dataclass
class StringRange:
    start: str
    stop: str


def str_range(str_range):
    return predicate(
        lambda index, reverse_dict, **kwargs: reverse_dict[(str_range.start)]
        <= index & index
        <= reverse_dict[(str_range.stop)]
    )


def indexed_items(df, start=0):
    n = start
    for name, series in df.items():
        yield n, name, series
        n += 1


def eval_tidy(df, predicate):
    reverse_dict = {name: index for index, name in enumerate(df.keys())}
    size = df.size

    return [
        name
        for index, name, series in indexed_items(df)
        if predicate(
            index=index, name=name, series=series, size=size, reverse_dict=reverse_dict
        )
    ]
