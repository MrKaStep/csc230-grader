from .rule import rule

from grader.rules.decorators import occurence_counter

from grader.machine import with_machine_rule
from grader.result import Result

from plumbum.path.utils import copy

@rule
@occurence_counter
@with_machine_rule
class TestRule:
    def __init__(self, config):
        self.build_command = config["build_command"]
        self.input_set_name = config["inputs"]
        self.output_set_name = config["outputs"]
        self.retcode = config.get("retcode", 0)

    def apply(self, project):
        res = Result()

        retcode, _, _ = self.session.run(self.build_command, retcode=None)
        if retcode:
            res.penalty = 10000
            res.comments.append("Program didn't compile")
            res.messages.append(f"compilation command exited with exit code {retcode}")
            return res

        failed_tests = []
        for inp, exp in zip(project.resource_set_files(self.input_set_name),
                project.resource_set_files(self.output_set_name)):
            cwd = self.machine.cwd
            copy(inp.path, self.machine.cwd)
            copy(exp.path, self.machine.cwd)

            retcode, _, _ = self.session.run(f"timeout 1s ./a.out < {cwd / inp.name} > {cwd / 'output'}", retcode=None)
            if retcode != self.retcode:
                res.penalty += 1
                res.messages.append(f"{inp.name} failed: retcode {retcode}")
                failed_tests.append(inp.name)
                continue

            retcode, _, _ = self.session.run(f"diff {cwd / 'output'} {cwd / exp.name}", retcode=None)
            if retcode:
                res.penalty += 1
                res.messages.append(f"{inp.name} failed: diff")
                failed_tests.append(inp.name)
                continue

        if len(failed_tests):
            res.comments += [f"{t} failed" for t in failed_tests]
        else:
            res.need_review = False
        return res

