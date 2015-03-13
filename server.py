import json
import cherrypy
import jinja2
from py2neo import neo4j
import py2neo.error

import os.path
current_dir = os.path.dirname(os.path.abspath(__file__))

class UnknownNodeException(Exception):
    pass

def serializeGraphStream(stream, nodeLabels, relationshipLabels):
    nodes = []
    relationships = []
    for i in stream:
        for label in nodeLabels:
            # Get the ref number
            node = getattr(i, label)
            refNum = int(node.ref.split("/")[1])

            # # Avoid duplicating nodes in the JSON file if they already exist
            # if next((x for x in nodes if x["id"] == refNum), None) != None:

            result = node.properties

            # Get the appropriate caption
            if "User" in node.labels:
                caption = node.properties["ip"]
                result.update({"type" : "user"})
            elif "Topic" in node.labels:
                caption = node.properties["name"]
                result.update({"type" : "topic"})
            else:
                raise UnknownNodeException

            # Add the relevant properties
            result.update({"id" : refNum, "caption"  : caption})

            # Add it to the nodes list
            nodes.append(result)
        for label in relationshipLabels:
            rel = getattr(i, label)
            # Source, target, caption
            source, target, caption = rel.start_node.ref.split("/")[1], rel.end_node.ref.split("/")[1], rel.type
            relationships.append({"source" : source, "target" : target, "caption" : caption})
    return {"nodes" : nodes, "edges" : relationships}

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
        with open("templates/index.html", "r") as f:
            return f.read()

class Graph(CypherSender):
    @cherrypy.expose
    def index(self):
        query = "MATCH (a:User)-[d:EDITED]->(b:Topic)<-[e:EDITED]-(c:User) RETURN a,b,c,d,e LIMIT 100"
        stream = self.getCypherStream(query)
        res = serializeGraphStream(stream, list("abc"), list("de"))
        stream.close()
        return json.dumps(res)

@cherrypy.popargs("fr", "to")
class Path(CypherSender):
    @cherrypy.expose
    def index(self, fr, to):
        return "Path from %s to %s" % (fr, to)

import yaml
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # cherrypy.config.update({'environment': 'production',
    #                         'log.error_file': 'site.log',
    #                         'log.screen': True})
    #
    # conf = {'/data': {'tools.staticdir.on': True,
    #                   'tools.staticdir.dir': os.path.join(current_dir, 'data')}}
    #
    # cherrypy.quickstart(App(), "/", config=conf)
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
