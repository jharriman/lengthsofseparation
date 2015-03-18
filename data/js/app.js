// Zoom listener
var zoomListener = d3.behavior.zoom()
  .scaleExtent([0.5, 2])
  .on("zoom", zoomHandler);

var width = 960,
    height = 500;

var force = d3.layout.force()
    .size([width, height])
    .charge(-400)
    .linkDistance(40)
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

var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height)
    .on()
  .append("g")

var rect = svg.append("rect")
    .attr("width", "100%")
    .attr("height", "100%")
    .style("fill", "none")
    .style("pointer-events", "all");

function dragstarted(d) {
  d3.event.sourceEvent.stopPropagation();
  d3.select(this).classed("fixed", d.fixed = true);
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
        return "node " + d.type
      })
      .attr("r", 12)
      .on("dblclick", dblclick)
      .call(drag);
});

function tick() {
  link.attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

  node.attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; });
}

function dblclick(d) {
  d3.select(this).classed("fixed", d.fixed = false);
}
