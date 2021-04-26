from .exceptions_branch import *
from .searchpath import (parse,
        LocationPath, LocationStep,
        NodenameRoot, NodenameAsterisk, NodenameDescendant,
        NodenameParent, NodenameSelf,
        NodenameKey, NodenameIndex)


def generate_branch(data):
    """Generate Branch.

    Args:
      data(Any): Json format data.
                 dict, list, str, int, float, bool

    Returns:
      BranchRoot with branch formed data.

    """

    return RootBranch(data)


class BranchBase():
    """Template Class for branch base.
    All Branch and Leaf class must be inherit this class.

    Args:
      data(any json data): Json format data under current branch.
                 dict, list, str, int, float, bool

      parent(BranchBase): Parent branch of this branch.

      _childbranches(dict or list): Child branches, wrapped by attributes.

    Attributes:
      parent(BranchBase): Parent branch of this branch.

      childnodenames(list): List of NodeName for childbranches. (getter)

      childbranches(list): List of childbranches. (getter)

      descendants(list): List of descendant branches. (getter)

      rootbranch(RootBranch): RootBranch of this branch. (getter)

      nodename(NodenameBase): Nodename of this branch. (getter)

      locationpath(LocationPath): LocationPath of this branch. (getter)

    Note:
      Not allow to access directory because data types are
      different for all branch types.

    """
    # Initialize Functions
    def __init__(self, data, parent):
        self.parent = parent
        self._childbranches = self._generate_childbranches(data)
        self.value = None  # For Leaf

    def _generate_childbranch(self, data, parent):
        """Generate child branch from data.

        Args:
          data(Any): Json format data.
                     dict, list, str, int, float, bool

        Returns:
          BranchBase: Generated from data.

        """
        if not parent:
            raise BranchDatatypeError()
        if isinstance(data, dict):
            return DictBranch(data, parent)
        if isinstance(data, list):
            return ListBranch(data, parent)
        if isinstance(data, (str, int, float, bool)) or data is None:
            return Leaf(data, parent)

        raise BranchDatatypeError(type(data))

    def _generate_childbranches(self, data):
        """Generate child branches and contain it.

        This method differs for each branch class.

        Args:
          data(any): Json data.

        Returns:
          dict: Dict of (key: Nodename, value: BranchBase)

        """
        raise NotImplementedError()

    @property
    def childnodenames(self):
        """Nodenames of branches.

        Returns:
          list: List of branch nodenames.

        """
        return list(self._childbranches.keys())

    @property
    def childbranches(self):
        """Return all child branches.

        Returns:
          list: List of all child branches.
        """
        return list(v for v in self._childbranches.values())

    @property
    def descendants(self):
        """Return all descendants branches.

        Returns:
          list: List of all descendants branches in flat format.

        """
        result = self.childbranches
        for branch in self.childbranches:
            result += branch.descendants
        return result

    @property
    def rootbranch(self):
        """Return root branch.

        Returns:
          RootBranch: Root of this branch.

        """
        if not self.parent:
            return self
        return self.parent.rootbranch

    @property
    def nodename(self):
        """Nodename for self.

        Returns:
          NodenameBase: nodename.

        Note:
          Nodename is unknown for branch, only parent knows.

        """
        for bnn in self.parent.childnodenames:
            branch = self.parent.childbranch(bnn)
            if id(branch) == id(self):
                return bnn
        raise BranchUnexpectedStructureError()

    @property
    def locationpath(self):
        """Extract location Path.

        Returns:
          LocationPath: LocationPath of this branch.

        """
        if self.parent.is_root():
            return LocationPath([LocationStep(self.nodename)])
        return self.parent.locationpath + LocationStep(self.nodename)

    # Operation methods
    def raw_set(self, nodename, childbranch):
        self._childbranches[nodename] = childbranch

    # Data Access Functions
    def childbranch(self, nodename):
        """Return child branch with target nodename if exist

        Args:
          nodename(NodenameBase): Child nodename.

        Returns:
          BranchBase: Target Child branch.
                  Return NullBranch if not exist.

        """
        return self._childbranches.get(nodename, NullBranch(parent=self))

    def isat(self, locationpath_str):
        """Check this branch is at target locationpath

        Args:
          locationpath_str(str): Check target.

        Returns:
          bool

        """
        locationpath = parse(locationpath_str)
        return self._isat(locationpath)

    def _isat(self, locationpath):
        """Check this branch is at target locationpath

        Args:
          locationpath(LocationPath): Check target.

        Returns:
          bool

        Note:
          Wrapped by isat.

        """
        rootbranch = self.rootbranch
        for branch in rootbranch.raw_search(locationpath):
            if branch.locationpath == self.locationpath:
                return True
        return False

    def is_root(self):
        """Check this branch is root or not.

        Returns:
          bool

        """
        raise NotImplementedError()

    def is_child(self):
        """Check this branch is child or not.

        Returns:
          bool

        """
        raise NotImplementedError()

    # Search Functions
    def search(self, locationpath_string, details=False):
        """Search target path and get json data list.

        Args:
          locationpath_string(str): XPath format search string.

          details(bool): Return searched path with value,
                         default: False(value only).

        Returns:
          list: List of json data at target path (details=False).
                With details True, list of set like
                {target_path(str), dict or list at target path}.

        Node:
          This method must be implemented in RootBranch only.

        """
        if not isinstance(locationpath_string, str):
            BranchUnexpectedArgumentError()

        locationpath = parse(locationpath_string)
        result = [(str(x.locationpath), x.dump())
                  for x in self.raw_search(locationpath)]
        if not details:
            result = [data for _, data in result]
        return result

    def raw_search(self, locationpath):
        """Search child branches by locationpath.

        Args:
          locationpath(LocationPath): Search LocationPath

        Returns:
          List: List of matched objects.

        """
        if not isinstance(locationpath, LocationPath):
            BranchUnexpectedArgumentError()
        locationstep = locationpath.current()
        nodename = locationstep.nodename
        predicates = locationstep.predicates

        # Check Nodename and find candidates
        candidates = self._search_candidates(nodename)

        # Check predicates for candidates
        candidates = [x for x in candidates if x.check_predicates(predicates)]

        # Search branches recursively and return.
        branchlocationpath = locationpath.branch()
        if not branchlocationpath:
            return candidates

        branches = []
        for candidate in candidates:
            branches += candidate.raw_search(branchlocationpath)
        return branches

    def _search_candidates(self, nodename):
        """Search branches by nodename.

        Args:
          nodename(NodenameBase): Search nodename.

        Returns:
          list: List of matched branch objects.

        """
        if isinstance(nodename, NodenameAsterisk):
            return self.childbranches
        if isinstance(nodename, NodenameDescendant):
            return self.descendants + [self]
        if isinstance(nodename, NodenameParent):
            return [self.parent]
        if isinstance(nodename, NodenameSelf):
            return [self]

        result = self.childbranch(nodename)
        if result:
            return [self.childbranch(nodename)]

        return []

    def check_predicates(self, predicates):
        """Check self branch matches predicates or not.

        Args
          predicates(Predicates): List of Arg objects.

        Returns:
          Boolean: Predicates match for the branch or not.
        """
        for predicate in predicates:
            locationpath = predicate.locationpath
            value = predicate.value

            result = False
            for branch in self.raw_search(locationpath):
                if isinstance(branch, Leaf) and str(branch.value) == value:
                    result = True
                    break
            if not result:
                return False

        return True

    # Utility methods
    def dump(self):
        """Return json data of child branches.

        Returns:
          Any json data: Dict format child branches.

        """
        raise BranchDedicatedMethodError()

    def __repr__(self):
        return str(self.dump())

    def __eq__(self, other):
        if isinstance(other, BranchBase):
            if self.dump() == other.dump():
                return True
        return False

    def __hash__(self):
        return id(self)


