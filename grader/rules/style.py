from .rule import rule

from grader.project import File
from grader.result import Result
from grader.util import get_c_without_comments
from grader.rules.decorators import per_file, occurence_counter

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
@per_file(annotate_comments=False)
class MagicNumbersRule:
    def __init__(self, config):
        self.whitelist = config.get("whitelist", [0, 1])
        self.penalty = config.get("per_magic_penalty", 0)

    def apply(self, f: File):
        res = Result()
        clean_code = get_c_without_comments(f)
        magic_numbers = set()

        for i, l in enumerate(clean_code.split('\n'), 1):
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
@per_file(annotate_comments=False)
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
@per_file(annotate_comments=False)
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
@per_file()
class LastLineEndingRule:
    def __init__(self, config):
        pass

    def apply(self, f: File):
        res = Result()
        if not f.read().endswith("\n"):
            res.penalty = 0.5
            res.comments.append("Missing newline at the end of file")
            res.messages.append("Missing newline at the end of file")
