import re
import operator

from dataclasses import dataclass
from functools import reduce, singledispatch, update_wrapper
from ordered_set import OrderedSet


class Selector(object):
    def __init__(self, selector):
        self.selector = selector

    def __call__(self, cols):
        return self.selector(cols)

    def __neg__(self):
        return Selector(lambda cols: OrderedSet(cols.keys()) - self(cols))

    def __reversed__(self):
        return Selector(lambda cols: OrderedSet(reversed(self(cols))))

    def __and__(self, other):
        return Selector(lambda cols: self(cols) & other(cols))

    def __or__(self, other):
        return Selector(lambda cols: self(cols) | other(cols))

    def __xor__(self, other):
        return Selector(lambda cols: self(cols).symmetric_difference(other(cols)))

    def __sub__(self, other):
        return Selector(lambda cols: self(cols).difference(other(cols)))

    def __invert__(self):
        return -self

    def __inv__(self):
        return -self


def dict_selector(selector):
    result = Selector(lambda cols, **kwargs: OrderedSet(selector(cols)))
    update_wrapper(result, selector)
    return result


def predicate_selector(predicate):
    result = Selector(
        lambda cols, **kwargs: OrderedSet(
            [
                name
                for name, series in cols.items()
                if predicate(name=name, series=series)
            ]
        )
    )
    update_wrapper(result, predicate)
    return result


def variadic_predicate(simple_predicate):
    def predicate(*args):
        if len(args) == 1:
            return simple_predicate(*args)
        else:
            return reduce(operator.__or__, map(simple_predicate, args))

    return predicate


@variadic_predicate
def starts_with(prefix):
    return predicate_selector(lambda name, **kwargs: name.startswith(prefix))


@variadic_predicate
def ends_with(suffix):
    return predicate_selector(lambda name, **kwargs: name.endswith(suffix))


@variadic_predicate
def contains(part):
    return predicate_selector(lambda name, **kwargs: part in name)


@variadic_predicate
def matches(regexp):
    return predicate_selector(
        lambda name, **kwargs: re.search(regexp, name) is not None
    )


def num_range(prefix, int_range, width=0):
    new_range = [
        str(x).rjust(width, "0")
        for x in list(range(int_range.start, int_range.stop + 1))
    ]
    return predicate_selector(
        lambda name, **kwargs: name.startswith(prefix)
        and name[len(prefix) :] in new_range
    )


def all_of(*args):
    def selector(cols):
        subset = OrderedSet(args)
        if subset.issubset(OrderedSet(cols.keys())):
            return subset
        else:
            raise ValueError

    return dict_selector(selector)


def any_of(*args):
    return predicate_selector(lambda name, **kwargs: name in [*args])


def everything():
    return dict_selector(lambda cols: cols.keys())


def last_col(offset=0):
    return dict_selector(lambda cols: cols.keys()[-1 - offset])


@variadic_predicate
def int_range(int_range):
    return dict_selector(
        lambda cols: cols.keys()[(int_range.start) : (int_range.stop + 1)]
    )


@variadic_predicate
def where(func):
    return predicate_selector(
        lambda series, **kwargs: func(type=series.dtype, values=series.values)
    )


@dataclass
class StringRange:
    start: str
    stop: str


def enumerate2(iterator, start=0):
    index = 0
    for (*yields,) in iterator:
        yield index, *yields
        index += 1


@variadic_predicate
def str_range(str_range):
    def selector(cols, **kwargs):
        reverse_dict = {name: index for index, name, series in enumerate2(cols.items())}

        return cols.keys()[
            (reverse_dict[str_range.start]) : (reverse_dict[str_range] + 1)
        ]


def enumerate2(iterator, start=0):
    n = start
    for (*yields,) in iterator:
        yield n, *yields
        n += 1
    return dict_selector(selector)


def df_cols(df):
    return {name: series for name, series in df.items()}


def eval_tidy(df, selector):
    return selector(df_cols(df))
