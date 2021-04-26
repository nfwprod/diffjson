import os
import csv
from .exceptions_diff import *
from .branch import *
from .pcounter import PCounterWrapper


# Functions
def diff_branches(listed_branches):
    """ Diff branches.

        Args:
          listed_branches(list): List of branches to compare.

        Returns:
          DiffRootBranch: Diff result.
    """

    return DiffRootBranch(listed_branches, nodenamemasks={})


def _diff(self, other):
    listed_branches = [other, self]
    return DiffRootBranch(listed_branches)


RootBranch.__sub__ = _diff


# Classes
class DiffBranchBase(BranchBase):
    """Template Class for DiffBranchBases.

    Args:
      listed_branches(list): Listed RootBranches to compare.

    Note:
      DiffBranchBase expand all input RootBranches to have same branches.

      DiffBranchBases are dict style multi dimensional branches.

      Use various dump and export methods to get various output data styles.

    """

    # Seal methods.
    def check_predicates(self, predicates):
        """Seal predicate search.

        Note:
          Raise exception when predicate is used in raw_search method.

        """
        if predicates:
            raise DiffBranchInvalidFunctionError()
        return super().check_predicates([])

    def _generate_childbranch(self, listed_branches, parent):
        if not parent:
            raise DiffBranchDatatypeError()
        if len(listed_branches) == 2:
            return DiffTwoBranch(listed_branches, parent)
        return DiffMultiBranch(listed_branches, parent)

    # Additional methods for DiffBranchBase.
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


