from grader.project import Project
from grader.result import Result

def per_file(annotate_comments=True, annotate_messages=True):
    def inner(cls):
        old_init = cls.__init__
        def new_init(self, config):
            old_init(self, config)
            self.per_file_penalty_limit = config.get("per_file_penalty_limit", -1)
            self.per_file_annotate_comments = config.get("per_file_annotate_comments", annotate_comments)
            self.per_file_annotate_messages = config.get("per_file_annotate_messages", annotate_messages)

        cls.__init__ = new_init

        old_apply = cls.apply
        def new_apply(self, project: Project):
            res = Result()
            for f in project.files():
                if not f.path.exists():
                    res.messages.append(f"{f.name} does not exist")
                    continue

                try:
                    file_res = old_apply(self, f)
                    if self.per_file_penalty_limit >= 0:
                        file_res.penalty = min(file_res.penalty, self.per_file_penalty_limit)

                    if self.per_file_annotate_messages:
                        file_res.messages = [f"{f.name}: {m}" for m in file_res.messages]

                    if self.per_file_annotate_comments:
                        file_res.comments = [f"{f.name}: {c}" for c in file_res.comments]
                    res += file_res
                except Exception as e:
                    res.messages.append(f"Execution of rule {cls.__name__} failed at {f}:\n{e}")
            return res

        cls.apply = new_apply
        return cls
    return inner


def occurence_counter(cls):
    old_init = cls.__init__
    def new_init(self, config):
        old_init(self, config)
        self.occurence_thresholds = config["occurence_thresholds"]
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
