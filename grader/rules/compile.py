from .rule import rule

from grader.rules.decorators import binary_rule

from grader.machine import with_machine_rule
from grader.result import Result

from itertools import product

@rule
@binary_rule
@with_machine_rule
class CompilationRule:
    def __init__(self, config):
        self.compiler = config["compiler"]
        self.cflags = config["cflags"]
        self.ldflags = config["ldflags"]
        self.modules = config["modules"]

    def apply(self, project, session):
        res = Result()
        res.custom["no_review"] = True

        modules = filter(lambda m: m.name in self.modules, project.modules)
        sources = [s for m in modules for s in m.sources]
        source_combos = product(m.sources for m in modules)
        object_combos = map(lambda l: map(get_object_file_name, l), source_combos)

        for s in sources:
            cmd = f"{self.compiler} {self.cflags} -c -o {get_object_file_name(s.name)} s.name"
            retcode, out, err = session.run(cmd, retcode=None)
            if retcode or err.strip() != "" or out.strip() != "":
                res.custom["no_review"] = False

            if retcode:
                res.penalty = True
                res.comments.append("Didn't compile")

            res.custom[f"COMPILATION_{s.name}"] = f"{cmd}\nstdout:\n{out}\nstderr:\n{err}\n\n"

        linker_result = ""
        for c in source_combos:
            cmd = f"{self.compiler} {self.ldflags} {' '.join(c)}"
            retcode, out, err = session.run(cmd, retcode=None)
            if retcode or err.strip() != "" or out.strip() != "":
                res.custom["no_review"] = False

            if retcode:
                res.penalty = True
                res.comments.append("Didn't link")

            linker_result = linker_result + f"{cmd}\nstdout:\n{out}\nstderr:\n{err}\n\n"

        res.custom["COMPILATION_linker"] = linker_result
            
        return res

