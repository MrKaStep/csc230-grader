from .rule import rule

from grader.result import Result

from grader.machine import with_machine_rule

from enum import Enum

import time


class UpdateType(Enum):
    CREATE = 1
    REMOVE = 2
    DELETE = 2
    UPDATE = 3


class Update:
    def __init__(self, s):
        l = s.split()
        if len(l) != 2:
            raise ValueError(f"Invalid update: '{s}'")

        self.file = l[1]
        if l[0] == "+":
            self.type = UpdateType.CREATE
        elif l[0] == "-":
            self.type = UpdateType.REMOVE
        elif l[0] == "u":
            self.type = UpdateType.UPDATE
        else:
            raise ValueError(f"Invalid update: '{s}'")


class Step:
    def __init__(self, config, index):
        self.index = index
        self.command = config["command"]
        self.prefix = config.get("prefix")
        update_configs = config.get("updates")
        self.updates = [Update(u) for u in update_configs] if update_configs else None

        self.expected_commands = config.get("expected_commands")
        self.exact_commands = config.get("exact_commands", False)


    def check_output(self, out, res):
        if self.expected_commands:
            lines = out.strip().split("\n")
            if len(lines) != len(self.expected_commands):
                res.messages.append(f"Step {self.index} '{self.command}' failed: incorrect number of lines in the output")
                return False

            found = {}

            for l in lines:
                argv = l.split()
                for c in self.expected_commands:
                    if self.exact_commands:
                        if set(argv) == set(c.split()):
                            found[c] = True
                    else:
                        if all(a in argv for a in c.split()):
                            found[c] = True
            for c in self.expected_commands:
                if c not in found:
                    res.messages.append(f"Step {self.index} '{self.command}' failed: '{c}' not found in the output")
                    return False

        elif self.prefix:
            for l in out.strip().split("\n"):
                if not l.startswith(s.prefix):
                    res.messages.append(f"Step {self.index} '{self.command}' failed: weird line in output:\n{l}")
                    return False
        return True


@rule
@with_machine_rule
class MakefileRule:
    def __init__(self, config):
        self.steps = [Step(s, i) for i, s in enumerate(config["steps"], 1)]

    def apply(self, project):
        res = Result()

        for s in self.steps:
            if s.updates is None:
                self.session.run(s.command)
                continue

            before = {f.name: f.stat().st_mtime_ns for f in self.machine.cwd.list()}

            retcode, out, err = self.session.run(s.command, retcode=None)
            if retcode != 0:
                res.messages.append(f"Step {s.index} failed: exit code {retcode}\nstdout:\n{out}\nstderr:\n{err}\n")
                return res
            after = {f.name: f.stat().st_mtime_ns for f in self.machine.cwd.list()}
            for u in s.updates:
                if u.type == UpdateType.CREATE:
                    if not (u.file not in before and u.file in after):
                        res.messages.append(f"Step {s.index} '{s.command}' failed: {u.file} not created")
                        return res
                elif u.type == UpdateType.REMOVE:
                    if not (u.file in before and u.file not in after):
                        res.messages.append(f"Step {s.index} '{s.command}' failed: {u.file} not removed")
                        return res
                elif u.type == UpdateType.UPDATE:
                    if not (u.file in before and u.file in after and before[u.file] != after[u.file]):
                        res.messages.append(f"Step {s.index} '{s.command}' failed: {u.file} not updated")
                        return res

            if not s.check_output(out, res):
                return res

            checked_files = {u.file for u in s.updates}
            for name in (set(before.keys()) | set(after.keys())) - checked_files:
                time_before = before.get(name)
                time_after = after.get(name)
                if time_before != time_after:
                    res.messages.append(f"Step {s.index} '{s.command}' failed: {name} changed: {time_before} != {time_after}")
                    return res

        res.need_review = False
        return res

