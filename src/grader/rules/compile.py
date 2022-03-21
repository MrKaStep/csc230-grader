from .rule import rule

from grader.rules.decorators import binary_rule

from grader.machine import with_machine_rule
from grader.result import Result

from grader.util import get_object_file_name

from itertools import product

@rule
@binary_rule
@with_machine_rule
class CompilationRule:
    def __init__(self, config):
        self.compiler = config.get("compiler", "gcc")
        self.cflags = config.get("cflags", "")
        self.ldflags = config.get("ldflags", "")
        self.modules = config["modules"]

    def apply(self, project):
        res = Result()
        res.need_review = False

        modules = list(filter(lambda m: m.name in self.modules, project.modules()))
        sources = [s.name for m in modules for s in m.sources]
        source_combos = list(product(*[[s.name for s in m.sources] for m in modules]))
        object_combos = list(map(lambda l: list(map(get_object_file_name, l)), source_combos))

        entire_message = ""
        for s in sources:
            cmd = f"{self.compiler} {self.cflags} -c -o {get_object_file_name(s)} {s}"
            retcode, out, err = self.session.run(cmd, retcode=None)
            if retcode or err.strip() != "" or out.strip() != "":
                res.need_review = True

            if retcode:
                res.penalty = True
                res.comments.append("Didn't compile")

            res.custom[f"COMPILATION_{s}"] = f"{cmd}\nstdout:\n{out}\nstderr:\n{err}\n\n"
            entire_message += res.custom[f"COMPILATION_{s}"]

        if not res.penalty:
            linker_result = ""
            for c in object_combos:
                cmd = f"{self.compiler} {self.ldflags} {' '.join(c)}"
                retcode, out, err = self.session.run(cmd, retcode=None)
                if retcode or err.strip() != "" or out.strip() != "":
                    res.need_review = True

                if retcode:
                    res.penalty = True
                    res.comments.append("Didn't link")

                linker_result = linker_result + f"{cmd}\nstdout:\n{out}\nstderr:\n{err}\n\n"

            res.custom["COMPILATION_linker"] = linker_result
            entire_message += linker_result

        res.custom["COMPILATION_combined"] = entire_message
            
        return res

