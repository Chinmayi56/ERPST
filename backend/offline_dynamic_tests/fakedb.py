"""
Minimal in-memory async fake of the subset of Motor's API this project's
service layer actually uses: find_one, find_one_and_update, insert_one,
find(...).sort(...).limit(...) with async iteration, count_documents,
update_one, update_many, create_index (no-op).
Not a full Mongo emulator -- built only to exercise the REAL, unmodified
service-layer code (application_service, employee_auth_service,
registration_service, notification_service, id_service) against realistic
document flows, offline.
"""
import copy


def _match(doc, filt):
    for k, v in filt.items():
        if k == "$or":
            if not any(_match(doc, sub) for sub in v):
                return False
            continue
        if isinstance(v, dict) and "$in" in v:
            if doc.get(k) not in v["$in"]:
                return False
            continue
        if doc.get(k) != v:
            return False
    return True


class Cursor:
    def __init__(self, docs):
        self._docs = docs
        self._i = 0

    def sort(self, key, direction=-1):
        self._docs = sorted(self._docs, key=lambda d: d.get(key), reverse=(direction == -1))
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        d = copy.deepcopy(self._docs[self._i])
        self._i += 1
        return d


class FakeCollection:
    def __init__(self):
        self._docs = []

    async def create_index(self, *a, **k):
        return None

    async def insert_one(self, doc):
        doc = copy.deepcopy(doc)
        if "_id" not in doc:
            doc["_id"] = f"fakeid-{len(self._docs)}-{id(doc)}"
        self._docs.append(doc)
        return doc

    async def find_one(self, filt=None, sort=None):
        filt = filt or {}
        matches = [d for d in self._docs if _match(d, filt)]
        if sort:
            key, direction = sort[0]
            matches.sort(key=lambda d: d.get(key), reverse=(direction == -1))
        return copy.deepcopy(matches[0]) if matches else None

    def find(self, filt=None):
        filt = filt or {}
        matches = [d for d in self._docs if _match(d, filt)]
        return Cursor(matches)

    async def count_documents(self, filt=None):
        filt = filt or {}
        return len([d for d in self._docs if _match(d, filt)])

    async def find_one_and_update(self, filt, update, return_document=True, upsert=False):
        for d in self._docs:
            if _match(d, filt):
                self._apply_update(d, update)
                return copy.deepcopy(d)
        if upsert:
            new_doc = dict(filt)
            self._apply_update(new_doc, update)
            self._docs.append(new_doc)
            return copy.deepcopy(new_doc)
        return None

    async def update_one(self, filt, update):
        for d in self._docs:
            if _match(d, filt):
                self._apply_update(d, update)
                return type("R", (), {"modified_count": 1})()
        return type("R", (), {"modified_count": 0})()

    async def update_many(self, filt, update):
        n = 0
        for d in self._docs:
            if _match(d, filt):
                self._apply_update(d, update)
                n += 1
        return type("R", (), {"modified_count": n})()

    def _apply_update(self, doc, update):
        if "$set" in update:
            doc.update(update["$set"])
        if "$inc" in update:
            for k, v in update["$inc"].items():
                doc[k] = doc.get(k, 0) + v


class FakeDB:
    def __init__(self):
        self._collections = {}

    def __getattr__(self, name):
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]
