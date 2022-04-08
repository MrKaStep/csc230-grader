from .rule import rule, construct_rule

from grader.project import Project
from grader.result import Result


@rule
class CompoundRule:
    def __init__(self, config: dict):
        self.rules = [construct_rule(rule_config) for rule_config in config["rules"]]

    def apply(self, project: Project):
        res = Result(need_review=False)
        for r in self.rules:
            res += r.apply(project)
        return res


@rule
class ProjectPathRule:
    def __init__(self, config: dict):
        pass

    def apply(self, project: Project):
        res = Result(need_review=False)
        res.custom["PROJECT_PATH"] = project.root
        return res
