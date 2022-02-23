from .rule import rule

from grader.result import Result
from grader.rules.decorators import occurence_counter, per_module
from grader.util import get_symbols

@rule
@occurence_counter
@per_module(annotate_comments=True)
class StaticFunctionsRule:
    def __init__(self, config):
        self.whitelist = config["whitelist"]

    def apply(self, module):
        res = Result()

        symbols = get_symbols(module.source.path)

        for symbol, info in symbols.items():
            bind = info["bind"]
            if bind != "STB_LOCAL" and symbol not in self.whitelist[module.name]:
                res.messages.append(f"{symbol} in {module.sources[0].path} has bind {bind}")
                res.comments.append(f"{symbol} could've been static")
                res.penalty += 1
        return res


@rule
@per_module(annotate_comments=False)
class RequiredFunctionsRule:
    def __init__(self, config):
        self.symbols = config["symbols"]

    def apply(self, module):
        res = Result()
        symbols = get_symbols(module.source.path)

        found = set(symbols.keys())

        for s in self.symbols[module.name]:
            if s not in found:
                res.messages.append(f"{s} not defined")
        return res
        
