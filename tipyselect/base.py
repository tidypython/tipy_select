import operator

from functools import reduce, update_wrapper
from ordered_set import OrderedSet


class Selector(object):
    def __init__(self, selector):
        self.selector = selector

    def __call__(self, cols):
        return self.selector(cols)

    def __neg__(self):
        return Selector(lambda cols: result_set(cols.keys()) - self(cols))

    def __reversed__(self):
        return Selector(lambda cols: result_set(reversed(self(cols))))

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
    result = Selector(lambda cols: result_set(selector(cols)))
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


def result_set(results):
    return OrderedSet(results)


def variadic_predicate(simple_predicate):
    def predicate(*args):
        if len(args) == 1:
            return simple_predicate(*args)
        else:
            return reduce(operator.__or__, map(simple_predicate, args))

    return predicate
