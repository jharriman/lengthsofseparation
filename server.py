import json
import cherrypy
import jinja2
from py2neo import neo4j
import py2neo.error

def serializeGraph(graph):
    sg = graph.to_subgraph()
    nodes = []
    relationships = []
    for i in sg.nodes:
        # Get the ref number
        refNum = int(i.ref.split("/")[1])

        # Get the appropriate caption
        if "User" in i.labels:
            caption = i.properties["ip"]
        elif "Topic" in i.labels:
            caption = i.properties["name"]

        # Add the relevant properties
        result = i.properties
        result.update({"id" : refNum, "caption"  : caption})

        # Add it to the nodes list
        nodes.append(result)
    for i in sg.relationships:
        # Source, target, caption
        source, target, caption = i.start.split("/")[1], i.end.split("/")[1], i.type
        relationships.append({"source" : source, "target" : target, "caption" : caption})
    return {"nodes" : nodes, "edges" : edges}

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
            # Get the appropriate caption
            if "User" in node.labels:
                caption = node.properties["ip"]
            elif "Topic" in node.labels:
                caption = node.properties["name"]

            # Add the relevant properties
            result = node.properties
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
        with open("test.html", "r") as f:
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

if __name__ == "__main__":
    cherrypy.quickstart(App())
