from grader.project import Project
from grader.result import Result

import traceback

def _per_object(obj_type, annotate_comments, annotate_messages):
    getter_func_map = {
        "module": Project.modules,
        "file": Project.files,
        "source_file": Project.source_files,
    }

    getter = getter_func_map[obj_type]

    def inner(cls):
        old_init = cls.__init__
        def new_init(self, config):
            old_init(self, config)
            self.per_obj_penalty_limit = config.get(f"per_{obj_type}_penalty_limit", -1)
            self.per_obj_annotate_comments = config.get(f"per_{obj_type}_annotate_comments", annotate_comments)
            self.per_obj_annotate_messages = config.get(f"per_{obj_type}_annotate_messages", annotate_messages)

        cls.__init__ = new_init

        old_apply = cls.apply
        def new_apply(self, project: Project):
            res = Result()
            for o in getter(project):
                try:
                    obj_res = old_apply(self, o)
                    if self.per_obj_penalty_limit >= 0:
                        obj_res.penalty = min(obj_res.penalty, self.per_obj_penalty_limit)

                    if self.per_obj_annotate_messages:
                        obj_res.messages = [f"{o.name}: {m}" for m in obj_res.messages]

                    if self.per_obj_annotate_comments:
                        obj_res.comments = [f"{o.name}: {c}" for c in obj_res.comments]
                    res += obj_res
                except Exception:
                    res.messages.append(f"Execution of rule {cls.__name__} failed at {o}:\n{traceback.format_exc()}")
            return res

        cls.apply = new_apply
        return cls
    return inner


def per_source_file(annotate_comments=True, annotate_messages=True):
    return _per_object("source_file", annotate_comments, annotate_messages)


def per_module(annotate_comments=True, annotate_messages=True):
    return _per_object("module", annotate_comments, annotate_messages)


def occurence_counter(cls):
    old_init = cls.__init__
    def new_init(self, config):
        old_init(self, config)
        self.occurence_thresholds = config.get("occurence_thresholds", 1)
        self.penalty_step = config["penalty_step"]
    cls.__init__ = new_init

    old_apply = cls.apply
    def new_apply(self, o):
        res = old_apply(self, o)
        count = res.penalty
        res.penalty = 0
        if isinstance(self.occurence_thresholds, list):
            for threshold in self.occurence_thresholds:
                if count >= threshold:
                    res.penalty += self.penalty_step
                else:
                    break
        else:
            res.penalty = (count // self.occurence_thresholds) * self.penalty_step
        return res
    cls.apply = new_apply

    return cls


def binary_rule(cls):
    old_init = cls.__init__
    def new_init(self, config):
        old_init(self, config)
        self.fail_penalty = config["fail_penalty"]
    cls.__init__ = new_init

    old_apply = cls.apply
    def new_apply(self, o):
        res = old_apply(self, o)
        if res.penalty:
            res.penalty = self.fail_penalty
        else:
            res.penalty = 0
        return res
    cls.apply = new_apply

    return cls

