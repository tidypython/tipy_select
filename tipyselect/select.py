import re

from dataclasses import dataclass

from .adapters import df_cols
from .base import dict_selector, predicate_selector, result_set, variadic_predicate


def select(df, selector):
    return selector(df_cols(df))


# -----------------------------------------------------------
# Literal name selectors


def everything():
    return dict_selector(lambda cols: cols.keys())


def all_of(*args):
    def selector(cols):
        subset = result_set(args)
        if subset.issubset(result_set(cols.keys())):
            return subset
        else:
            raise ValueError

    return dict_selector(selector)


def any_of(*args):
    return predicate_selector(lambda name, **kwargs: name in [*args])


# -----------------------------------------------------------
# Name-matching selectors


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


# -----------------------------------------------------------
# Positional selectors


def last_col(offset=0):
    return dict_selector(lambda cols: cols.keys()[-1 - offset])


@variadic_predicate
def int_range(int_range):
    return dict_selector(
        lambda cols: cols.keys()[(int_range.start) : (int_range.stop + 1)]
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

    return dict_selector(selector)


# -----------------------------------------------------------
# Content matching selectors


@variadic_predicate
def where(func):
    return predicate_selector(
        lambda series, **kwargs: func(type=series.dtype, values=series.values)
    )
