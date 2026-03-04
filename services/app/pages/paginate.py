class Pagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page
        self.has_prev = page > 1
        self.has_next = page < self.pages

    def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num >= self.page - left_current and num <= self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num