class DiffRootBranch(DiffBranchBase):
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
    def __init__(self, listed_branches, nodenamemasks=None, reportmode=None):
        # Only report mode must be defined first for _report
        self.reportmode = reportmode

        # Input Check
        if not isinstance(listed_branches, list):
            raise DiffRootBranchArgError()
        for branch in listed_branches:
            if not isinstance(branch, RootBranch):
                raise DiffRootBranchArgError()

        if not (nodenamemasks is None or isinstance(nodenamemasks, dict)):
            raise DiffRootBranchArgError()

        if not nodenamemasks:
            nodenamemasks = {}

        # Mask branches
        (maskmap, masked_branches) = self._mask_branches(
                listed_branches, nodenamemasks)
        self.maskmap = maskmap

        # Contain data
        super().__init__(masked_branches, None)
        self._childbranches = self._generate_childbranches(masked_branches)
        self._listnum = len(listed_branches)
        self._listed_branches = listed_branches

    def is_root(self):
        return True

    def is_child(self):
        return False

    # Must be implemented
    def _is_self_unchanged(self):
        return True

    def _is_child_unchanged(self):
        for branch in self.childbranches:
            if not branch.is_unchanged():
                return False
        return True

    def _report(self, line):
        if self.reportmode == 'stdout':
            print(line)

    # Unique methods
    def _mask_branches(self, listed_branches, nodenamemasks):
        """ Convert nodename of target branch.

        Args:
          listed_branches(list): Listed RootBranch.

          nodenamemasks(dict, optional):
              Dict of locationpath_string and lambda.
              At target branch, replace nodenames for
              childbranches by lambda generated string.

        Returns:
          set: Set of Mask and Listed Masked Branches.
               Mask: {<locationpath_string>:
                        [<Original Nodename for Branch 01>, ...]}

        """
        # Mask duplex target check
        self._report('Mask duplex target check')
        self._check_nodenamemask(listed_branches, nodenamemasks)

        # Parse searchpath  of nodenamestr to boost
        self._report('Generate path and mask map')
        pathandmasks = self._generate_pathandmaskmap(
                listed_branches, nodenamemasks)

        # Mask
        total = len(listed_branches)
        self._report('Mask Listed Branches, total: {}'.format(total))
        (masklist, masked_branches) =\
                self._part_mask_branches(
                        listed_branches, pathandmasks)

        # Arrange Maskmap
        self._report('Arrange Maskmaps')
        maskmaps = self._arrange_maskmaps(masklist)
        return (maskmaps, masked_branches)

    # Internal methods for _mask_branches
    def _check_nodenamemask(self, listed_branches, nodenamemasks):
        def _check_nodenamemask_per_branch(branch, nodenamemasks):
            targets = []

            for searchpath_str, mask in nodenamemasks.items():
                searchpath = parse(searchpath_str)
                for searchedbranch in branch.raw_search(searchpath):
                    # Check same branch is targeted by other nodenamemasks
                    locationpath_string = str(searchedbranch.locationpath)
                    if locationpath_string in targets:
                        raise DiffRootBranchMaskmapDuplexError(
                                locationpath_string)
                    targets.append(locationpath_string)

                    # Check mask target is Dict Branch or List Branch
                    if not isinstance(searchedbranch,
                                      (DictBranch, ListBranch)):
                        raise DiffRootBranchTypeError(type(searchedbranch))

                    # Check duplex masked nodenames for other branches
                    maskedbnns = []
                    for childbranch in searchedbranch.childbranches:
                        maskedbnn = mask(childbranch)
                        if maskedbnn in maskedbnns:
                            raise DiffRootBranchMaskmapDuplexError(
                                    (maskedbnn, str(searchpath), childbranch))
                        maskedbnns.append(maskedbnn)
            return True

        for branch in listed_branches:
            _check_nodenamemask_per_branch(branch, nodenamemasks)
        return True

    def _generate_pathandmaskmap(self, listed_branches, nodenamemasks):
        pathandmasks = {}
        for searchpath_str, mask in nodenamemasks.items():
            searchpath = parse(searchpath_str)
            for branch in listed_branches:
                pathandmasks.update(
                        {x.locationpath: mask
                            for x in branch.raw_search(searchpath)})
        return pathandmasks

    def _part_mask_branches(self, listed_branches, pathandmasks):
        masklist = []
        masked_branches = []
        for branch in listed_branches:
            (maskmap, masked_branch) = self._mask_branch(branch, pathandmasks)
            masklist.append(maskmap)
            masked_branches.append(masked_branch)
        return (masklist, masked_branches)

    def _mask_branch(self, branch, pathandmasks):
        total = len(branch.search('//'))
        PCounterWrapper.init_pcounter(self, total,
                prefix='  ', reportmode=self.reportmode)
        (maskmap, newbranch) = self._recursive_copy(
                branch, self, pathandmasks)
        PCounterWrapper.del_pcounter(self)

        return (maskmap, newbranch)

    @PCounterWrapper('mask_branch', is_method=True)
    def _recursive_copy(self, currentbranch, parent, pathandmasks):
        def detect_mask(pathandmasks):
            mymask = None
            locationpath = currentbranch.locationpath
            for searchpath, mask in pathandmasks.items():
                if locationpath == searchpath:
                    mymask = mask
                    break
            return mymask

        def generate_newbranch(currentbranch, parent):
            if isinstance(currentbranch, RootBranch):
                newbranch = RootBranch(None)
            elif isinstance(currentbranch, DictBranch):
                newbranch = DictBranch({}, parent)
            elif isinstance(currentbranch, ListBranch):
                if mymask:
                    newbranch = DictBranch({}, parent)
                else:
                    newbranch = ListBranch([], parent)
            elif isinstance(currentbranch, Leaf):
                newbranch = Leaf(currentbranch.value, parent)
            elif isinstance(currentbranch, NullBranch):
                newbranch = NullBranch()
            else:
                raise DiffRootBranchTypeError(type(currentbranch))

            return newbranch

        # Find Mask for current path
        # RootBranch must be passed because it has no mask
        # and cause error for locationpath method.
        if isinstance(currentbranch, RootBranch):
            mymask = None
        else:
            mymask = detect_mask(pathandmasks)

        # Convert ListBranch to Dict Branch if masked
        newbranch = generate_newbranch(currentbranch, parent)

        # Contain Child Branches
        maskmap = {}
        for bnn in currentbranch.childnodenames:
            childbranch = currentbranch.childbranch(bnn)
            if mymask:
                masked_bnn = NodenameKey(str(mymask(childbranch)))
            else:
                masked_bnn = bnn

            maskmap[str(childbranch.locationpath)] = str(masked_bnn)
            (_maskmap, _childbranch) =\
                    self._recursive_copy(
                            childbranch, newbranch, pathandmasks)
            newbranch.raw_set(masked_bnn, _childbranch)
            maskmap.update(_maskmap)

        # Return copied branch
        return (maskmap, newbranch)

    def _arrange_maskmaps(self, masklist):
        maskmaps = {}
        all_maskedpath =\
                set([pname for mask in masklist for pname in mask.keys()])
        for pname in all_maskedpath:
            listed_bnn = []
            for maskmap in masklist:
                listed_bnn.append(maskmap.get(pname, None))
            maskmaps[pname] = listed_bnn

        return maskmaps

    def _generate_childbranches(self, listed_branches):
        """Generate child branches.

        Args:
          listed_branches(list): Child branches.

        Returns:
          dict: Dict of child listed branches.

        Note:
          Return DiffTwoBranch for 2 branch diff.
          Return DiffMultiBranch for long listed branches.

        """
        # Input Check
        for branch in listed_branches:
            if not isinstance(branch, RootBranch):
                raise DiffRootBranchArgError()

        listed_childbranches = []
        for branch in listed_branches:
            listed_childbranches.append(branch.childbranch(NodenameRoot()))

        childbranch = self._generate_childbranch(listed_childbranches, self)

        return {NodenameRoot(): childbranch}

    # Utility methods
    def search(self, locationpath_string, details=False, **kwargs):
        """Search target path with search nodepath string.

        Args:
          locationpath_string(str): XPath format search string.

          details(bool, option): Return searched path with value,
                         default: False(value only).

          dump_mode(str, option): DiffTwoBranch only.
            'all': Return all branch.
            'added': Return added branches, including it's children.
            'bulk_added': Return root of added branches.
            'removed': Return removed branches, including it's children.
            'bulk_removed': Return root of removed branches.
            'changed': Return changed branch only.
        Returns:
          dict or list: dict or list format JSON data.

        Node:
          This method must be implemented in RootBranch only.

        """
        result = []

        locationpath = parse(locationpath_string)
        for branch in self.raw_search(locationpath):
            data = branch.dump(**kwargs)
            if not data:
                continue
            result.append(
                    (str(branch.locationpath), data))

        result.sort(key=lambda x: x[0])
        if not details:
            result = [data for _, data in result]

        return result

    def dump_as_table(self, hide_unchanged=False):
        """Dump diff result as table format.

        Args:
          hide_unchanged(bool, optional): Stop to output unchanged branch,
            default False

        Returns:
          list

        """
        def _recursive_dump(currentbranch, hide_unchanged):
            result = currentbranch.dump_as_slice(hide_unchanged)
            for branch in currentbranch.childbranches:
                result.update(
                        _recursive_dump(branch, hide_unchanged))
            return result

        header = ['LocationPath'] +\
                 ['Data{}'.format(i) for i in range(0, self._listnum)]

        basebranch = self._childbranches[NodenameRoot()]
        data = _recursive_dump(basebranch, hide_unchanged)
        sorted_path = sorted(list(data.keys()))

        lines = []
        lines.append(header)
        for path in sorted_path:
            lines.append([path] + data[path])

        return lines

    def dump(self, **kwargs):
        """Dump diff data.

        Args:
          **kwargs: Dump args, passed to child branches.


        Returns:
          dict: List format diff result.
                {<path>: [<value of 1st branch>, <value of 2nd branch>, ,,]}

        Note:
          Cannot inherit dump from Branch to ignore disturbing
          hierarchical output.

        """
        return self._childbranches[NodenameRoot()].dump(**kwargs)

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
        except Exception as exception:
            raise exception

        lines = self.dump_as_table(hide_unchanged)
        if emphasis:
            for line in lines:
                for i in range(1, len(line) - 1):
                    if line[-i] == line[-i-1]:
                        line[-i] = '-'

        with open(fname, 'w') as fd:
            writer = csv.writer(fd)
            writer.writerows(lines)


