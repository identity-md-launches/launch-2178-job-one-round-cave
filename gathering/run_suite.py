"""Run unittest with temporary directories confined to task scratch."""
from pathlib import Path
import runpy
import sys
import tempfile

scratch = Path('test/scratch').resolve()
scratch.mkdir(parents=True, exist_ok=True)
original = tempfile.TemporaryDirectory

def local_temporary_directory(*args, **kwargs):
    if kwargs.get('dir') in (None, '/tmp'):
        kwargs['dir'] = str(scratch)
    return original(*args, **kwargs)

tempfile.TemporaryDirectory = local_temporary_directory
sys.argv = ['unittest', *sys.argv[1:]]
runpy.run_module('unittest', run_name='__main__')
