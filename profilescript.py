import json
from sqlite3 import connect

conn = connect("database.db")
cursor = conn.cursor()

with open('cogs/profiles.json', 'r') as file:
    d = json.loads(file.read())

profiles = d['users']

def executeSQL(statement, data = ()):
    cursor.execute(statement, data)
    conn.commit()
    return cursor.fetchall()

def addbio(userid, bio):
    executeSQL('INSERT INTO fields (user_id, type, name, data) VALUES (?, 0, "Bio", ?)', (userid, bio))

def addpronouns(userid, pronouns):
    executeSQL('INSERT INTO fields (user_id, type, name, data) VALUES (?, 1, "Pronouns", ?), (userid, pronouns)')

def addbestfriend(user0, user1):
    status = executeSQL('SELECT relationship_id FROM relationships WHERE (user_a_id = ? AND user_b_id = ?) OR (user_a_id = ? AND user_b_id = ?)', (user0, user1, user1, user0))

    if not len(status):
        executeSQL('INSERT INTO relationships (user_a_id, user_b_id, type) VALUES (?, ?, 1)', (user0, user1))
        executeSQL('INSERT INTO relationships (user_a_id, user_b_id, type) VALUES (?, ?, 1)', (user1, user0))

def addpicture(userid, url):
    executeSQL('INSERT INTO fields (user_id, type, name, data) VALUES (?, 3, "Image Showcase", ?)', (userid, url))

def addbadges(userid, badge):
    executeSQL('INSERT INTO fields (user_id, type, name, data) VALUES (?, 2, "Badge Showcase", ?)', (userid, badge))
