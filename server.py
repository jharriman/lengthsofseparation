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
from serializers import serializeGraphStream
from arithmetic.compression import ArithmeticEncoder
import geometry

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
        stream = self.getCypherStream("MATCH (n) Return n;")
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
            if "User" in node.labels:
                # TODO! Include ips as part of the encodeable set
                pass
                # namesOnPath.append(node.properties["ip"][0])
            elif "Topic" in node.labels:
                namesOnPath.append(node.properties["name"])
        encodedSet = []
        for name in namesOnPath:
            # TODO! include periods in the dictionary set
            encodedSet.append(self.aenc.encodePhrase(name.replace(".","").replace(":", "")))
        return {"encoding" : encodedSet, "path" : namesOnPath}

    @cherrypy.expose
    def geo(self, jsonStr=None):
        """Compute the OpenSCAD file and serve it as a download"""
        data = json.loads(jsonStr)
        # Unify the sequence
        sequenceSet = []
        for s in data["encoding"]:
            sequenceSet += s
        geoStr = geometry.createConnections(sequenceSet, data["maxLength"])
        # Write the string into a buffer
        buf = StringIO.StringIO()
        buf.write(geoStr)
        buf.seek(0)

        # Change the headers so the file is just downloaded
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="los.scad"'
        return file_generator(buf);


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
