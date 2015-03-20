/* State */
var currentNodes = [null, null];
var currentEdges= [];
var currentShortest = [];
var globalGraph;
var globalAdjacencyTable;
var gDataEncoding;

/* Presets */
var userPropNames = ["ip", "cityName", "locationCode", "country", "latitude", "longitude", "type"];
var topicPropNames = ["name", "type"];

/* Dijkstras */
function makeAdjacencyTable(graph) {
  var byRef = {};
  graph.nodes.forEach(function(d, i){
    byRef[i] = [];
  })
  graph.links.forEach(function(l){
    /* Lookup lets us map to the index of the node in the nodes array directly,
       which gives us a faster lookup.
    */
    byRef[graph.lookup[l.source.id]].push(graph.lookup[l.target.id]);
    byRef[graph.lookup[l.target.id]].push(graph.lookup[l.source.id]);
  })
  return byRef;
}

function findShortestPath(graph, adjacencyTable, source, target){
  // Clone an intital array to visit
  var sourceId = source.neo4j_node_id;
  var toVisit = adjacencyTable[graph.lookup[sourceId]].slice(0);

  // Make an array of visited nodes
  var visited = graph.nodes.map(function(){return null});
  visited[graph.lookup[sourceId]] = [0, [graph.lookup[sourceId]]];
  var vNum;
  while(typeof (vNum = toVisit.pop()) != "undefined"){
    var minVal = Number.POSITIVE_INFINITY;
    var minPath = [];
    // Check if neighbors have been visited
    adjacencyTable[vNum].forEach(function(neighbor){
      var neighborPath;
      if((neighborPath = visited[neighbor]) != null){
        minVal = Math.min(neighborPath[0], minVal);
        // Set the path to the minimum neighbor path
        if (minVal == neighborPath[0]){
          minPath = neighborPath[1].slice(0);
        }
      }
      else{
        toVisit.push(neighbor);
      }
    });
    minPath.push(vNum);
    visited[vNum] = [minVal + 1, minPath];

    // If we've just found the value for the target node, stop and report
    if(vNum == graph.lookup[target.neo4j_node_id]){
      return visited[vNum];
    }
  }
}

/* Selection functions */
function setSelected(node, setting, panelId){
  // Set classes for css
  d3.select("#n" + node.neo4j_node_id.toString()).classed("selected", setting);
  d3.select("#n" + node.neo4j_node_id.toString()).classed("fixed", node.fixed = setting);

  // Fill the panels
  if (typeof panelId != "undefined"){
    if (setting){
      showDetail(node, panelId);
    }
    else{
      hideDetail(panelId);
    }
  }
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
  // Set the panel title
  $("#panelh" + panelID.toString()).html(node[props[0]]);

  // Set the panel class based on the type of user
  var panel = $("#paneld" + panelID.toString());
  panel.removeClass("panel-info panel-warning");
  if (node["type"] == "user"){
    panel.addClass("panel-info");
  }
  else {
    panel.addClass("panel-warning");
  }

  // Turn the panel on
  panel.show();
}

function hideDetail(panelID){
  $("#paneld" + panelID.toString()).show();
}

// Operators on Alchemy structures
var removeCurrentNode = function(node){
  if (currentNodes[0] == node){
    setSelected(currentNodes[0], false);
    currentNodes[0] = null;
    $("#lengthBtn").hide();
  }
  else if (currentNodes[1] == node){
    currentNodes[1] = currentNodes[0];
    currentNodes[0] = null;
    $("#lengthBtn").hide();
  }
  // Else do nothing
  return
}
var addCurrentNode = function(n){
  // Do nothing if this is already selected
  if (d3.select("#n" + n.neo4j_node_id.toString()).classed("selected")){
    return;
  }

  /* Highlight this node */
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
  /* Configure CSS */
  setSelected(currentNodes[0], true, 1);
  setSelected(currentNodes[1], true, 2);

  /* Download button */
  // Find the shortest path
  currentShortest = findShortestPath(globalGraph, globalAdjacencyTable, currentNodes[0], currentNodes[1]);

  // Show the button
  var button = $("#lengthBtn");
  // Create document to show shortest path
  var popBox = shortestPopBoxToButton(currentShortest, globalGraph, button);

  $("#lengthBtn").show();

}

function downloadFile(){
  gDataEncoding["maxLength"] = 10;
  var form = $('form[name="download"] input[name="jsonStr"]').val(JSON.stringify(gDataEncoding));
  $(".featherlight").click();
  return true;
};

function shortestPopBoxToButton(path, graph, button){
  /* Get the arithmetic encoding */
  var neo4j_ids = path[1].map(function(nodeId){
    return graph.nodes[nodeId].neo4j_node_id;
  });
  // Ask cherrypy for the arithmetic encoding
  $.ajax({
      type: "POST",
      url: "/encoding",
      data: JSON.stringify(neo4j_ids),
      contentType: "application/json",
      dataType: "json",
      success: function(data){
        var retStr = "";
        var sum = 0.0;
        data.encoding.forEach(function(es){
          // TODO: Need a better fix for this, but the array dereference is because of the way I have to tag things
          es[1].forEach(function(e){
            sum += parseFloat(e);
          })
        })
        retStr += "<h1>" + sum + "</h1>\n";
        // Report the path back
        path = "";
        data.path.slice(0,-1).forEach(function(p){
          path += p[1] + ' <span class="glyphicon glyphicon-arrow-right" aria-hidden="true"></span> ';
        })
        path += data.path[-1];
        retStr += "<p>" + path + "</p>"
        retStr += '<form name="download" method="post" action="/geo" onsubmit="return downloadFile();"><input name="jsonStr" id="geoStr" type="hidden"/>'
        retStr += '<button class="btn btn-danger downloadBtn" type="submit" value="Download"><h4>Download?</h4></button>'
        retStr += '</form>'

        // Configure download data
        gDataEncoding = data;

        // Turn on lightbox
        button.attr("data-featherlight", retStr);
      }
  });
}

function lookupNodeById(nodeID){
  var nodeIndex = globalGraph.lookup[nodeID];
  return globalGraph.nodes[nodeIndex];
}

/* D3 Functions */
var zoomListener = d3.behavior.zoom()
  .scaleExtent([0.5, 2])
  .on("zoom", zoomHandler);

var width = 960,
    height = 500;

var force = d3.layout.force()
    .size([width, height])
    .charge(-400)
    .linkDistance(50)
    .friction(0.85)
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
  // Turn off tooltip
  $("#n" + d.neo4j_node_id).tipsy("hide");
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
      .on("mouseover", function(d){
        $("#n" + d.neo4j_node_id).tipsy("show");
      })
      .on("mouseout", function(d){
        $("#n" + d.neo4j_node_id).tipsy("hide");
      })
      .call(drag);
  $('svg circle').tipsy({
        gravity: 'w',
        html: true,
        trigger: "manual",
        title: function() {
          var d = this.__data__;
          return d.caption;
        }
      });
  globalGraph = graph;
  globalAdjacencyTable = makeAdjacencyTable(graph);
});

function tick() {
  link.attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

  node.attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; });
}
