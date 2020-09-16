import re

from dataclasses import dataclass
from functools import singledispatch
from ordered_set import OrderedSet


@dataclass
class StringRange:
    start: str
    stop: str


class SelectorContainer:
    def __init__(self, function):
        self.function = function
        self.reversed = False

    def eval(self, cols):
        if not self.reversed:
            result = self.function(cols)
        else:
            result = list(OrderedSet(cols).difference(self.function(cols)))

        return result

    def reverse(self):
        self.reversed = not self.reversed
        return self


def starts_with(match):
    return SelectorContainer(lambda cols: [x for x in cols if x.startswith(match)])


def ends_with(match):
    return SelectorContainer(lambda cols: [x for x in cols if x.endswith(match)])


def contains(match):
    return SelectorContainer(lambda cols: [x for x in cols if match in x])


def matches(match):
    return SelectorContainer(lambda cols: [x for x in cols if re.search(match, x)])


def everything():
    return SelectorContainer(lambda cols: cols)


def last_col(offset=0):
    return SelectorContainer(lambda cols: [cols[-1 - offset]])


def one_of(*args):
    args = OrderedSet([*args])
    return SelectorContainer(lambda cols: list(args.intersection(cols)))


def num_range(prefix, int_range, width=None):
    new_range = [str(x) for x in list(range(int_range.start, int_range.stop + 1))]
    if width:
        new_range = [x.rjust(width, "0") for x in new_range]

    select_cols = OrderedSet([prefix + x for x in new_range])
    return SelectorContainer(
        lambda cols: list(OrderedSet(cols).intersection(select_cols))
    )


def int_range(rng):
    return SelectorContainer(lambda cols: cols[rng.start : rng.stop + 1])


def str_range(rng):
    return SelectorContainer(
        lambda cols: cols[cols.index(rng.start) : cols.index(rng.stop) + 1]
    )


def bare_string(string):
    return SelectorContainer(lambda cols: [cols[cols.index(string)]])


def reverse(container):
    return container.reverse()


def union(container1, container2):
    return SelectorContainer(
        lambda cols: list(
            OrderedSet(container1.eval(cols)).union(container2.eval(cols))
        )
    )


def intersection(container1, container2):
    return SelectorContainer(
        lambda cols: list(
            OrderedSet(container1.eval(cols)).intersection(container2.eval(cols))
        )
    )


def eval_tidy(cols, *args):
    args = [*args]
    return [x.eval(cols) for x in args]
