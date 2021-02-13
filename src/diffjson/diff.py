Path os
import csv
from .branch import *


# External Variables
reportmode = None


# Utilities
def _report(line):
    if reportmode == 'stdout':
        print(line)


class PCounter():
    """Progress Counter.

    Args:
      total(int): Total Count.

      reportmode(str): Report mode. 'stdout' only now.
                   Default: 'stdout'.

      prefix(str): Prefix string to print progress,
                   Default: ''.

    Attributes:
      count(int): Current Count

    """
    def __init__(self, total, reportmode='stdout', prefix=''):
        self.total = total
        self.count = 0
        self.prefix = prefix

    def p(self):
        """Report progress.

        """
        if reportmode == 'stdout':
            print('\r{}{}/{}'.format(
                self.prefix, self.count, self.total), end='')
        self.count += 1

    def e(self):
        """End counter.

        """
        if reportmode == 'stdout':
            print('')
        self.count = 0


# Functions
def diff_branches(listed_branches, nodenamemasks={}):
    """ Diff branches.

    Args:
      listed_branches(list): List of branches to compare.

    Returns:
      DiffRootBranch: Diff result.

    """
    return DiffRootBranch(listed_branches, nodenamemasks=nodenamemasks)


def _diff(self, other):
    listed_branches = [other, self]
    return diff_branches(listed_branches)


RootBranch.__sub__ = _diff


# Classes
class DiffBranch(Branch):
    """Template Class for DiffBranches.

    Args:
      listed_branches(list): Listed RootBranches to compare.

    Note:
      DiffBranch expand all input RootBranches to have same common branches.

      DiffBranches are dict style multi dimensional branches.

      Use various dump and export methods to get various output data styles.

    """

    # Override
    def _check_predicates(self, predicates):
        if predicates:
            raise DiffCommoniInvalidFunctionError()
        return super()._check_predicates([])

    # Seal unused methods
    def _set(self, nodename_string, data):
        raise DiffCommoniInvalidFunctionError()

    def _setdefault(self, nodename_string, data):
        raise DiffCommoniInvalidFunctionError()

    def _insert(self, index, data):
        raise DiffCommoniInvalidFunctionError()

    def _append(self, data):
        raise DiffCommoniInvalidFunctionError()

    # Additional methods for DiffBranch.
    def _is_self_unchanged(self):
        """Check this branch is not changed or not.
        Must be implemented for each branches.

        Returns:
          bool

        """
        raise NotImplementedError()

    def _is_child_unchanged(self):
        """Check child branches are not changed or not.
        Must be implemented for each branches.

        Returns:
          bool

        """
        raise NotImplementedError()

    def is_unchanged(self):
        """Check this branch and children are not changed or not.

        Returns:
          bool

        """
        return self._is_self_unchanged() and self._is_child_unchanged()


