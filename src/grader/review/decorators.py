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

    def render_penalty(res, suffix=''):
        if res.penalty == 0:
            return "c"
        if int(res.penalty) == res.penalty:
            res.penalty = int(res.penalty)
        return f"-{res.penalty}{suffix}"

    def render_comments(res, end='.'):
        return " ".join((c + end for c in dict.fromkeys(res.comments)))

    def render_messages(res):
        return "\n".join(dict.fromkeys(res.messages))

    def render_result(self, result: Result):
        review_line = render_penalty(result, self.penalty_suffix) + " " + \
                      render_comments(result)

        if review_line.strip() == 'c':
            review_line = ""

        if self.render_type == ResultRenderType.TOGETHER:
            review = review_line + "\n\n" + render_messages(result)
            messages = ""
        else:
            review = review_line
            messages = render_messages(result)

        return review, messages
    cls.render_result = render_result

    return cls
