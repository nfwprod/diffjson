import hashlib
import re
from .exceptions import *


# Location Path and Steps
class LocationPath():
    """LocationPath Class.

    Args:
      locationsteps(list): List of LocationStep instance.

    Attributes:
      _locationsteps(list): List of locationsteps.

    """

    def __init__(self, locationsteps):
        if not isinstance(locationsteps, list) or len(locationsteps) == 0:
            raise LocationPathFormatError()
        for ls in locationsteps:
            if not isinstance(ls, LocationStep):
                raise LocationPathFormatError(ls)

        self._locationsteps = locationsteps

    def __repr__(self):
        if isinstance(self._locationsteps[0].nodename, NodenameRoot):
            return '/' + '/'.join([str(x) for x in self._locationsteps[1:]])
        else:
            return '/'.join([str(x) for x in self._locationsteps])

    def __add__(self, ls):
        if isinstance(ls, LocationPath):
            return LocationPath(self._locationsteps + ls._locationsteps)
        elif isinstance(ls, LocationStep):
            return LocationPath(self._locationsteps + [ls])
        else:
            raise LocationPathFormatError(ls)

    def __eq__(self, lp):
        if not isinstance(lp, LocationPath):
            return False
        if not len(self._locationsteps) == len(lp._locationsteps):
            return False
        for i in range(0, len(self._locationsteps)):
            if not self._locationsteps[i] == lp._locationsteps[i]:
                return False
        return True

    def __hash__(self):
        return int(hashlib.sha256(self.__repr__().encode()).hexdigest(), 16)

    def current(self):
        """Get top locationstep.

        Returns:
          LocationStep

        """
        return self._locationsteps[0]

    def branch(self):
        """Get branch locationpath.

        Returns:
          LocationPath: Branch locationpath.
                      [] for last locationstep.

        """
        if len(self._locationsteps) > 1:
            return LocationPath(self._locationsteps[1:])
        else:
            return None


class LocationStep():
    def __init__(self, nodename, predicates=None):
        if not isinstance(nodename, NodenameBase):
            raise LocationStepFormatError()
        self.nodename = nodename
        self.set_predicates(predicates)

    def set_predicates(self, predicates):
        if not predicates:
            predicates = Predicates()
        if predicates and not isinstance(predicates, Predicates):
            raise LocationStepFormatError(predicates)
        self.predicates = predicates.sorted()

    def __repr__(self):
        predicates = ','.join([str(a) for a in self.predicates])
        if predicates:
            return '{}[{}]'.format(self.nodename, predicates)
        else:
            return '{}'.format(self.nodename)

    def __eq__(self, ls):
        if not isinstance(ls, LocationStep):
            return False
        if not self.nodename == ls.nodename:
            return False
        if not self.predicates == ls.predicates:
            return False
        return True


# Nodename Classes
class NodenameBase():
    def __init__(self, branchkey=None):
        self.branchkey = branchkey

    def __eq__(self, n):
        if not isinstance(self, NodenameBase):
            return False
        if not self.branchkey == n.branchkey:
            return False
        return True

    def __hash__(self):
        return hash((type(self), self.branchkey))

    def __repr__(self):
        return self.branchkey


class NodenameRoot(NodenameBase):
    def __init__(self):
        super().__init__(branchkey='/')


class NodenameAsterisk(NodenameBase):
    def __init__(self):
        super().__init__(branchkey='*')


class NodenameDescendant(NodenameBase):
    def __init__(self):
        super().__init__(branchkey='')


class NodenameParent(NodenameBase):
    def __init__(self):
        super().__init__(branchkey='..')


class NodenameSelf(NodenameBase):
    def __init__(self):
        super().__init__(branchkey='.')


class NodenameKey(NodenameBase):
    def __init__(self, branchkey):
        if not isinstance(branchkey, str):
            raise NodenameFormatError(branchkey)
        super().__init__(branchkey)


class NodenameIndex(NodenameBase):
    def __init__(self, branchkey):
        if isinstance(branchkey, int):
            pass
        elif isinstance(branchkey, str):
            if not re.match(r'^[0-9]+$', branchkey):
                raise NodenameFormatError(branchkey)
            branchkey = int(branchkey)
        else:
            raise NodenameFormatError(branchkey)

        super().__init__(branchkey)

    def __repr__(self):
        return '[{}]'.format(self.branchkey)


# Predicate Classes
class Predicate():
    def __init__(self, locationpath, value):
        if not isinstance(locationpath, LocationPath):
            raise PredicateFormatError(locationpath)
        if not isinstance(value, str):
            raise PredicateFormatError(value)
        self.locationpath = locationpath
        self.value = value

    def __eq__(self, p):
        if not isinstance(p, Predicate):
            return Fasle
        if not self.locationpath == p.locationpath:
            return Fasle
        if not self.value == p.value:
            return Fasle

    def __repr__(self):
        return('{}={}'.format(
            str(self.locationpath), self.value))


class Predicates():
    def __init__(self, predicates=[]):
        if not isinstance(predicates, list):
            raise PredicatesFormatError()
        for predicate in predicates:
            if not isinstance(predicate, Predicate):
                raise PredicatesFormatError(predicate)

        self._predicates = predicates

    def __add__(self, predicates):
        return Predicates(self._predicates + predicates._predicates)

    def __iter__(self):
        for predicate in self._predicates:
            yield predicate

    def __eq__(self, ps):
        if not isinstance(ps, Predicates):
            return False
        if not len(self._predicates) == len(ps._predicates):
            return False
        for i in range(0, len(self._predicates)):
            if self._predicates[i] != ps._predicates[i]:
                return False
        return True

    def __repr__(self):
        return ','.join([str(x) for x in self._predicates])

    def __bool__(self):
        if len(self._predicates) == 0:
            return False
        else:
            return True

    def sorted(self):
        return Predicates(sorted(self._predicates, key=lambda x: str(x)))
