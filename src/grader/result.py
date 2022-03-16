class Result:
    def __init__(self, neutral=False):
        self.penalty = 0
        self.messages = []
        self.comments = []
        self.custom = {} 
        if neutral:
            self.need_review = False
        else:
            self.need_review = True

    def __iadd__(self, other):
        self.penalty += other.penalty
        self.messages += other.messages
        self.comments += other.comments
        self.custom = {**self.custom, **other.custom}
        self.need_review |= other.need_review
        return self

    def __add__(self, other):
        res = deepcopy(self)
        res += other
        return res

    def __str__(self):
        return f"<Result penalty: {self.penalty} comments: {'. '.join(self.comments)} messages: <{len(self.messages)} messages> need_review: {self.need_review}>"

    def render_penalty(self, suffix=''):
        if self.penalty == 0:
            return "c"
        if int(self.penalty) == self.penalty:
            self.penalty = int(self.penalty)
        return f"-{self.penalty}{suffix}"

    def render_comments(self, end='.'):
        return " ".join((c + end for c in dict.fromkeys(self.comments)))

    def render_messages(self):
        return "\n".join(dict.fromkeys(self.messages))

