import database as db
import config

class MockCursor:
    def __init__(self):
        self.queries = []
        self.responses = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        if self.responses:
            return self.responses.pop(0)
        return None

    def fetchall(self):
        if self.responses:
            return self.responses.pop(0)
        return []

cursor = MockCursor()

# Test equipment insert
config.EQUIPMENT_DB["rusty_knife"] = {}
config.ITEMS_INFO["rusty_knife"] = {"max_stack": 1}

# Let count be 0
cursor.responses.append((0,))

db.add_item(123, "rusty_knife", qty=3, cursor=cursor, specific_durability=10)

print(cursor.queries)

# Test consumable insert
config.ITEMS_INFO["battery"] = {"max_stack": 5}
cursor = MockCursor()
cursor.responses.append([]) # existing stacks
cursor.responses.append((0,)) # count

db.add_item(123, "battery", qty=6, cursor=cursor)
print(cursor.queries)
