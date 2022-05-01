from .rule import rule

from grader.result import Result
from grader.rules.decorators import occurence_counter, per_module
from grader.util import get_symbols, get_relocations

@rule
@occurence_counter
@per_module(pass_project=True)
class StaticSymbolsRule:
    def __init__(self, config):
        self.whitelist = config["whitelist"]
        self.check_variables = config.get("check_variables", False)

    def apply(self, module, project):
        res = Result()

        symbols = get_symbols(module.source.path)

        relocations = set()
        for m in project.modules():
            if m is not module:
                try:
                    relocations |= get_relocations(m.source.path)
                except RuntimeError as e:
                    res.messages.append(f"Failed to get relocations for {m.name}: {e}")

        for symbol, info in symbols.items():
            if info["type"] != "STT_FUNC" and (not self.check_variables or info["type"] != "STT_OBJECT"):
                continue
            bind = info["bind"]
            if bind != "STB_LOCAL" and symbol not in self.whitelist[module.name]:
                if symbol in relocations:
                    res.messages.append(f"{symbol} in {module.source.path} is global and is used elsewhere")
                    res.need_review=True
                else:
                    res.messages.append(f"{symbol} in {module.source.path} has bind {bind}")
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
        
