from grader.rules.rule import Result
from grader.project import Project
from grader.util import camel_to_snake_case

import re


_reviewer_registry = {}


def _register_reviewer(name, cls):
    # _reviewer_registry[cls.__name__] = cls
    _reviewer_registry[camel_to_snake_case(name)] = cls


def _make_callable(cls):
    def call(self, *args, **kwargs):
        return self.review(*args, **kwargs)

    cls.__call__ = call

    return cls


def _enable_macros(cls):
    def expand_macros(self, message):
        delimiters = ".,:;!?\\s"
        for k, v in sorted(self.macros.items(), key=lambda x: len(x[0]), reverse=True):
            message = re.sub(f"(?<=[{delimiters}]){k}(?=[{delimiters}]|$)", v, message)
        return message

    cls.expand_macros = expand_macros

    old_init = cls.__init__
    def init(self, config):
        old_init(self, config)
        assert not hasattr(self, "macros")

        self.macros = config.get("macros", {})

    cls.__init__ = init

    old_review = cls.review
    def new_review(self, project, result):
        return self.expand_macros(old_review(self, project, result))

    cls.review = new_review



def reviewer(cls):
    assert hasattr(cls, "review") and callable(getattr(cls, "review"))

    if not cls.__name__.endswith("Reviewer"):
        raise ValueError(f"invalid reviewer class name: {name}. Reviewer class names should end with 'Reviewer'")
    _register_reviewer(cls.__name__[:-len("Reviewer")], cls)

    cls = _make_callable(cls)
    cls = _enable_macros(cls)

    return cls


def construct_reviewer(name, config):
    return _reviewer_registry[name](config)

