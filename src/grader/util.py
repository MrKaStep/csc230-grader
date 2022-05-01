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
    return source_name.__class__(re.sub("\.[^\.]*$", ".o", source_name))


def get_object_path(source_path, machine=None, session=None):
    assert source_path.name.endswith(".c")
    assert machine is None and session is None or machine is not None and session is not None

    obj_path = get_object_file_name(source_path)

    messages = []

    try:
        if machine is None:
            gcc = local["gcc"]
            gcc("-o", obj_path, "-c", source_path)
        else:
            with machine.tempdir() as tempdir:
                rem_source_path = tempdir / "src.c"
                rem_obj_path = tempdir / "src.o"
                copy(source_path, rem_source_path)
                session.run(f"cd {tempdir}")
                session.run("gcc -o src.o -c src.c")
                copy(rem_obj_path, obj_path)
    except:
        raise RuntimeError(f"{source_path.name}: compilation failed")

    return obj_path


@lru_cache(maxsize=10)
def get_symbols(source_path, machine=None, session=None):
    obj_path = get_object_path(source_path, machine, session)
    with open(obj_path, "rb") as f:
        elf = ELFFile(f)
        
        symtab = elf.get_section_by_name(".symtab")

        if not symtab:
            raise RuntimeError(f"{source_path.name}: .symtab not found")

        symbols = {}

        for symbol in symtab.iter_symbols():
            symbols[symbol.name] = symbol["st_info"]

    os.remove(obj_path)
    return symbols


@lru_cache(maxsize=10)
def get_relocations(source_path, machine=None, session=None):
    obj_path = get_object_path(source_path, machine, session)
    with open(obj_path, "rb") as f:
        elf = ELFFile(f)
        # Here we're getting the SHT_RELA type section as it's more common
        relocations = elf.get_section_by_name(".rela.text")
        symtab = elf.get_section_by_name(".symtab")

        if not relocations:
            return set() 

        res = set()
        for rel in relocations.iter_relocations():
            symbol = symtab.get_symbol(rel["r_info_sym"])
            if symbol["st_info"]["type"] == "STT_NOTYPE":
                res.add(symbol.name)

    os.remove(obj_path)
    return res

