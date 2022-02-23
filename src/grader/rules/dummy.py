from .rule import rule

from grader.project import Project
from grader.result import Result


@rule
class DummyRule:
    def __init__(self, config: dict):
        self.desired = config["desired"]

    def apply(self, project: Project):
        res = Result()
        file_count = len(list(project.files()))
        if file_count != self.desired:
            res.penalty = 100500
            res.comments.append("Invalid number of files")
            res.messages.append(f"Found {file_count} files. Required {self.desired}")
        return res

