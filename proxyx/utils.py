import re
import typing


def load_string_patterns(
    patterns: typing.List[str],
) -> typing.List[typing.Union[str, typing.Pattern]]:
    """
    Initializes patterns, from string to compiled Python regex pattern.

    :param patterns: List of patterns as strings.
    :return: List of initialized patterns, compiled once.
    """
    lst = []
    for p_str in patterns:
        if p_str == "*":
            lst.append(p_str)
        else:
            lst.append(re.compile(rf"{p_str}"))
    return lst
