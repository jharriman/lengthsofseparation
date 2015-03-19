from py2neo import neo4j
import py2neo.error

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
    relLookup = {}
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
            # Serialize
            serialRel = serializeRelationship(rel, nodesLookup)
            # Check if rel already exists
            try:
                relLookup[serialRel["source"]]
                continue
            except KeyError:
                relLookup[serialRel["source"]] = serialRel["target"]
                relationships.append(serialRel);
    return {"nodes" : nodes, "links" : relationships, 'lookup' : nodesLookup}