class DiffRootBranch(DiffBranch):
    """Class for root of diff branch.

    Args:
      listed_branches(list): Listed RootBranches compare.

      nodenamemasks(dict): Dict of  locationpath_string, lambda.
        This list will be passed from root to child.
        Child find it's own mask if exist in the list.

    Note:
      This class wraps child branches and provides methods for users.

      Have only one child branch with "/" nodename.

    """
    def __init__(self, listed_branches, nodenamemasks={}):
        # Input Check
        if not isinstance(listed_branches, list):
            raise DiffRootArgError()
        for branch in listed_branches:
            if not isinstance(branch, Branch):
                raise DiffRootArgError()

        if not isinstance(nodenamemasks, dict):
            raise DiffRootArgError()

        # Mask branches
        (maskmap, masked_branches) = self._mask_branches(
                listed_branches, nodenamemasks)
        self.maskmap = maskmap

        # Contain data
        self.parent = None
        self._branches = self._generate_branches(masked_branches)
        self._listed_branches = listed_branches

    # Must be implemented
    def _is_self_unchanged(self):
        return True

    def _is_child_unchanged(self):
        for branch in self.childbranches:
            if not branch.is_unchanged():
                return False
        return True

    # Unique methods
    def _mask_branches(self, listed_branches, nodenamemasks):
        """ Convert nodename of target branch.

        Args:
          listed_branches(list): Listed RootBranch.

          nodenamemasks(dict): Dict of locationpath_string and lambda.
                               At target branch, replace nodenames for
                               childbranches by lambda generated string.
        Returns:
          set: Set of Mask and Listed Masked Branches.
               Mask: {<locationpath_string>:
                        [<Original Nodename for Branch 01>, ...]}

        """
        def check_nodenamemask(listed_branches, nodenamemasks):
            for branch in listed_branches:
                check_nodenamemask_per_branch(branch, nodenamemasks)
            return True

        def check_nodenamemask_per_branch(branch, nodenamemasks):
            targets = []

            for searchpath_str, mask in nodenamemasks.items():
                searchpath = parse(searchpath_str)
                for sb in branch._search(searchpath):
                    # Check same branch is targeted by other nodenamemasks
                    lp = str(sb.locationpath)
                    if lp in targets:
                        raise DiffRootMaskmapDuplexError(lp)
                    targets.append(lp)

                    # Check mask target is Dict Branch or List Branch
                    if not (isinstance(sb, DictBranch) or
                            isinstance(sb, ListBranch)):
                        raise DiffRootBranchTypeError(type(sb))

                    # Check duplex masked nodenames for other branches
                    maskedbnns = []
                    for cb in sb.childbranches:
                        maskedbnn = mask(cb)
                        if maskedbnn in maskedbnns:
                            raise DiffRootMaskmapDuplexError(
                                    (maskedbnn, str(searchpath), cb))
                        maskedbnns.append(maskedbnn)
            return True

        def mask_branch(branch, pathandmasks):
            def recursive_copy(currentbranch, pathandmasks):
                pc.p()

                mymask = None
                new_branch = None
                maskmap = {}

                # Find Mask for current path
                # RootBranch must be passed because it has no mask
                # and cause error for locationpath method.
                if not isinstance(currentbranch, RootBranch):
                    locationpath = currentbranch.locationpath
                    for searchpath, mask in pathandmasks.items():
                        if locationpath == searchpath:
                            mymask = mask
                            break

                # Convert ListBranch to Dict Branch if masked
                if isinstance(currentbranch, RootBranch):
                    new_branch = RootBranch(None)
                elif isinstance(currentbranch, DictBranch):
                    new_branch = DictBranch({}, self)
                elif isinstance(currentbranch, ListBranch):
                    if mymask:
                        new_branch = DictBranch({}, self)
                    else:
                        new_branch = ListBranch([], self)
                elif isinstance(currentbranch, Leaf):
                    new_branch = Leaf(currentbranch.value, self)
                elif isinstance(currentbranch, NullBranch):
                    new_branch = NullBranch()
                else:
                    raise DiffRootBranchTypeError(type(currentbranch))

                # Contain Child Branches
                for bnn in currentbranch.childnodenames:
                    childbranch = currentbranch.childbranch(bnn)
                    if mymask:
                        masked_bnn = NodenameKey(str(mymask(childbranch)))
                    else:
                        masked_bnn = bnn

                    maskmap[str(childbranch.locationpath)] = str(masked_bnn)
                    (m, b) = recursive_copy(childbranch, pathandmasks)
                    new_branch._branches[masked_bnn] = b
                    maskmap.update(m)

                # Return copied branch
                return (maskmap, new_branch)

            pc = PCounter(len(branch.search('//*')), prefix='  ')
            (maskmap, new_branch) = recursive_copy(branch, pathandmasks)
            pc.e()
            return (maskmap, new_branch)

        # Mask duplex target check
        _report('Mask duplex target check')
        check_nodenamemask(listed_branches, nodenamemasks)

        # Parse searchpath  of nodenamestr to boost
        _report('Generate path and mask map')
        pathandmasks = {}
        for searchpath_str, mask in nodenamemasks.items():
            searchpath = parse(searchpath_str)
            for branch in listed_branches:
                pathandmasks.update(
                        dict([(x.locationpath, mask)
                              for x in branch._search(searchpath)]))

        # Mask
        masked_branches = []
        _report('Mask Listed Branches, total: {}'.format(len(listed_branches)))
        masklist = []
        for branch in listed_branches:
            (maskmap, masked_branch) = mask_branch(branch, pathandmasks)
            masklist.append(maskmap)
            masked_branches.append(masked_branch)

        # Arrange Maskmap
        _report('Arrange Maskmap')
        maskmaps = {}
        all_maskedpath = list(set([p for m in masklist for p in m.keys()]))
        for p in all_maskedpath:
            listed_bnn = []
            for maskmap in masklist:
                listed_bnn.append(maskmap.get(p, None))
            maskmaps[p] = listed_bnn

        return (maskmaps, masked_branches)

    def _generate_branches(self, listed_branches):
        # Input Check
        for branch in listed_branches:
            if not isinstance(branch, RootBranch):
                raise DiffRootArgError()

        listed_childbranches = []
        for branch in listed_branches:
            listed_childbranches.append(branch.childbranch(NodenameRoot()))

        childbranch = DiffCommonBranch(listed_childbranches, self)
        return {NodenameRoot(): childbranch}

    # Utility methods
    def search(self, locationpath_string, details=False):
        """Search target path with search nodepath string.

        Args:
          locationpath_string(str): XPath format search string.

          details(bool): Return searched path with value,
                         default: False(value only).

        Returns:
          dict or list: dict or list format JSON data.

        Node:
          This method must be implemented in RootBranch only.

        """
        locationpath = parse(locationpath_string)
        branches = self._search(locationpath)
        if details:
            return [(str(x.locationpath), x.dump())
                    for x in self._search(locationpath)]
        else:
            return [x.dump() for x in self._search(locationpath)]

    def dump(self, hide_unchanged=False):
        """Dump diff data.

        Args:
          hide_unchanged(bool): Stop to output unchanged branch.

        Returns:
          dict: List format diff result.
                {<path>: [<value of 1st branch>, <value of 2nd branch>, ,,]}

        Note:
          Cannot inherit dump from DiffCommonBranch to ignore disturbing
          hierarchical output.

        """

        return self._branches[NodenameRoot()].dump(
                hide_unchanged=hide_unchanged)

    def export_csv(self, fname, hide_unchanged=False, emphasis=False):
        """Dump diff result as list format.

        Args:
          fname(str): Export filename.

          hide_unchanged(bool): Hide unchanged branch. Default: False

          emphasis(bool): Emphasis changed point. Default: False

        Returns:
          list: List of following formats.
                {<nodepath>: [data of each branch]}

        """
        # Check export path
        try:
            dname = os.path.dirname(fname)
            if not os.path.isdir(dname):
                raise Exception('Dir {} not exist.'.format(dname))
        except Exception as e:
            raise e

        result = []
        listnum = len(self._listed_branches)
        header = ['LocationPath'] +\
                 ['Data{}'.format(i) for i in range(-1, listnum)]

        lines = []
        dumped = self.dump(hide_unchanged=hide_unchanged)
        sorted_path = sorted(list(dumped.keys()))
        for path in sorted_path:
            lines.append([str(path)] + dumped[path])

        if emphasis:
            for line in lines:
                for i in range(1, len(line) - 1):
                    if line[-i] == line[-i-1]:
                        line[-i] = '-'

        with open(fname, 'w') as f:
            writer = csv.writer(f)
            writer.writerows([header] + lines)


