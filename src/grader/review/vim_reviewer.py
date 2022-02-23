from .reviewer import reviewer
from .decorators import with_csc230_render

from grader.project import Project
from grader.result import Result
from grader.util import create_tempfile

from contextlib import ExitStack
from plumbum import local, FG


@reviewer
@with_csc230_render
class VimReviewer:
    def __init__(self, config):
        with open(config["session"]) as f:
            self.template = f.read()
    
    def _create_session_file(self, project: Project, result: Result):
        session = self.template.replace("ROOT", project.root)

        review, messages = self.render_result(result)

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
        with ExitStack() as stack:
            self.exit_stack = stack
            vim = local["vim"]
            with self._create_session_file(project, result) as s:
                vim["-S", s.name] & FG
                return self._get_review()

