import json
import cherrypy
import jinja2
from py2neo import neo4j
import py2neo.error

import os.path
current_dir = os.path.dirname(os.path.abspath(__file__))

class UnknownNodeException(Exception):
    pass

def serializeRelationship(rel, nodes):
    # Convert neo4j tag to index in list
    start = int(rel.start_node.ref.split("/")[1])
    end = int(rel.end_node.ref.split("/")[1])

    # Source, target, caption
    source, target, caption = nodes[start], nodes[end], rel.type
    return {"source" : source, "target" : target, "caption" : caption}

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
    # Convert node list to an OrderedDict for easy lookup in relationship serialization
    nodesLookup = {}
    for index, item in enumerate(nodes):
        nodesLookup[item["refNum"]] = index
    for i in sg.relationships:
        # Source, target, caption
        relationships.append(serializeRelationship(rel, nodesLookup))
    return {"nodes" : nodes, "links" : edges}

def serializeGraphStream(stream, nodeLabels, relationshipLabels):
    nodes = []
    nodesLookup = {}
    relationships = []
    count = 0
    for i in stream:
        for label in nodeLabels:
            node = getattr(i, label)

            # Get the ref number
            refNum = int(node.ref.split("/")[1])

            # Avoid duplicating nodes in the JSON file if they already exist
            try:
                nodesLookup[refNum]
                continue
            except KeyError:
                pass

            # Get the properties and update the result
            result = node.properties
            result.update({"neo4j_node_id" : refNum})

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

            # Store node in lookup table
            nodesLookup[refNum] = count
            count += 1
        for label in relationshipLabels:
            rel = getattr(i, label)
            # Source, target, caption
            relationships.append(serializeRelationship(rel, nodesLookup))
    return {"nodes" : nodes, "links" : relationships}

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

class Graph(CypherSender):
    @cherrypy.expose
    def index(self):
        query = "MATCH (a:User)-[d:EDITED]->(b:Topic)<-[e:EDITED]-(c:User) RETURN a,b,c,d,e LIMIT %s" % ("100")
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
