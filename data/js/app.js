// Node state functions
var stateOn = function(obj){
  if (obj && obj._state != "hidden"){
    console.log(obj);
    obj._state = "selected";
    console.log(obj);
    console.log(obj._state);

    // Set Styles
    obj._setD3Properties(obj.a.svgStyles.edge.update(obj));
    obj.a._drawEdges.updateEdge(obj._d3);
  }
}

var stateOff = function(obj){
  if (obj && obj._state != "hidden"){
    obj._state = "active";
    // Set Styles
    obj._setD3Properties(obj.a.svgStyles.edge.update(obj));
    obj.a._drawEdges.updateEdge(obj._d3);
  }
}

// State
var currentNodes = [null, null];
var currentEdges= [];

// Operators on Alchemy structures
var removeCurrentNode = function(node){
  if (currentNodes[0] == node){
    currentNodes[0] = null;
  }
  else if (currentNodes[1] == node){
    currentNodes[1] = currentNodes[0];
    currentNodes[0] = null;
  }
  // Else do nothing
  return
}
var addCurrentNode = function(node){
  if(currentNodes[0] == null){
    currentNodes[0] = node;
    return;
  }
  else if (currentNodes[1] == null){
    currentNodes[1] = currentNodes[0];
    currentNodes[0] = node;
  }
  // Remove highlight if something outside of our buffer is selected.
  else {
    // Remove highlight from currentNode[1] since it will be removed from the buffer
    stateOff(currentNodes[1]);
    currentNodes[1].setStyles();

    // Remove the current node and replace
    currentNodes[1] = currentNodes[0];
    currentNodes[0] = node;
  }
  // Now that the nodes have been selected, highlight the edge of the shortest path between them
  var id0 = currentNodes[0].getProperties().neo4j_node_id;
  var id1 = currentNodes[1].getProperties().neo4j_node_id;
  findPath(id0, id1);

}
var checkState = function(node){
    // Add the node to currently selected queue
    if (node._state == "highlighted"){
      addCurrentNode(node);
    }
    else {
      removeCurrentNode(node);
    }
    console.log(currentNodes);
}

var flipEdgeState = function(edge){
  if (edge._state != "hidden"){
    edge._state = edge._state == "active"? "selected" : "active";
    edge.setStyles();
  }
}

// Queries against Neo4j through Cherrypy
var findPath = function(fr, to){
  var urlString = ["", "path", fr.toString(), to.toString()].join("/");
  $.get(urlString, function(data){
    var edges = JSON.parse(data);
    highlightEdges(edges);
  });
}

var refresh = function(){
  console.log("REFRESH!")
  currentEdges.map(stateOn);
  currentNodes.map(stateOn);
}

var config = {
        dataSource: "/graph",
        nodeClick: checkState,
        forceLocked: false,
        alpha: 0.00000000000001,
        linkDistance: 40,
        friction: 0.1,
        nodeTypes: {"type" : ["user", "topic"]},
        nodeStyle:{
          "all" : {
            color : "#00FF00"
          },
          "user" : {
            color : "#FF0000",
            selected: {
              "color": "#ffffff",
            },
            highlighted: {
              "color": "#b4dcff"
            }
          },
          "topic" : {
            color : "#0000FF",
            selected: {
              "color": "#ffffff",
            },
            highlighted: {
              "color": "#b4dcff"
            }
          }
        },
        edgeMouseOver : function(){},
        deselectAll: refresh
      };
alchemy = new Alchemy(config);

var highlightEdges = function(edges){
  // If we already have edges, deactivate them
  currentEdges.map(stateOff);

  // Convert to JSON from server string
  currentEdges = []
  edges.map(function(edge){
    var graphEdges = alchemy.get.edges(edge.source, edge.target);
    try{
      var e = graphEdges.getEdges(edge.source, edge.target)[0];
    }
    catch(err){
      try{
        var e = graphEdges.getEdges(edge.target, edge.source)[0];
      }
      catch(err) {
        return;
      }
    }
    stateOn(e);
    currentEdges[currentEdges.length] = e;
  });
}
