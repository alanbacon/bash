import re
import sys
from subprocess import PIPE, Popen
SUBPROCESS_HAS_TIMEOUT = True
if sys.version_info < (3, 0):
    try:
        from subprocess32 import PIPE, Popen  #NOQA
    except ImportError:
        # You haven't got subprocess32 installed. If you're running 2.X this
        # will mean you don't have access to things like timeout
        SUBPROCESS_HAS_TIMEOUT = False

SPLIT_NEWLINE_REGEX = re.compile(' *\n *')


class bash(object):
    "This is lower class because it is intended to be used as a method."

    def __init__(self, *args, **kwargs):
        self.p = None
        self.stdout = None
        self.bash(*args, **kwargs)

    def bash(self, *cmds, env=None, stdout=PIPE, stderr=PIPE, timeout=None, sync=True):
        cmd = bash.unpackCommands(cmds)
        self.p = Popen(
            cmd, shell=True, stdout=stdout, stdin=PIPE, stderr=stderr, env=env
        )
        if sync:
            self.sync(timeout)
        return self

    def sync(self, timeout=None):
        kwargs = {'input': self.stdout}
        if timeout:
            kwargs['timeout'] = timeout
            if not SUBPROCESS_HAS_TIMEOUT:
                raise ValueError(
                    "Timeout given but subprocess doesn't support it. "
                    "Install subprocess32 and try again."
                )
        self.stdout, self.stderr = self.p.communicate(**kwargs)
        self.code = self.p.returncode
        return self

    def __repr__(self):
        return self.value()

    def __unicode__(self):
        return self.value()

    def __str__(self):
        return self.value()

    def __nonzero__(self):
        return self.__bool__()

    def __bool__(self):
        return bool(self.value())

    def __iter__(self):
        return self.results().__iter__()

    def value(self):
        if self.stdout:
            return self.stdout.strip().decode(encoding='UTF-8')
        return ''

    def results(self):
        output = self.stdout.decode(encoding='UTF-8').strip() or ''
        if output:
            return SPLIT_NEWLINE_REGEX.split(output)
        else:
            return []

    @staticmethod
    def areArgs(cmds):
        return len(cmds) > 0

    @staticmethod
    def areMultipleArgs(cmds):
        return len(cmds) > 1

    @staticmethod
    def commandChecker(cmds):
        raisedError = None
        try:
            if not bash.areArgs(cmds):
                raise SyntaxError('no arguments')

            masterCommand = cmds[0]
            if not isinstance(masterCommand, str):
                raise SyntaxError('first argument to bash must be a command as a string')

            if bash.areMultipleArgs(cmds):
                arguments = cmds[1]
                if not isinstance(arguments, list):
                    raise SyntaxError('second argument to bash (if specified) must be a list of strings')
                areStrings = list(map(lambda el : isinstance(el, str), arguments))
                nonStrings = list(filter(lambda isString : not isString, areStrings))
                if len(nonStrings):
                    raise SyntaxError('one or more command arguments were not strings')

            if len(cmds) > 2:
                raise SyntaxError('more than two bash arguments given')

        except SyntaxError as e:
            raisedError = e

        finally:
            if isinstance(raisedError, Exception):
                raise SyntaxError(
                    str(raisedError) + '\n'
                    'bash and xargs will accept one or two arguments: [command <str>, arguments <list of strings>]'
                )

    @staticmethod
    def unpackCommands(cmds):
        bash.commandChecker(cmds)
        masterCommand = cmds[0]
        arguments = cmds[1] if bash.areMultipleArgs(cmds) else []
        seperator = ' '
        argumentsString = seperator.join(arguments)
        return masterCommand + ' ' + argumentsString
