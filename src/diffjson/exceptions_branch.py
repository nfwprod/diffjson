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
    pass

class BranchUnexpectedArgumentError(Exception):
    """Unexpected Arggument.

    """
    pass