class DiffChildBranch(DiffBranchBase):
    """Class for diff child branch.

    """
    def is_root(self):
        return False

    def is_child(self):
        return True


class DiffMultiBranch(DiffChildBranch):
    """Class for diff child branch for multi branch diff.

    Args:
      listed_branches(list): Branches to compare.
      parent(BranchBase): Parent of DiffMultiBranch

    Attributes:
      parent(BranchBase): Parent of DiffMultiBranch

    """
    def __init__(self, listed_branches, parent):
        super().__init__(listed_branches, parent)
        self._listnum = len(listed_branches)
        self._values = self._contain_values(listed_branches)
        self._branchtypes = self._contain_branchtypes(listed_branches)
        self._listed_branches = listed_branches

    # Must be implemented
    def _is_self_unchanged(self):
        if len(set(self._branchtypes)) == 1:
            if self._branchtypes[0] != Leaf:
                return True
            if len(set(self._values)) == 1:
                return True
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

    def _generate_childbranches(self, listed_branches):
        """Generate child branches.

        Args:
          listed_branches(list): Child branches.

        Returns:
          dict: Dict of child listed branches.

        """
        branches = {}

        # Get Union child_nodenames
        all_bnn = set([bnn for b in listed_branches
            for bnn in b.childnodenames])
        for bnn in all_bnn:
            listed_childbranches = []
            for branch in listed_branches:
                if isinstance(branch, (DictBranch, ListBranch)):
                    listed_childbranches.append(branch.childbranch(bnn))
                elif isinstance(branch, (NullBranch, Leaf)):
                    listed_childbranches.append(NullBranch())
                else:
                    raise DiffMultiBranchArgError()

            branches[bnn] =\
                    self._generate_childbranch(listed_childbranches, self)
        return branches

    # Utility methods
    def dump_as_slice(self, hide_unchanged=False):
        """Dump diff result of target branch.
        Not include children. Target branch only.

        Args:
          hide_unchanged(bool, optional): Stop to output unchanged branch,
            default False

        """
        if hide_unchanged and self.is_unchanged():
            return {}

        current_data = []
        for i in range(0, self._listnum):
            if self._branchtypes[i] == Leaf:
                current_data.append(self._values[i])
            else:
                current_data.append(self._branchtypes[i].__name__)
        return {str(self.locationpath): current_data}

    def dump_as_structure(self, hide_unchanged=False):
        """Dump branch data at this branch.

        Args:
          hide_unchanged(bool, optional): Stop to output unchanged branch,
            default False

        Returns:
          list: List of dumped data for each diffed branch.

        """
        if hide_unchanged and self.is_unchanged():
            return []

        return [branch.dump() for branch in self._listed_branches]

    def dump(self, hide_unchanged=False):
        """Dump diff data.

        Note:
          For this version, dump is dump_as_structure.
          This might be reviewed.

        """
        return self.dump_as_structure(hide_unchanged=hide_unchanged)


