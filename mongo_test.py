import ps_secrets
import pymongo

dbparms = ps_secrets.mongodb["pythonmongo"]
dbparms["username"] = "pythonmongo"
con_str = "mongodb+srv://{username}:{password}@sandbox.xn4gy.mongodb.net/?retryWrites=true&w=majority".format(*dbparms)
client = pymongo.MongoClient(con_str, server_api=ServerApi('1'))
db = client.test

