from grader.result import Result

from enum import Enum


class ResultRenderType(Enum):
    TOGETHER = 1
    SEPARATE = 2


def with_csc230_render(cls):
    old_init = cls.__init__
    def new_init(self, config: dict):
        self.render_type = ResultRenderType[config.get("render_type", "together").upper()]
        self.penalty_suffix = config.get("penalty_suffix", "")
        old_init(self, config)
    cls.__init__ = new_init

    def render_result(self, result: Result):
        if self.render_type == ResultRenderType.TOGETHER:
            review = result.render_penalty(self.penalty_suffix) + " " + \
                     result.render_comments() + "\n\n" + \
                     result.render_messages()

            messages = ""
        else:
            review = result.render_penalty(self.penalty_suffix) + " " + \
                     result.render_comments()
            messages = result.render_messages()

        return review, messages
    cls.render_result = render_result

    return cls