class RootBranch(BranchBase):
    """Class for root data in json data tree.

    Note:
      This class wraps child branches and provides methods for users.
      Have only one child branch with "/" nodename.

    """
    def __init__(self, data):
        super().__init__(data, None)

    def _generate_childbranches(self, data):
        nodename = NodenameRoot()
        return {nodename: self._generate_childbranch(data, self)}

    def dump(self):
        return self.childbranch(NodenameRoot()).dump()

    @property
    def locationpath(self):
        raise BranchRootLocationPathError()

    def is_root(self):
        return True

    def is_child(self):
        return False

    # Specific methods for RootBranch
    def set(self, locationpath_string, data):
        """Update existing branch.

        Args:
          locationpath_string(str): XPath format search string.

          data(any json data): Json format data under current branch.
                     dict, list, str, int, float, bool

        Returns:
          list: List of locationpaths where data was changed.

        """
        locationpath = parse(locationpath_string)

        result = []
        for branch in self.raw_search(locationpath):
            parent = branch.parent
            nn_or_index = branch.nodename
            result.append(parent.set(nn_or_index, data))

        return [r for r in result if r]

    def setdefault(self, locationpath_string, nodename_string, data):
        """Add new data to target DictBranch.

        Args:
          locationpath_string(str): XPath format search string.

          nodename_string(str): Nodename for new node.

          data(any json data): Json format data under current branch.
                     dict, list, str, int, float, bool

        Returns:
          list: List of locationpaths where data was changed.

        """
        locationpath = parse(locationpath_string)
        nodename = NodenameKey(nodename_string)

        result = []
        for branch in self.raw_search(locationpath):
            result.append(branch.setdefault(nodename, data))

        return [r for r in result if r]

    def insert(self, locationpath_string, index, data):
        """Insert new data to target ListBranch.

        Args:
          locationpath_string(str): XPath format search string.

          index(int): XPath format search string.

          data(any json data): Json format data under current branch.

        Returns:
          list: List of locationpaths where data was changed.

        """
        locationpath = parse(locationpath_string)

        result = []
        for branch in self.raw_search(locationpath):
            result.append(branch.insert(index, data))

        return [r for r in result if r]

    def append(self, locationpath_string, data):
        """Append new data to target ListBranch.

        Args:
          data(any json data): Json format data under current branch.

        Returns:
          list: List of locationpaths where data was changed.

        """
        locationpath = parse(locationpath_string)

        result = []
        for branch in self.raw_search(locationpath):
            result.append(branch.append(data))

        return [r for r in result if r]

    def pop(self, locationpath_string):
        """Pop BranchBase.

        Args:
          locationpath_string(str): XPath format search string.

        Returns:
          list: List of dumped Branches at target locationpath_string.

        """
        locationpath = parse(locationpath_string)

        result = []
        for branch in self.raw_search(locationpath):
            parent = branch.parent
            result.append(parent.pop(branch.nodename).dump())

        return result

    def remove(self, locationpath_string):
        """Remove BranchBase.

        Args:
          locationpath_string(str): XPath format search string.

        Note:
          Don't delete self, only delete link from parent.

        """
        locationpath = parse(locationpath_string)

        for branch in self.raw_search(locationpath):
            parent = branch.parent
            parent.remove(branch.nodename)

        return


