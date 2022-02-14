from copy import deepcopy

from grader.project import Project
from grader.result import Result
from grader.scope import Scope
from grader.util import camel_to_snake_case


# Enable automatic rule registration
_rule_registry = {}


def _register_rule(name, cls):
    # _rule_registry[name] = cls
    assert camel_to_snake_case(name) not in _rule_registry
    _rule_registry[camel_to_snake_case(name)] = cls


def add_penalty_limit(cls):
    old_init = cls.__init__
    def new_init(self, config):
        old_init(self, config)

        assert not hasattr(self, "penalty_limit")
        
        self.penalty_limit = config.get("penalty_limit", -1)

    cls.__init__ = new_init

    old_apply = cls.apply
    def new_apply(self, project, *args, **kwargs):
        try:
            res = old_apply(self, project, *args, **kwargs)
            if self.penalty_limit >= 0:
                res.penalty = min(res.penalty, self.penalty_limit)
        except Exception as e:
            res = Result()
            res.messages.append(f"Execution of rule {cls.__name__} failed at {project}:\n{e}")
        return res
    cls.apply = new_apply

    return cls


def rule(cls):
    assert hasattr(cls, "apply") and callable(getattr(cls, "apply"))

    if not cls.__name__.endswith("Rule"):
        raise ValueError(f"invalid rule class name: {name}. Rule class names should end with 'Rule'")
    _register_rule(cls.__name__[:-len("Rule")], cls)

    cls = add_penalty_limit(cls)

    def call(self, *args, **kwargs):
        return self.apply(*args, **kwargs)

    cls.__call__ = call
    return cls


def construct_rule(config):
    return _rule_registry[config["name"]](config["config"])


