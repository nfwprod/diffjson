class PCounter():
    """Progress Counter.

    Args:
      total(int): Total of counted functions.

      prefix(str, option): Add this prefix when print progress, default:''.

      reportmode(str, option): Mode for progress output, default None.
        'stdout': stdout

    """
    def __init__(self, total, prefix='', reportmode=None):
        self.total = total
        self.prefix = prefix
        self.reportmode = reportmode
        self.count = 0

    def step(self):
        """Report progress.

        """
        if self.reportmode == 'stdout':
            if self.total:
                print('\r{}{}/{}'.format(
                    self.prefix, self.count, self.total), end='')
            else:
                print('\r{}{}/??'.format(
                    self.prefix, self.count), end='')
        self.count += 1

    def end(self):
        """End counter.

        """
        if self.reportmode == 'stdout':
            print('')
        self.count = 0


class PCounterWrapper():
    """Progress Counter.

    Args:
      countername(str): Countername, used for non method decorator.
      is_method(bool, option): Decorating method or function, default False.

    Note:
      For method, use 'self' for proccess counter identifier.
      For function, use 'countername' for identifier.

    """

    pcounters = {}

    def __init__(self, countername, is_method=False):
        if countername in PCounterWrapper.pcounters.keys():
            raise Exception(
                    "PCounter countername duplex, {}.".format(countername))
        self.countername = countername
        self.is_method = is_method

    def __call__(self, func):
        def decorated_func(*args, **kwargs):
            result = func(*args, **kwargs)

            if self.is_method:
                countername = id(args[0])
            else:
                countername = self.countername
            if countername not in PCounterWrapper.pcounters.keys():
                raise Exception("Init pcounter")

            PCounterWrapper.pcounters[countername].step()
            return result

        return decorated_func

    @classmethod
    def init_pcounter(cls, countername, total, prefix='', reportmode=None):
        """Init process counter.

        Args:
          countername(str): Countername, used for non method decorator.

          total(int): Total of counted functions.

          prefix(str, option): Add this prefix when print progress, default:''.

          reportmode(str, option): Mode for progress output, default None.
            'stdout': stdout

        """
        if not isinstance(countername, str):
            countername = id(countername)
        if countername in cls.pcounters.keys():
            raise Exception("Pcounter {} already exists.".format(countername))

        cls.pcounters[countername] =\
                PCounter(total, prefix=prefix, reportmode=reportmode)

    @classmethod
    def del_pcounter(cls, countername):
        """Delete process counter.

        Args:
          countername(str): Countername, used for non method decorator.

        """
        if not isinstance(countername, str):
            countername = id(countername)
        if countername not in cls.pcounters.keys():
            raise Exception("Pcounter {} not exists.".format(countername))

        cls.pcounters[countername].end()
        del cls.pcounters[countername]