class ChildBranch(BranchBase):
    """Class for child data in json data tree.

    Note:
      All child branch classes inherits this class.

    """
    def is_root(self):
        return False

    def is_child(self):
        return True

    def __getitem__(self, item):
        """Return child branch data like dict or list.

        Args:
          item(str or int): Str for dict(DictBranch), int for list(ListBranch).

        Returns:
          dict or list: dict for DictBranch, list for ListBranch.

        Note:
          Only for user interface. Not used for src code.
          Implemented for DictBranch and ListBranch only.

        """
        raise BranchDedicatedMethodError()

    # Operation methods
    # All operation methods are wrapped in RootBranch Class
    def set(self, nodename, data):
        """Set data to existing branch.

        Args:
          nodepath(Nodename): Nodename for set target.

          data(any json data): Json format data under current branch.
                     dict, list, str, int, float, bool

        """
        if nodename not in self.childnodenames:
            return None
        self._childbranches[nodename] = self._generate_childbranch(data, self)
        return self.locationpath + LocationStep(nodename)

    def setdefault(self, nodename, data):
        """Add new data to target DictBranch if not exists.

        Keep current data if already exists."

        Args:
          nodepath_string(str): XPath format search string.

          data(any json data): Json format data under current branch.
                     dict, list, str, int, float, bool

        Returns:
          LocationPath or None: LocationPath of new branch.
                    Return None if target nodename already exist.

        Note:
          Must be implemented for DictBranch only.

        """
        raise BranchDedicatedMethodError()

    def insert(self, index, data):
        """Insert new data to target DictBranch.

        Args:
          nodepath_string(str): XPath format search string.

          data(any json data): Json format data under current branch.
                     dict, list, str, int, float, bool

        Returns:
          LocationPath or None: LocationPath of new branch.
                    Return None if target nodename already exist.

        Note:
          Must be implemented for ListBranch only.

        """
        raise BranchDedicatedMethodError()

    def append(self, data):
        """Append new data to target DictBranch.

        Args:
          data(any json data): Json format data under current branch.
                     dict, list, str, int, float, bool

        Returns:
          LocationPath or None: LocationPath of new branch.
                    Return None if target nodename already exist.

        Note:
          Must be implemented for ListBranch only.

        """
        raise BranchDedicatedMethodError()

    def pop(self, nodename):
        """Pop target BranchBase.

        Args:
          nodename(NodeName): Pop Target

        Returns:
          BranchBase

        """
        if nodename in self.childnodenames:
            result = self._childbranches[nodename]
            del self._childbranches[nodename]

        return result

    def remove(self, nodename):
        """Remove target BranchBase.

        Args:
          nodename(NodeName): Pop Target

        """
        if nodename in self.childnodenames:
            del self._childbranches[nodename]


