from os.path import dirname, basename, isfile, join
import glob
from importlib import import_module

# Import all reviewer modules
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]


for module_name in __all__:
    import_module("." + module_name, package=__name__)

