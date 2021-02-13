from .exceptions import *
from .searchpath import *


def generate_branch(data):
    """Generate Branch.

    Args:
      data(Any): Json format data.
                 dict, list, str, int, float, bool

    Returns:
      BranchRoot with branch formed data.

    """

    return RootBranch(data)


class Branch():
    """Template Class for branch base.
    All Branch and Leaf class must be inherit this class.

    Args:
      data(any json data): Json format data under current branch.
                 dict, list, str, int, float, bool

      parent(Branch): Parent branch of this branch.

    Attributes:
      parent(Branch): Parent branch of this branch.

      childnodenames(list): List of NodeName for childbranches. (getter)

      childbranches(list): List of childbranches. (getter)

      descendants(list): List of descendant branches. (getter)

      rootbranch(RootBranch): RootBranch of this branch. (getter)

      nodename(NodenameBase): Nodename of this branch. (getter)

      locationpath(LocationPath): LocationPath of this branch. (getter)

    Note:
      Branch objects are wrapped with branches().

      Not allow to access directory because data types are
      different for all branch types.

    """
    # Initialize Functions
    def __init__(self, data, parent):
        self.parent = parent
        self._branches = self._generate_branches(data)  # For middle branches
        self.value = None  # For Leaf

    def _generate_branch(self, data, parent):
        """Generate child branch from data.

        Args:
          data(Any): Json format data.
                     dict, list, str, int, float, bool

        Returns:
          Branch: Generated from data.

        """
        if (isinstance(data, dict)):
            return DictBranch(data, parent)
        elif (isinstance(data, list)):
            return ListBranch(data, parent)
        elif (isinstance(data, str)
                or isinstance(data, int)
                or isinstance(data, float)
                or isinstance(data, bool)
                or data is None):
            return Leaf(data, parent)
        else:
            raise BranchDatatype(type(data))

    def _generate_branches(self, data):
        """Generate child branches and contain it.

        This method differs for each branch class.

        Args:
          data(any): Json data.

        Returns:
          dict: Dict of (key: Nodename, value: Branch)

        """
        raise NotImplementedError()

    # Data Access (Wrapped methods)
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
        raise BrachDedicatedMethodError()

    @property
    def childnodenames(self):
        """Nodenames of branches.

        Returns:
          list: List of branch nodenames.

        """
        return [k for k in self._branches.keys()]

    @property
    def childbranches(self):
        """Return all child branches.

        Returns:
          list: List of all child branches.
        """
        return [v for v in self._branches.values()]

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
        else:
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
        raise BranchUnexpectedStructure()

    @property
    def locationpath(self):
        """Extract location Path.

        Returns:
          LocationPath: LocationPath of this branch.

        """
        return LocationPath(self._locationsteps())

    def _locationsteps(self):
        """Extract location step list.

        Returns:
          list: List of location steps from parent to self.

        Note:
          Wrapped by locationpath.

        """
        if not self.parent:
            return []
        else:
            return self.parent._locationsteps() + [LocationStep(self.nodename)]

    # Data Access Functions
    def childbranch(self, nodename):
        """Return child branch with target nodename if exist

        Args:
          nodename(NodenameBase): Child nodename.

        Returns:
          Branch: Target Child branch.
                  Return NullBranch if not exist.

        """
        return self._branches.get(nodename, NullBranch(parent=self))

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
        for branch in rootbranch._search(locationpath):
            if branch.locationpath == self.locationpath:
                return True
        return False

    # Search Functions
    def _search_candidates(self, nodename):
        """Search branches by nodename.

        Args:
          nodename(NodenameBase): Search nodename.

        Returns:
          list: List of matched branch objects.

        """
        if isinstance(nodename, NodenameAsterisk):
            return self.childbranches
        elif isinstance(nodename, NodenameDescendant):
            return self.descendants + [self]
        elif isinstance(nodename, NodenameParent):
            return [self.parent]
        elif isinstance(nodename, NodenameSelf):
            return [self]
        else:
            result = self.childbranch(nodename)
            if result:
                return [self.childbranch(nodename)]
            else:
                return []

    def _check_predicates(self, predicates):
        """Check self branch matches predicates or not.

        Args
          predicates(Predicates): List of Arg objects.

        Returns:
          Boolean: Predicates match for the branch or not.
        """
        for p in predicates:
            locationpath = p.locationpath
            value = p.value

            result = False
            for branch in self._search(locationpath):
                if isinstance(branch, Leaf) and str(branch.value) == value:
                    result = True
                    break
            if not result:
                return False

        return True

    def _search(self, locationpath):
        """Search child branches by locationpath.

        Args:
          locationpath(LocationPath): Search LocationPath

        Returns:
          List: List of matched objects.

        """
        locationstep = locationpath.current()
        nodename = locationstep.nodename
        predicates = locationstep.predicates

        # Check Nodename and find candidates
        candidates = self._search_candidates(nodename)

        # Check predicates for candidates
        candidates = [x for x in candidates if x._check_predicates(predicates)]

        # Search branches recursively and return.
        branchlocationpath = locationpath.branch()
        if not branchlocationpath:
            return candidates
        else:
            branches = []
            for candidate in candidates:
                branches += candidate._search(branchlocationpath)
            return branches

    # Operation methods
    # All operation methods are wrapped on RootBranch Class
    def _set(self, nodename, data):
        """Set data to existing branch.

        Args:
          nodepath(Nodename): Nodename for set target.

          data(any json data): Json format data under current branch.
                     dict, list, str, int, float, bool

        """
        if nodename not in self.childnodenames:
            return None
        self._branches[nodename] = self._generate_branch(data, self)
        return self.locationpath + LocationStep(nodename)

    def _setdefault(self, nodename, data):
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
        raise BrachDedicatedMethodError()

    def _insert(self, index, data):
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
        raise BrachDedicatedMethodError()

    def _append(self, data):
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
        raise BrachDedicatedMethodError()

    def _pop(self, nodename):
        """Pop target Branch.

        Args:
          nodename(NodeName): Pop Target

        Returns:
          Branch

        """
        if nodename in self.childnodenames:
            result = self._branches[nodename]
            del(self._branches[nodename])

        return result

    def _remove(self, nodename):
        """Remove target Branch.

        Args:
          nodename(NodeName): Pop Target

        """
        if nodename in self.childnodenames:
            del(self._branches[nodename])

    # Utility methods
    def dump(self):
        """Return json data of child branches.

        Returns:
          Any json data: Dict format child branches.

        """
        raise BrachDedicatedMethodError()

    def __repr__(self):
        return str(self.dump())

    def __eq__(self, other):
        if self.dump() == other.dump():
            return True
        else:
            return False