class DictBranch(ChildBranch):
    """Class for node data in json data tree.

    """
    def dump(self):
        return {k.branchkey: v.dump()
                for k, v in self._childbranches.items()}

    def _generate_childbranches(self, data):
        result = {}

        for key, value in data.items():
            nodename = NodenameKey(key)
            result[nodename] = self._generate_childbranch(value, self)
        return result

    def setdefault(self, nodename, data):
        if nodename in self.childnodenames:
            return None
        self._childbranches[nodename] = self._generate_childbranch(data, self)
        return self.locationpath + LocationStep(nodename)

    def __getitem__(self, item):
        nodename = NodenameKey(item)
        return self.childbranch(nodename).dump()


class ListBranch(ChildBranch):
    """Class for List type branch.

    """
    def dump(self):
        result = [(int(k.branchkey), v.dump())
                  for k, v in self._childbranches.items()]
        return [x[1] for x in sorted(result, key=lambda x: x[0])]

    def _generate_childbranches(self, data):
        result = {}

        for i in range(0, len(data)):
            value = data[i]
            nodename = NodenameIndex(i)
            result[nodename] = self._generate_childbranch(value, self)
        return result

    def insert(self, index, data):
        if index > len(self._childbranches):
            newindex = len(self._childbranches)
        else:
            newindex = index

        for i in range(len(self._childbranches), newindex, -1):
            fnode = NodenameIndex(i - 1)
            tnode = NodenameIndex(i)
            self._childbranches[tnode] = self._childbranches[fnode]
        nodename = NodenameIndex(newindex)
        self._childbranches[nodename] = self._generate_childbranch(data, self)

        return self.locationpath + LocationStep(nodename)

    def raw_append(self, data):
        nodename = NodenameIndex(len(self._childbranches))
        self._childbranches[nodename] = self._generate_childbranch(data, self)

        return self.locationpath + LocationStep(nodename)

    def __getitem__(self, item):
        nodename = NodenameIndex(item)
        return self.childbranch(nodename).dump()


class NullBranch(ChildBranch):
    """Dummy branch for not existing branch.

    """
    def __init__(self, parent=None):
        super().__init__(None, parent)

    def dump(self):
        return None

    def _generate_childbranches(self, data):
        return {}

    def __bool__(self):
        return False


class Leaf(ChildBranch):
    """Class for edge node in json data tree.

    Args:
      data(any json edge data): Edge data.
      parent(ChildBranch): Parent branch of this leaf.

    Attributes:
      data(str or int or float or bool): Edge value.

    """
    def __init__(self, data, parent):
        super().__init__(data, parent)
        self.value = data

    def dump(self):
        return self.value

    def _generate_childbranches(self, data):
        return {}
