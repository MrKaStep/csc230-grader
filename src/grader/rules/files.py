from .rule import rule

from grader.project import Project
from grader.result import Result
from grader.rules.decorators import occurence_counter, binary_rule

@rule
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
@occurence_counter
class ExtraFilesRule:
    def __init__(self, config: dict):
        pass

    def apply(self, project: Project):
        whitelist = set(f.name for f in project.files())

        res = Result()
        for path in project.root.list():
            if path.name not in whitelist:
                res.penalty += 1
                res.messages.append(f"Extra file: {path.name}")

        if res.penalty:
            res.comments.append("Some extra files found")

        return res