class RootBranch(Branch):
    """Class for root data in json data tree

    Note:
      This class wraps child branches and provides methods for users.
      Have only one child branch with "/" nodename.

    """
    def __init__(self, data):
        super().__init__(data, None)

    def _generate_branches(self, data):
        nodename = NodenameRoot()
        return {nodename: self._generate_branch(data, self)}

    def dump(self):
        return self.childbranch(NodenameRoot()).dump()

    @property
    def locationpath(self):
        raise BranchRootLocationPathError()

    # Specific methods for RootBranch
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
        locationpath = parse(locationpath_string)
        if details:
            return [(str(x.locationpath), x.dump())
                    for x in self._search(locationpath)]
        else:
            return [x.dump() for x in self._search(locationpath)]

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
        branches = self._search(locationpath)

        result = []
        for branch in self._search(locationpath):
            parent = branch.parent
            nn_or_index = branch.nodename
            result.append(parent._set(nn_or_index, data))

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
        for branch in self._search(locationpath):
            result.append(branch._setdefault(nodename, data))

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
        for branch in self._search(locationpath):
            result.append(branch._insert(index, data))

        return [r for r in result if r]

    def append(self, data):
        """Append new data to target ListBranch.

        Args:
          data(any json data): Json format data under current branch.

        Returns:
          list: List of locationpaths where data was changed.

        """
        locationpath = parse(locationpath_string)

        result = []
        for branch in self._search(locationpath):
            result.append(branch._append(data))

        return [r for r in result if r]

    def pop(self, locationpath_string):
        """Pop Branch.

        Args:
          locationpath_string(str): XPath format search string.

        Returns:
          list: List of dumped Branches at target locationpath_string.

        """
        locationpath = parse(locationpath_string)

        result = []
        for branch in self._search(locationpath):
            parent = branch.parent
            result.append(parent._pop(branch.nodename).dump())

        return result

    def remove(self, locationpath_string):
        """Remove Branch.

        Args:
          locationpath_string(str): XPath format search string.

        Note:
          Don't delete self, only delete link from parent.

        """
        locationpath = parse(locationpath_string)

        for branch in self._search(locationpath):
            parent = branch.parent
            parent._remove(branch.nodename)

        return


class DictBranch(Branch):
    """Class for node data in json data tree.

    """
    def dump(self):
        return dict(
                [(k.branchkey, v.dump())
                    for k, v in self._branches.items()])

    def _generate_branches(self, data):
        result = {}

        for k, v in data.items():
            nodename = NodenameKey(k)
            result[nodename] = self._generate_branch(v, self)
        return result

    def _setdefault(self, nodename, data):
        if nodename in self.childnodenames:
            return None
        self._branches[nodename] = self._generate_branch(data, self)
        return self.locationpath + LocationStep(nodename)

    def __getitem__(self, item):
        nodename = NodenameKey(item)
        return self.childbranch(nodename).dump()


class ListBranch(Branch):
    """Class for List type branch.

    """
    def dump(self):
        result = [(int(k.branchkey), v.dump())
                  for k, v in self._branches.items()]
        return [x[1] for x in sorted(result, key=lambda x: x[0])]

    def _generate_branches(self, data):
        result = {}

        for i in range(0, len(data)):
            v = data[i]
            nodename = NodenameIndex(i)
            result[nodename] = self._generate_branch(v, self)
        return result

    def _insert(self, index, data):
        if index > len(self._branches):
            newindex = len(self._branches)
        else:
            newindex = index

        for i in range(len(self._branches), newindex, -1):
            fnode = NodenameIndex(i - 1)
            tnode = NodenameIndex(i)
            self._branches[tnode] = self._branches[fnode]
        nodename = NodenameIndex(newindex)
        self._branches[nodename] = self._generate_branch(data, self)

        return self.locationpath + LocationStep(nodename)

    def _append(self, data):
        nodename = NodenameIndex(len(self._branches))
        self._branches[nodename] = self._generate_branch(data, self)

        return self.locationpath + LocationStep(nodename)

    def __getitem__(self, item):
        nodename = NodenameIndex(item)
        return self.childbranch(nodename).dump()


class NullBranch(Branch):
    """Dummy branch for not existing branch.

    """
    def __init__(self, parent=None):
        super().__init__(None, parent)

    def dump(self):
        return None

    def _generate_branches(self, data):
        return {}

    def __bool__(self):
        return False


class Leaf(Branch):
    """Class for edge node in json data tree.

    Args:
      data(any json edge data): Edge data.
      parent(Branch): Parent branch of this leaf.

    Attributes:
      data(str or int or float or bool): Edge value.

    """
    def __init__(self, data, parent):
        super().__init__(data, parent)
        self.value = data

    def dump(self):
        return self.value

    def _generate_branches(self, data):
        return {}
