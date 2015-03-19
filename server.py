import json
import cherrypy
import jinja2
from py2neo import neo4j
import py2neo.error

import os.path
current_dir = os.path.dirname(os.path.abspath(__file__))
from serializers import serializeGraphStream

def wrapHtml(file, template_dir):
    output = ""
    with open(os.path.join(template_dir, "header.html"), "r") as f:
        output += f.read()
    with open(os.path.join(template_dir, file), "r") as f:
        output += f.read()
    with open(os.path.join(template_dir, "footer.html"), "r") as f:
        output += f.read()
    return output

class CypherSender(object):
    def __init__(self):
        self.neo = neo4j.Graph()

    def getCypher(self, query):
        return self.neo.cypher.execute(query)

    def getCypherStream(self,query):
        return self.neo.cypher.stream(query)

class App(CypherSender):
    def __init__(self):
        self.path = Path()
        self.graph = Graph()
        super(App, self).__init__()

    @cherrypy.expose
    def index(self):
        return wrapHtml("index.html", "templates")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def encoding(self):
        return cherrypy.request.json

class Graph(CypherSender):
    @cherrypy.expose
    def index(self):
        query = "MATCH (a:User)-[d:EDITED]->(b:Topic)<-[e:EDITED]-(c:User) RETURN a,b,c,d,e LIMIT %s" % ("10")
        stream = self.getCypherStream(query)
        res = serializeGraphStream(stream, list("abc"), list("de"))
        stream.close()
        return json.dumps(res)

@cherrypy.popargs("fr", "to")
class Path(CypherSender):
    @cherrypy.expose
    def index(self, fr, to):
        query = "MATCH a,b,p=shortestPath((a)-[*]-(b)) WHERE id(a)=%s AND id(b)=%s RETURN p;" % (fr, to)
        r = self.getCypherStream(query)

        # Extract paths from the stream
        paths = list()
        for i in r:
            paths.append(i.p)

        # Close the stream
        r.close()

        # Serialize and return the list
        if paths != []:
            rels = map(serializeRelationship, paths[0].relationships)
            return json.dumps(rels)
        return None

import yaml
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {
        "/js" : {
            "tools.staticdir.on" : True,
            "tools.staticdir.dir" : os.path.join(current_dir, 'data/js')
        },
        "/css" : {
            "tools.staticdir.on" : True,
            "tools.staticdir.dir" : os.path.join(current_dir, 'data/css')
        }
      }
    with open("conf/server.conf", "r") as f:
        cherrypy.quickstart(App(), config=conf)
