// State
var currentNodes = [null, null];
var currentEdges= [];
var globalGraph;

function setSelected(node, setting, panelId){
  d3.select("#n" + node.neo4j_node_id.toString()).classed("selected", setting);
  d3.select("#n" + node.neo4j_node_id.toString()).classed("fixed", node.fixed = setting);
  // Fill the panel
  if (typeof panelId != "undefined"){
    showDetail(node, panelId);
  }
}

// Operators on Alchemy structures
var removeCurrentNode = function(node){
  if (currentNodes[0] == node){
    setSelected(currentNodes[0], false);
    currentNodes[0] = null;
  }
  else if (currentNodes[1] == node){
    currentNodes[1] = currentNodes[0];
    currentNodes[0] = null;
  }
  // Else do nothing
  return
}
var addCurrentNode = function(n){
  // Do nothing if this is already selected
  if (d3.select("#n" + n.neo4j_node_id.toString()).classed("selected")){
    return;
  }

  // Highlight this node
  if(currentNodes[0] == null){
    currentNodes[0] = n;
    setSelected(currentNodes[0], true, 1);
    return;
  }
  else if (currentNodes[1] == null){
    currentNodes[1] = currentNodes[0];
    currentNodes[0] = n;
  }
  else {
    // Remove the current node and replace
    setSelected(currentNodes[1], false);
    currentNodes[1] = currentNodes[0];
    currentNodes[0] = n;
  }
  // Set updates
  setSelected(currentNodes[0], true, 1);
  setSelected(currentNodes[1], true, 2);

  // Now that the nodes have been selected, highlight the edge of the shortest path between them
  // var id0 = currentNodes[0].getProperties().neo4j_node_id;
  // var id1 = currentNodes[1].getProperties().neo4j_node_id;
  // findPath(id0, id1);

}

var userPropNames = ["ip", "cityName", "locationCode", "latitude", "longitude", "type"];
var topicPropNames = ["name", "type"];

function lookupNodeById(nodeID){
  var nodeIndex = globalGraph.lookup[nodeID];
  return globalGraph.nodes[nodeIndex];
}
function showDetail(node, panelID){
  // Grab the table body element
  var t = $("table#panel" + panelID.toString() + " tbody").empty();
  if (node["type"] == "user"){
    var props = userPropNames
  }
  else{
    var props = topicPropNames
  }
  props.forEach(function(propName){
    $("<tr><td class='movie'>" + propName + "</td><td>" + node[propName] + "</td></tr>").appendTo(t);
  });
  $("#panelh" + panelID.toString()).html(node[props[0]]);
}

// Zoom listener
var zoomListener = d3.behavior.zoom()
  .scaleExtent([0.5, 2])
  .on("zoom", zoomHandler);

var width = 960,
    height = 500;

var force = d3.layout.force()
    .size([width, height])
    .charge(-400)
    .linkDistance(50)
    .friction(0.9)
    .on("tick", tick);

var drag = force.drag()
    .on("dragstart", dragstarted)
    .on("drag", dragged)
    .on("dragend", dragended);

var plotDrag = d3.behavior.drag()
    .origin(function(d) { return d; })
    .on("dragstart", dragstarted)
    .on("drag", dragged)
    .on("dragend", dragended);

var svg = d3.select("#graph").append("svg")
    .on()
  .append("g")

var rect = svg.append("rect")
    .attr("width", "100%")
    .attr("height", "100%")
    .style("fill", "none")
    .style("pointer-events", "all");

function dragstarted(d) {
  d3.event.sourceEvent.stopPropagation();
  // Make fixed
  d3.select(this).classed("fixed", d.fixed = true);

  // Update path pool
  addCurrentNode(d);

  d3.select(this).classed("dragging", true);
}

function dragged(d) {
  // Scale dragging down as you increase in scale level
  d3.select(this).attr("cx", d.x = d3.event.x).attr("cy", d.y = d3.event.y);
}

function dragended(d) {
  d3.select(this).classed("dragging", false);
}

var container = svg.append("g");

function zoomHandler() {
  var translate = d3.event.translate.map(function(x){ return parseInt(x * zoomListener.scale());});
  container.attr("transform", "translate(" + translate  + ")scale(" + d3.event.scale + ")");
}
zoomListener(rect);

var link = container.selectAll(".link"),
    node = container.selectAll(".node");

d3.json("/graph", function(error, graph) {
  force
      .nodes(graph.nodes)
      .links(graph.links)
      .start();

  link = link.data(graph.links)
    .enter().append("line")
      .attr("class", "link");

  node = node.data(graph.nodes)
    .enter().append("circle")
      .attr("class", function(d, i){
        return "node " + d.type;
      })
      .attr("id", function(d, i){
        return "n" + d.neo4j_node_id;
      })
      .attr("r", 12)
      .call(drag);
  globalGraph = graph;
});

function tick() {
  link.attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

  node.attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; });
}

// function dblclick(d) {
//   d3.select(this).classed("fixed", d.fixed = false);
// }
