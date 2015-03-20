## Built-ins ##
###############
import json
import StringIO

## Third-Party ##
#################
import cherrypy
from cherrypy.lib import file_generator
import jinja2
from py2neo import neo4j
import py2neo.error


## In-project ##
################
from serializers import serializeGraphStream, serializeGraphStreamList
from core.compression import ArithmeticEncoder
import core.geometry

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
    def __init__(self, useWordList=True):
        super(App, self).__init__()
        # Choose whether or not to use the whole English word list, or just use the input from the database.
        if useWordList:
            # Feed in data to the Arithmetic Encoder
            with open("data/words/English_word_list.txt", "r") as f:
                lines = f.readlines()
                self.aenc = ArithmeticEncoder(lines)
        else:
            self.databaseList = self.makeEncodingList()
            self.aenc = ArithmeticEncoder(self.databaseList)
        self.path = Path()
        self.graph = Graph()

    def makeEncodingList(self):
        stream = self.getCypherStream("MATCH (n) RETURN n")
        wordList = set()
        for i in stream:
            node = i.n
            if "Topic" in node.labels:
                wordList.update(node.properties["name"].split())
            elif "User" in node.labels:
                wordList.add(node.properties["ip"][0])
        return list(wordList)


    @cherrypy.expose
    def index(self):
        return wrapHtml("index.html", "templates")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def encoding(self):
        path = cherrypy.request.json
        # Lookup titles
        namesOnPath = []
        for i in path:
            node = self.neo.node(i)
            # Append the country of the user
            if "User" in node.labels:
                cityName = node.properties["cityName"] if node.properties["cityName"] else ""
                country = node.properties["country"] if node.properties["country"] else ""
                namesOnPath.append([1, " ".join([cityName, country])])
            elif "Topic" in node.labels:
                namesOnPath.append([0,node.properties["name"]])
        encodedSet = []
        for nameTagSet in namesOnPath:
            tag = nameTagSet[0]
            name = nameTagSet[1]
            encodedSet.append([tag, self.aenc.encodePhrase(name.replace(".","").replace(":", ""))])
        return {"encoding" : encodedSet, "path" : namesOnPath}

    @cherrypy.expose
    def geo(self, jsonStr=None):
        """Compute the OpenSCAD file and serve it as a download"""
        data = json.loads(jsonStr)
        # Unify the sequence
        sequenceSet = []
        for s in data["encoding"]:
            sequenceSet.extend([[s[0],x] for x in s[1]])
        geoStr = core.geometry.createConnections(sequenceSet, data["maxLength"])
        # Write the string into a buffer
        buf = StringIO.StringIO()
        buf.write(geoStr)
        buf.seek(0)

        # Change the headers so the file is just downloaded
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="los.scad"'
        return file_generator(buf);


def getMostConnectedTopics(stream):
    nodes = []
    for i in stream:
        node = getattr(i, "n")
        nodes.append(int(node.ref.split("/")[1]))
    return nodes

class Graph(CypherSender):
    @cherrypy.expose
    def index(self):
        # Find the most connected Topics
        query = "MATCH (x)-[r]->(n) RETURN n, COUNT(r) ORDER BY COUNT(r) DESC LIMIT 10"
        stream = self.getCypherStream(query)
        mostConnectedTopics = getMostConnectedTopics(stream)

        # Get the nodes connected to the most connected nodes and everything
        # they are connected to.
        streams = []
        for refNum in mostConnectedTopics:
            query = "MATCH (a)-[r:EDITED*1..2]-(d) WHERE id(d)=%d RETURN a,r,d LIMIT 100" % (refNum)
            streams.append(self.getCypherStream(query))
        # query = "MATCH (a:User)-[d:EDITED]->(b:Topic) WITH a,d,b,count(d) as connections RETURN a,d,b ORDER BY connections DESC LIMIT %s" % ("1000")
        # graph = serializeGraphStream(stream, list("ab"), list("d"))
        # Serialize all the streams
        graph = serializeGraphStreamList(streams, list("ad"), list("r"))
        stream.close()
        return json.dumps(graph)

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
import os.path
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
        },
        "/fonts" : {
            "tools.staticdir.on" : True,
            "tools.staticdir.dir" : os.path.join(current_dir, 'data/fonts')
        }
      }
    with open("conf/server.conf", "r") as f:
        cherrypy.quickstart(App(useWordList=False), config=conf)
