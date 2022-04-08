from .rule import rule

from grader.project import Project
from grader.result import Result
from grader.rules.decorators import occurence_counter, binary_rule, skip_review_on_good

@rule
@skip_review_on_good
@occurence_counter
class ResourceSetCountRule:
    def __init__(self, config: dict):
        self.name = config["resource_name"]

    def apply(self, project: Project):
        res = Result()
        for f in project.resource_set_files(self.name):
            if not f.path.exists():
                res.penalty += 1
                res.messages.append(f"{f.name} missing")

        if res.penalty:
            res.comments.append(f'Some "{self.name}" files missing')
        return res


@rule
@skip_review_on_good
@binary_rule
class FilePresentRule:
    def __init__(self, config: dict):
        self.name = config["name"]

    def apply(self, project: Project):
        f = next(filter(lambda f: f.name == self.name, project.files()), None)
        assert f is not None
        
        res = Result()
        if not f.path.exists():
            res.penalty = True
            res.comments.append(f"{self.name} missing")
            res.messages.append(f"{self.name} missing")
        else:
            res.penalty = False

        return res


@rule
@skip_review_on_good
@occurence_counter
class ExtraFilesRule:
    def __init__(self, config: dict):
        pass

    def apply(self, project: Project):
        whitelist = set(f.name for f in project.files())

        res = Result()
        extra_files = []
        for path in project.root.list():
            if path.name not in whitelist:
                res.penalty += 1
                res.messages.append(f"Extra file: {path.name}")
                extra_files.append(path.name)

        if res.penalty:
            res.comments.append(f"Some extra files found{(': ' + ', '.join(extra_files)) if len(extra_files) < 6 else ''}")

        return res


@rule
class LsRule:
    def __init__(self, config: dict):
        pass

    def apply(self, project: Project):
        res = Result(need_review=False);
        res.custom["LS_root"] = "\n".join(f.name for f in sorted(project.root.list()))
        return res
