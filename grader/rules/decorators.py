from grader.project import Project
from grader.result import Result

def per_file(cls, annotate_comments=True, annotate_messages=True):
    old_apply = cls.apply
    def new_apply(self, project: Project):
        res = Result()
        for f in project.files():
            if not f.path.exists():
                res.messages.append(f"{f.name} does not exist")
                continue

            try:
                file_res = old_apply(f)
                if annotate_messages:
                    file_res.messages = [f"{f.name}: {m}" for m in file_res.messages]

                if annotate_comments:
                    file_res.comments = [f"{f.name}: {c}" for c in file_res.comments]
                res += file_res
            except Exception as e:
                res.messages.append(f"Execution fo rule {cls.__name__} failed at {f}:\n{e}")
        return res

    cls.apply = new_apply
    return cls
