import re
import tempfile

from plumbum import local

def camel_to_snake_case(s):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()


def create_tempfile(contents, mode="w", **kwargs):
    f = tempfile.NamedTemporaryFile(mode=mode, **kwargs)
    f.write(contents)
    f.flush()
    return f


def get_c_without_comments(path):
    gcc = local["gcc"]
    cleaner = gcc["-fpreprocessed", "-dD", "-E"]

    return "\n".join(cleaner(path).split("\n")[1:])
