from .reviewer import reviewer
from grader.project import Project
from grader.rules.rule import Result
from grader.util import create_tempfile

from contextlib import ExitStack
from enum import Enum
from plumbum import local, FG


class ResultRenderType(Enum):
    TOGETHER = 1
    SEPARATE = 2


@reviewer
class VimReviewer:
    def __init__(self, config):
        with open(config["session"]) as f:
            self.template = f.read()

        self.render_type = ResultRenderType[config.get("render_type", "together").upper()]
        self.penalty_suffix = config.get("penalty_suffix", "")

    
    def _create_session_file(self, project: Project, result: Result):
        session = self.template.replace("ROOT", project.root)
        if self.render_type == ResultRenderType.TOGETHER:
            review = result.render_penalty(self.penalty_suffix) + " " + \
                     result.render_comments() + "\n\n" + \
                     result.render_messages()

            self.review_file = self.exit_stack.enter_context(create_tempfile(review, mode="w+t"))

            session = session.replace("REVIEW_PATH", self.review_file.name)
        else:
            review = result.render_penalty(self.penalty_suffix) + " " + \
                     result.render_comments()
            messages = result.render_messages()

            self.review_file = self.exit_stack.enter_context(create_tempfile(review, mode="w+t"))

            messages_path = self.exit_stack.enter_context(create_tempfile(messages)).name

            session = session.replace("REVIEW_PATH", self.review_file.name)
            session = session.replace("MESSAGES_PATH", messages_path)

        for name, contents in result.custom.items():
            path = self.exit_stack.enter_context(create_tempfile(contents)).name
            session = session.replace(name, path)

        return create_tempfile(session)


    def _get_review(self):
        assert self.review_file is not None
        self.review_file.seek(0)
        review = self.review_file.read()
        if self.render_type == ResultRenderType.TOGETHER:
            review = review.split('\n')[0]
        else:
            review = review.strip()
        
        return review


    def review(self, project: Project, result: Result):
        if result.custom.get("no_review", False):
            return ""
        with ExitStack() as stack:
            self.exit_stack = stack
            vim = local["vim"]
            with self._create_session_file(project, result) as s:
                vim["-S", s.name] & FG
                return self._get_review()

