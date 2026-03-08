from enum import IntFlag
from functools import reduce
from operator import or_ as _or_


def _with_limits(enumeration):
    """add NONE and ALL psuedo-members to enumeration"""
    none_member = enumeration(0)
    all_member = enumeration(reduce(_or_, enumeration))
    enumeration.NONE = none_member
    enumeration.ALL = all_member
    enumeration._member_map_['NONE'] = none_member
    enumeration._member_map_['ALL'] = all_member
    return enumeration


@_with_limits
class DelugeFeatures(IntFlag):
    BASE = 1  # marks all features up to 2.2.0
