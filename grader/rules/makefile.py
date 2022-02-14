from .rule import rule

from grader.result import Result

from grader.machine import with_machine_rule

@rule
@with_machine_rule
class MakefileRule:
    def __init__(self, config):
        self.compiler = config.get("compiler", "gcc")
        self.updates = config["updates"]

    def apply(self, project):
        pass

    def get_built_files(self, make_output):
        files = []
        for l in make_output.strip().split('\n'):
            args = l.strip().split()
            found = False
            for i, arg in enumerate(args):
                if arg == '-o':
                    assert i < len(args) - 1
                    files.append(args[i + 1])
                    found = True
                    break

            if not found:
                if '-c' in args:
                    source_count = 0
                    source = None
                    for arg in args:
                        if arg.endswith(".c"):
                            source_count += 1
                            source = arg
                    if source_count == 1:
                        files.append(source[:-1] + 'o')

        return set(files)
    
    def test_makefile(self, rem):
        initial_file_count = len(rem.cwd.list())

        retcode, out, err = self.session.run("make", retcode=None)

        if retcode:
            return {
                "fail": "error",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        if not rem.path("tour").exists():
            return {
                "fail": "exists",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        expected_files = set(["map.o", "input.o", "tour.o", "tour"])

        for l in out.strip().split("\n"):
            if not l.strip().startswith("gcc"):
                return {
                    "fail": f"weird_not_gcc: '{l}'",
                    "retcode": retcode,
                    "out": out,
                    "err": err,
                }

            if "tour" in l.split() and l.count("tour.c") > 0:
                return {
                    "fail": f"weird_direct_source: '{l}'",
                    "retcode": retcode,
                    "out": out,
                    "err": err,
                }


        found_files = get_built_files(out)
        if found_files != expected_files:
            return {
                "fail": f"weird_mismatched_files: {list(found_files)}",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        time.sleep(2)
        session.run("touch map.h")
        retcode, out, err = session.run("make", retcode=None)

        if retcode:
            return {
                "fail": "error",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        expected_files = set(["map.o", "tour.o", "tour"])
        found_files = get_built_files(out)
        if found_files != expected_files:
            return {
                "fail": f"select: rebuilt files {list(found_files)}",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        retcode, out, err = session.run("make clean", retcode=None)
        file_count = len(rem.cwd.list())
        if file_count != initial_file_count:
            return {
                "fail": f"clean: initial {initial_file_count}, final {file_count}",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        return {
            "fail": None
        }
