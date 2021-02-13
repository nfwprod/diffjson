class BranchDatatypeError(Exception):
    """Not json format data is inputted for Branch Init.

    """
    pass


class BranchRootLocationPathError(Exception):
    """Dedicated method is called for unexpected Class.

    """
    pass


class BranchDedicatedMethodError(Exception):
    """Dedicated method is called for unexpected Class.

    """
    pass


class BranchUnexpectedStructureError(Exception):
    """Broken branch structure.

    """


class DiffRootArgError(Exception):
    """Unexpected data for DiffBranch Init.

    """
    pass


class DiffCommoniInvalidFunctionError(Exception):
    """Unexpected data for DiffBranch Init.

    """
    pass


class DiffCommonArgError(Exception):
    """Unexpected data for DiffBranch Init.

    """
    pass


class DiffRootMaskmapDuplexError(Exception):
    """Mask has duplex outputs.

    """
    pass


class DiffRootBranchTypeError(Exception):
    """Compared Branch has unexpected Branch.

    """
    pass
