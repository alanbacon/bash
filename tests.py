from datetime import datetime
import unittest

try:
    from subprocess import TimeoutExpired
except ImportError:
    try:
        from subprocess32 import TimeoutExpired
    except ImportError:
        pass

import bash as bash_module
from bash import bash


class TestBash(unittest.TestCase):

    def test_bash_concatenation_by_method(self):
        result = bash('ls .').bash('grep "tests.py$"').value()
        self.assertEqual(result, 'tests.py')

    def test_bash_concatenation_within_command(self):
        result = bash('ls . | grep "tests.py$"').value()
        self.assertEqual(result, 'tests.py')

    def test_bash_repr(self):
        result = bash('ls . | grep "tests.py$"')
        self.assertEqual(repr(result), 'tests.py')

    def test_bash_stdout(self):
        result = bash('ls . | grep "tests.py$"')
        self.assertEqual(result.stdout, b'tests.py\n')
        self.assertEqual(result.code, 0)

    def test_bash_stderr(self):
        result = bash('./missing_command')
        self.assertEqual(result.stdout, b'')
        self.assertTrue(result.stderr in [
            # Mac OSX
            b'/bin/sh: ./missing_command: No such file or directory\n',
            # Travis
            b'/bin/sh: 1: ./missing_command: not found\n'
        ])
        self.assertEqual(result.code, 127)

    def test_passing_env(self):
        result = bash('echo $NAME', env={'NAME': 'Fred'})
        self.assertEqual(result.stdout, b'Fred\n')

    def test_output_to_stdout(self):
        b = bash('ls .', stdout=None)
        self.assertEqual(str(b), '')
        # Shouldn't find anything because we haven't piped it.
        self.assertEqual(str(b.bash('grep setup')), '')

    def test_timeout_works(self):
        if not bash_module.SUBPROCESS_HAS_TIMEOUT:
            raise unittest.SkipTest()
        self.assertRaises(TimeoutExpired, bash, 'sleep 2; echo 1', timeout=1)

    def test_sync_false_does_not_wait(self):
        t1 = datetime.now()
        b = bash('sleep 0.5; echo 1', sync=False)
        t2 = datetime.now()

        self.assertTrue((t2-t1).total_seconds() < 0.5)
        b.sync()
        self.assertEqual(b.stdout, b'1\n')

    def test_iterate_over_results(self):
        expecting = ['setup.py', 'tests.py']
        b = bash('ls . | grep "\.py"')
        results = b.results()
        self.assertEqual(results, expecting)

        iteratedResults = [result for result in b]
        self.assertEqual(iteratedResults, expecting)

    def test_accept_args_list(self):
        expecting = ['setup.py', 'tests.py']
        b = bash('ls').bash('grep', ['-e', '"\.py"'])
        results = b.results()
        self.assertEqual(results, expecting)

    def test_syntax_error_no_args(self):
        with self.assertRaises(SyntaxError) as e:
            bash()

        self.assertEqual(
            str(e.exception),
            'no arguments\n' + 
            'bash and xargs will accept one or two arguments: [command <str>, arguments <list of strings>]'
        )

    def test_syntax_error_not_string_arg(self):
        with self.assertRaises(SyntaxError) as e:
            bash(1)

        self.assertEqual(
            str(e.exception),
            'first argument to bash must be a command as a string\n' + 
            'bash and xargs will accept one or two arguments: [command <str>, arguments <list of strings>]'
        )

    def test_syntax_error_second_arg_not_list(self):
        with self.assertRaises(SyntaxError) as e:
            bash('a', 'b')

        self.assertEqual(
            str(e.exception),
            'second argument to bash (if specified) must be a list of strings\n' + 
            'bash and xargs will accept one or two arguments: [command <str>, arguments <list of strings>]'
        )

    def test_syntax_error_second_arg_not_list_of_strings(self):
        with self.assertRaises(SyntaxError) as e:
            bash('a', [1])

        self.assertEqual(
            str(e.exception),
            'one or more command arguments were not strings\n' + 
            'bash and xargs will accept one or two arguments: [command <str>, arguments <list of strings>]'
        )

    def test_syntax_error_second_arg_not_list_of_strings(self):
        with self.assertRaises(SyntaxError) as e:
            bash('a', ['b'], 'c')

        self.assertEqual(
            str(e.exception),
            'more than two bash arguments given\n' + 
            'bash and xargs will accept one or two arguments: [command <str>, arguments <list of strings>]'
        )

    def test_xargs(self):
        expecting = 'setup.py:    author=\'Alex Couper\','
        result = bash('ls').bash('grep', ['-e', '"\.py"']).xargs('grep', ['"author=\'Alex Couper\'"']).value()
        self.assertEqual(result, expecting)

