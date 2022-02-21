import os
import re
import tempfile

from plumbum import local

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.enums import ENUM_ST_INFO_TYPE

from functools import lru_cache


def camel_to_snake_case(s):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()


def create_tempfile(contents, mode="w", **kwargs):
    f = tempfile.NamedTemporaryFile(mode=mode, **kwargs)
    f.write(contents)
    f.flush()
    return f


def create_file(path, contents, mode="w", **kwargs):
    f = open(path, mode=mode, **kwargs)
    f.write(contents)
    f.flush()
    return f


#TODO(mrkastep): fix lines like "void f(int /*param*/) { // other comment"
def get_c_without_comments(f):
    lines = f.readlines()

    res = []
    in_comment = False

    for l in lines:
        l = l.strip()
        if not in_comment:
            line_comment = l.find("//")
            if line_comment != -1:
                res.append(l[:line_comment])
                continue

        cur = ""
        while True:
            if not in_comment:
                tag = l.find("/*")
                if tag != -1:
                    in_comment = True
                    cur = cur + l[:tag]
                    l = l[tag + 2:]
                    continue
                cur = cur + l
                break
            else:
                tag = l.find("*/")
                if tag != -1:
                    in_comment = False
                    l = l[tag + 2:]
                    continue
                break
        res.append(cur)

    return "\n".join(res)


def get_object_file_name(source_name):
    return re.sub("\.[^\.]*$", ".o", source_name)


@lru_cache(maxsize=10)
def get_symbols(source_path):
    assert source_path.name.endswith(".c")

    gcc = local["gcc"]

    obj_path = get_object_file_name(source_path)

    messages = []

    try:
        gcc("-o", obj_path, "-c", source_path)
    except:
        raise RuntimeError(f"{source_path.name}: compilation failed")

    with open(obj_path, "rb") as f:
        elf = ELFFile(f)

        symtab = elf.get_section_by_name(".symtab")

        if not symtab:
            raise RuntimeError(f"{source_path.name}: .symtab not found")

        num_symbols = symtab.num_symbols()

        symbols = {}

        for i in range(num_symbols):
            symbol = symtab.get_symbol(i)
            symbol_type = symbol["st_info"]["type"]
            if symbol_type == "STT_FUNC":
                symbols[symbol.name] = {"bind": symbol["st_info"]["bind"]}

    os.remove(obj_path)
    return symbols
