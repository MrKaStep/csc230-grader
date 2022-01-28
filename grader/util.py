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