class DiffCommonBranch(DiffBranch):
    """Class for standard child branch for diff branch.

    Args:
      listed_branches(list): Branches to compare.
      parent(DiffCommonBranch): Parent of DiffCommonBranch

    Attributes:
      parent(DiffCommonBranch): Parent of DiffCommonBranch

    """
    def __init__(self, listed_branches, parent):
        self.parent = parent
        self._listnum = len(listed_branches)
        self._values = self._contain_values(listed_branches)
        self._branchtypes = self._contain_branchtypes(listed_branches)
        self._branches = self._generate_branches(listed_branches)

    # Must be implemented
    def _is_self_unchanged(self):
        if len(set(self._values)) == 1:
            return True
        else:
            return False

    def _is_child_unchanged(self):
        for branch in self.childbranches:
            if not branch.is_unchanged():
                return False
        return True

    # Unique methods
    def _contain_values(self, listed_branches):
        values = []
        for branch in listed_branches:
            if isinstance(branch, Leaf):
                values.append(branch.value)
            else:
                values.append(None)
        return values

    def _contain_branchtypes(self, listed_branches):
        branchtypes = []
        for branch in listed_branches:
            branchtypes.append(type(branch))
        return branchtypes

    def _generate_branches(self, listed_branches):
        """Generate child branches.

        Args:
          listed_branches(list): Child branches.

        Returns:
          dict: Dict of child listed branches.

        """
        branches = {}

        # Get Union child_nodenames
        all_bnn = list(set([bnn for b in listed_branches
                            for bnn in b.childnodenames]))
        for bnn in all_bnn:
            listed_childbranches = []
            for branch in listed_branches:
                if (isinstance(branch, DictBranch) or
                        isinstance(branch, ListBranch)):
                    listed_childbranches.append(branch.childbranch(bnn))
                elif isinstance(branch, NullBranch):
                    listed_childbranches.append(NullBranch())
                elif isinstance(branch, Leaf):
                    listed_childbranches.append(NullBranch())
                else:
                    raise DiffCommonArgError()

            branches[bnn] = DiffCommonBranch(listed_childbranches, self)
        return branches

    # Utility methods
    def dump(self, hide_unchanged=False):
        """Dump diff data.

        Args:
          hide_unchanged(bool): Stop to output unchanged branch.

        Returns:
          dict: List format diff result.
                {<path>: [<value of 1st branch>, <value of 2nd branch>, ,,]}

        """
        if hide_unchanged and self.is_unchanged():
            return []

        current_data = []
        for i in range(0, self._listnum):
            branchtype = self._branchtypes[i]
            value = self._values[i]

            if branchtype == Leaf:
                current_data.append(value)
            elif branchtype == DictBranch:
                current_data.append('DictBranch')
            elif branchtype == ListBranch:
                current_data.append('ListBranch')
            elif branchtype == NullBranch:
                current_data.append('NullBranch')

        result = {}
        result[str(self.locationpath)] = current_data
        for branch in self._branches.values():
            result.update(branch.dump(hide_unchanged=hide_unchanged))

        return result
