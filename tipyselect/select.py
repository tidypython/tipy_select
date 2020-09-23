import re

from dataclasses import dataclass

from .adapters import df_cols
from .base import (
    dict_selector,
    predicate_selector,
    reduce_selectors,
    result_set,
    variadic_selector,
)


def select(df, *selectors):
    return reduce_selectors(selectors)(df_cols(df))


# -----------------------------------------------------------
# Literal name selectors


def everything():
    return dict_selector(lambda cols: cols.keys())


# This is equivalent to any_of(col), but avoids the extra set machinery.
# Should it be strict, like all_of?
def column(col):
    return predicate_selector(lambda name, **kwargs: name == col)


def all_of(*args):
    return one_of(*args, strict=True)


def any_of(*args):
    return one_of(*args, strict=False)


def one_of(*args, strict=False):
    def selector(cols):
        subset = result_set(args)
        colset = result_set(cols.keys())
        if subset.issubset(colset):
            return subset
        else:
            if strict:
                diff = subset.difference(colset)
                raise ValueError(
                    f"Selector `all_of` called with non-existent columns: {', '.join(diff)}."
                )
            else:
                return subset.intersection(colset)

    return dict_selector(selector)


# -----------------------------------------------------------
# Name-matching selectors


@variadic_selector
def starts_with(prefix):
    return predicate_selector(lambda name, **kwargs: name.startswith(prefix))


@variadic_selector
def ends_with(suffix):
    return predicate_selector(lambda name, **kwargs: name.endswith(suffix))


@variadic_selector
def contains(part):
    return predicate_selector(lambda name, **kwargs: part in name)


@variadic_selector
def matches(regexp):
    return predicate_selector(
        lambda name, **kwargs: re.search(regexp, name) is not None
    )


# -----------------------------------------------------------
# Positional selectors


def last_col(offset=0):
    return dict_selector(lambda cols: cols.keys()[-1 - offset])


@variadic_selector
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


@variadic_selector
def str_range(str_range):
    def selector(cols, **kwargs):
        reverse_dict = {name: index for index, name, series in enumerate2(cols.items())}

        return cols.keys()[
            (reverse_dict[str_range.start]) : (reverse_dict[str_range] + 1)
        ]

    return dict_selector(selector)


# -----------------------------------------------------------
# Content matching selectors


@variadic_selector
def where(func):
    return predicate_selector(
        lambda series, **kwargs: func(type=series.dtype, values=series.values)
    )


# -----------------------------------------------------------
# Content matching selectors


@variadic_selector
def rename(dict):
    def selector(cols):
        diff = result_set(dict.values()) - result_set(cols.keys())
        if not diff:
            return result_set([(k, v) for k, v in dict.items()])
        else:
            raise ValueError(
                f"Selector `rename` called with non-existent columns: {', '.join(diff)}."
            )

    return dict_selector(selector)
