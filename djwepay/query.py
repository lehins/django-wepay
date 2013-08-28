
class WePayQuerySet(QuerySet):

    def create(self, **kwargs):
        obj = self.model(**kwargs)
