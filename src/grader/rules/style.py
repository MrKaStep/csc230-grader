from .rule import rule

from grader.project import File
from grader.result import Result
from grader.util import get_c_without_comments, get_symbols
from grader.rules.decorators import per_source_file, occurence_counter

import re


def find_magic_number(line):
    if line.strip().startswith("//") or line.strip().startswith("#define") or line.strip().startswith("/*") and line.strip().endswith("*/"):
        return None

    pattern = "(?<=[^a-zA-Z0-9_])[0-9]+"
    matches = re.findall(pattern, line)
    for m in matches:
        n = int(m)
        if n != 0 and n != 1:
            return n
    return None

@rule
@per_source_file(annotate_comments=False)
class MagicNumbersRule:
    def __init__(self, config):
        self.whitelist = config.get("whitelist", [0, 1])
        self.skip_markers = config.get("skip_markers", [])
        self.penalty = config.get("per_magic_penalty", 0)

    def apply(self, f: File):
        res = Result()
        clean_code = get_c_without_comments(f)
        magic_numbers = set()

        for i, l in enumerate(clean_code.split('\n'), 1):
            skip = False
            for m in self.skip_markers:
                if l.count(m) > 0:
                    skip = True
                    break
            if skip:
                continue

            for magic in self._find_magic_numbers(l):
                res.messages.append(f"Magic number {magic} at line {i}")
                magic_numbers.add(magic)

        if self.penalty:
            for magic in magic_numbers:
                res.comments.append(f"{magic} is a magic number")
                res.penalty += self.penalty

        return res


    def _find_magic_numbers(self, line):
        if line.strip().startswith("#define"):
            return []

        pattern = "(?<=[^a-zA-Z0-9_])[0-9]+"
        matches = re.findall(pattern, line)
        return list(filter(lambda x: x not in self.whitelist, map(int, matches)))

@rule
@occurence_counter
@per_source_file(annotate_comments=False)
class LineEndingsRule:
    def __init__(self, config):
        pass

    def apply(self, f: File):
        res = Result()
        res.penalty = f.read().count("\r")
        if res.penalty:
            res.comments.append(f"Invalid line endings found")
            res.messages.append(f"{res.penalty} carriage returns found")
        return res


@rule
@per_source_file(annotate_comments=False)
@occurence_counter
class HardTabsRule:
    def __init__(self, config):
        pass

    def apply(self, f: File):
        res = Result()
        res.penalty = f.read().count("\t")
        if res.penalty:
            res.comments.append(f"Hard tabs found")
            res.messages.append(f"{res.penalty} hard tabs found")
        return res


@rule
@per_source_file()
class LastLineEndingRule:
    def __init__(self, config):
        pass

    def apply(self, f: File):
        res = Result()
        if not f.read().endswith("\n"):
            res.penalty = 0.5
            res.comments.append("Missing newline at the end of file")
            res.messages.append("Missing newline at the end of file")
        return res


@rule
@occurence_counter
@per_source_file(annotate_comments=False)
class CurlyBracesRule:
    def __init__(self, config):
        pass

    def apply(self, f: File):
        res = Result()
        symbols = get_symbols(f.path) if f.name.endswith(".c") else {}
        symbols = {n: i for n, i in symbols.items() if i["type"] == "STT_FUNC" }

        level = 0
        bad_function = 0
        bad_other = 0

        def has_func_name(l):
            for s in symbols:
                if l.count(s) > 0:
                    return True
            return False

        prev_function = False
        clean_code = get_c_without_comments(f)
        for l in clean_code.split('\n'):
            for i, c in enumerate(l):
                if c == '{':
                    level += 1

                    if level == 1 and has_func_name(l[:i]):
                        bad_function += 1
                    else:
                        if (not l[:i] or l[:i].isspace()) and not prev_function:
                            bad_other += 1
                elif c == '}':
                    level -= 1
            prev_function = has_func_name(l)
                    
        if bad_function:
            res.comments.append("Bad curly braces in function definitions found")
            res.messages.append(f"Bad function curly braces: {bad_function}")

        if bad_other:
            res.comments.append("Bad curly braces in control structures found")
            res.messages.append(f"Bad other curly braces: {bad_other}")

        res.penalty = bad_function + bad_other
        return res




