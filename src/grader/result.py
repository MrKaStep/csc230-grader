class Result:
    def __init__(self, need_review=True):
        self.penalty = 0
        self.messages = []
        self.comments = []
        self.custom = {} 
        self.need_review = need_review

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