class DiffTwoBranch(DiffMultiBranch):
    """Class for diff two branches.
    This class has some extra method only for 2 branch diff.

    Args:
      listed_branches(list): Branches to compare.
      parent(BranchBase): Parent of DiffMultiBranch

    Attributes:
      parent(BranchBase): Parent of DiffMultiBranch

    """
    # Override Methods
    def __init__(self, listed_branches, parent):
        if len(listed_branches) != 2:
            raise DiffTwoBranchArgError('Diff target branches must be 2.')

        self._listed_branches = listed_branches
        super().__init__(listed_branches, parent)

    # Utility methods
    def is_added(self):
        """Check this branch is added or not.

        Returns:
          bool

        """
        if self._branchtypes[0] == NullBranch and \
                self._branchtypes[1] != NullBranch:
            return True
        return False

    def is_bulk_added(self):
        """Check this branch is root of added branch or not.

        Returns:
          bool

        Note:
          If parent branch is added branch, this branch is not root.
          But if parent is DiffRootBranch, this branch is added root.

        """
        if self.is_added():
            if isinstance(self.parent, DiffRootBranch) or\
               not self.parent.is_added():
                return True
        return False

    def is_removed(self):
        """Check this branch and children are removed or not.

        Returns:
          bool

        """
        if self._branchtypes[0] != NullBranch and \
                self._branchtypes[1] == NullBranch:
            return True
        return False

    def is_bulk_removed(self):
        """Check this branch is root of removed branch or not.

        Returns:
          bool

        Note:
          If parent branch is removed branch, this branch is not root.
          But if parent is DiffRootBranch, this branch is removed root.

        """
        if self.is_removed():
            if isinstance(self.parent, DiffRootBranch) or\
               not self.parent.is_removed():
                return True
        return False

    def is_changed(self):
        """Check this branch and children are changed or not.

        Returns:
          bool

        Note:
          This method is only for purely changed branch.
          No need for bulk because children of changed branch are
          added or deleted.

        """
        if self._branchtypes[0] != self._branchtypes[1]:
            if (self._branchtypes[0] != NullBranch) and\
               (self._branchtypes[1] != NullBranch):
                return True
        elif self._branchtypes[0] == Leaf:
            if self._values[0] != self._values[1]:
                return True
        return False

    def _dump_check(self, dump_mode):
        valid_dump_modes = ['added', 'bulk_added', 'removed', 'bulk_removed',
                        'changed', 'all']
        if dump_mode not in valid_dump_modes:
            raise DiffTwoBranchArgError(
                    'dump_mode must be in {}'.format(valid_dump_modes))

        if dump_mode == 'added' and self.is_added():
            return True
        if dump_mode == 'bulk_added' and self.is_bulk_added():
            return True
        if dump_mode == 'removed' and self.is_removed():
            return True
        if dump_mode == 'bulk_removed' and self.is_bulk_removed():
            return True
        if dump_mode == 'changed' and self.is_changed():
            return True
        if dump_mode == 'all':
            return True
        return False

    def dump_as_slice(self, hide_unchanged=False, dump_mode='all'):
        """Dump diff result of target branch.
        Not include children. Target branch only.

        Args:
          hide_unchanged(bool): Stop to output unchanged branch.

          dump_mode(str): Select dump target.
            If hide_unchanged=True, ignored.
            'all': Dump all branch.
            'added': Dump added branch. Include added root and children.
            'bulk_added': Dump added root branch, ignore children of them.
            'removed': Dump removed branch. Include added root and children.
            'bulk_removed': Dump removed root branch, ignore children of them.
            'changed': Dump changed branch only.

        """
        if self._dump_check(dump_mode):
            return super().dump_as_slice(hide_unchanged)
        return None

    def dump_as_structure(self, hide_unchanged=False, dump_mode='all'):
        """Dump branch data at this branch.

        Args:
          hide_unchanged(bool): Stop to output unchanged branch.

          dump_mode(str): Select dump target.
            If hide_unchanged=True, ignored.
            'all': Dump all branch.
            'added': Dump added branch. Include added root and children.
            'bulk_added': Dump added root branch, ignore children of them.
            'removed': Dump removed branch. Include added root and children.
            'bulk_removed': Dump removed root branch, ignore children of them.
            'changed': Dump changed branch only.

        """
        if self._dump_check(dump_mode):
            return super().dump_as_structure(hide_unchanged)
        return None

    def dump(self, hide_unchanged=False, dump_mode='all'):
        """Dump diff data.

        Note:
          For this version, dump is dump_as_structure.
          This might be reviewed.

        """
        return self.dump_as_structure(
                hide_unchanged=hide_unchanged, dump_mode=dump_mode)
