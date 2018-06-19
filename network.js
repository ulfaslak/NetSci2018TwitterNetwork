// Network canvas and div
var canvas = document.getElementById("canvas")
var canvas_div = document.getElementsByClassName("canvas_container")[0]
canvas.width = canvas_div.offsetWidth
canvas.height = canvas_div.offsetHeight
context = canvas.getContext("2d")
var canvas_width = canvas.width
var canvas_height = canvas.height

// Brush stuff
var brush_svg = d3.select(document.getElementById("brush"))
var brush_width = document.getElementById("brush").getBoundingClientRect().width
var brush_height = document.getElementById("brush").getBoundingClientRect().height * 1.0

// Retina canvas rendering    
var devicePixelRatio = window.devicePixelRatio || 1
d3.select(canvas)
  .attr("width", canvas_width * devicePixelRatio)
  .attr("height", canvas_height * devicePixelRatio)
  .style("width", canvas_width + "px")
  .style("height", canvas_height + "px").node()
context.scale(devicePixelRatio, devicePixelRatio)

// Network
var simulation = d3.forceSimulation()
  .force("link", d3.forceLink().id(function(d) { return d.id; }))
  .force("charge", d3.forceManyBody())
  .force("center", d3.forceCenter(canvas_width / 2, canvas_height / 2))
  .force("x", d3.forceX(canvas_width / 2))
  .force("y", d3.forceY(canvas_height / 2));

simulation.force("x").strength(0.1);
simulation.force("y").strength(0.1);

tmin = new Date("2018-06-04 00:00:00+00:00")
tmax = new Date("2018-06-20 00:00:00+00:00")


focusLabel = document.getElementById('username').value;
var selection = [parseInt(brush_width * 0.3732), parseInt(brush_width * 0.7479)]

document.getElementById('username').addEventListener('keyup', function() {
  focusLabel = document.getElementById('username').value;
  if (simulation.alpha() < 0.01) {
    simulation.alpha(0.01).restart();
  }

})

function restart(dataset) {
  d3.csv(dataset, function(data){
    
    // Convert links to graph
    var data = data
      .filter(l => tmin < new Date(l.datetime) && new Date(l.datetime) < tmax)
      .map(l => { return {"source": l.source, "target": l.target, "datetime": new Date(l.datetime)}})
    
    graph_daddy = convertToJson(data)
    graph_active = _.clone(graph_daddy)

    simulation
      .nodes(graph_active.nodes)
      .on("tick", ticked);
    
    simulation.force("link")
      .links(graph_active.links);
    
    d3.select(canvas)
      .call(d3.drag()
      .container(canvas)
      .subject(dragsubject)
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended));

    canvas.onmousemove = function(e){
        focusLabel = simulation.find(e.offsetX, e.offsetY).id;
        if (simulation.alpha() < 0.01) {
          simulation.alpha(0.01).restart();
        }
      }
    canvas.onmouseout = function(e){
        focusLabel = document.getElementById('username').value;
      }

    var dates = data.map(d => {return d.datetime})

    x = d3.scaleTime()
      .domain([tmin, tmax])
      .rangeRound([0, brush_width]);

    brush_svg.append("g")

    brush_svg.append("g")
      .attr("class", "axis axis--grid")
      .attr("transform", "translate(0," + brush_height * 0.6 + ")")
      .call(d3.axisBottom(x)
        .ticks(d3.timeHour, 12) // 12
        .tickSize(-brush_height)
        .tickFormat(function() { return null; }))
      .selectAll(".tick")
        .classed("tick--minor", function(d) { return d.getHours(); });

    brush_svg.append("g")
      .attr("class", "axis axis--x")
      .attr("transform", "translate(0," + brush_height * 0.6 + ")")
      .call(d3.axisBottom(x)
        .ticks(d3.timeDay)
        .tickPadding(0))
      .attr("text-anchor", null)
      .selectAll("text")
      .attr("x", 5);

    brush = d3.brushX()
      .extent([[0, 0], [brush_width, brush_height]])
      .on("brush", brushed)

    brush_svg.append("g")
      .call(brush)
      .call(brush.move, selection);

    function ticked() {
      context.clearRect(0, 0, canvas_width, canvas_height);
        
      context.strokeStyle = "#212121";
      context.lineWidth = 2.0;
      context.globalAlpha = 0.3;
      context.globalCompositeOperation = "destination-over"
      graph_active.links.forEach(drawLink);
      
      context.globalAlpha = 1.0
      context.strokeStyle = "white";
      context.lineWidth = 1;
      context.globalCompositeOperation = "source-over"

      graph_active.nodes.forEach(drawNode);
      graph_active.nodes.forEach(drawLabel);
    }
    
    function dragsubject() {
      return simulation.find(d3.event.x, d3.event.y);
    }
  })

  var brush_area = brush_width//(brush_width - 10) - (brush_width / 1.5)
  function brushed() {
    selection = d3.event.selection;
    limits = selection.map(x.invert)
    if ((selection[1] - selection[0]) > brush_area) {
      // brush is expanding, add nodes from graph_daddy
      addLinks(limits); 
    } else if ((selection[1] - selection[0]) < brush_area) {  
      // Brush is shrinking, remove nodes from graph_active
      removeLinks(limits);
    } else {  
      // Area remains constant (panning)
      addLinks(limits);
      removeLinks(limits);
    }
    brush_area = selection[1] - selection[0]
    simulation.alpha(1).restart();
  }

  var playbutton = document.getElementById("playbutton")
  playbutton.onclick = function() {
    // Animate brush movement
    var inc = 0;
    var selection_0 = _.clone(selection)
    var steps = brush_width / 100;
    (function theLoop (i) {
      setTimeout(function () {
        if (inc < 94) {
          brush_svg
            .call(brush)
            .transition().duration(20)
            .call(brush.move, [inc*steps, inc*steps+42]);
        } else if (inc == 94){
          brush_svg
            .call(brush)
            .transition()
            .call(brush.move, selection_0);
        }
        inc += 1;
        if (--i) {          // If i > 0, keep going
          theLoop(i);       // Call the loop again, and pass it the current value of i
        }
      }, 20);
    })(95);
  }
}

restart("https://gist.githubusercontent.com/ulfaslak/2686ebe674b761e7947aacd2780b8384/raw/links_likes.csv")

// Network functions
// -----------------

function dragstarted() {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d3.event.subject.fx = d3.event.subject.x;
  d3.event.subject.fy = d3.event.subject.y;
}

function dragged() {
  d3.event.subject.fx = d3.event.x;
  d3.event.subject.fy = d3.event.y;
}

function dragended() {
  if (!d3.event.active) simulation.alphaTarget(0);
  d3.event.subject.fx = null;
  d3.event.subject.fy = null;
}

function drawLink(d) {
  context.beginPath();
  context.moveTo(d.source.x, d.source.y);
  context.lineTo(d.target.x, d.target.y);
  context.stroke();
}

function drawNode(d) {
  thisnodesize = d.size**(0.5) * 2;
  context.beginPath();
  context.moveTo(d.x + thisnodesize, d.y);
  context.arc(d.x, d.y, thisnodesize, 0, 2 * Math.PI);
  if (d.id.toLowerCase() == focusLabel.toLowerCase()) {
    context.fillStyle = "#2980b9"
  } else {
    context.fillStyle = "black";
  }
  context.fill();
  context.stroke();
}

function drawLabel(d) {
  if (d.id.toLowerCase() == focusLabel.toLowerCase()) {
    thisnodesize = d.size**(0.5) * 2;
    context.beginPath();
    context.rect(d.x, d.y - 30, d.id.length*12, 25);
    context.fillStyle = "white";
    context.fill()
    context.stroke()
    context.beginPath()
    context.fillStyle = "black";
    context.font = "20px Georgia";
    context.moveTo(d.x+10, d.y-10);
    context.fillText(d.id, d.x+10, d.y-10);
    context.stroke();
  }
}

// Brush functions
// ---------------

function addLinks(limits) {
  var active_nodes = []
    graph_daddy.links
      .filter(l => (limits[0] < l.datetime && l.datetime < limits[1]))
      .forEach((l, i) => {
        if (!hasLink(graph_active.links, l)) {
          graph_active.links.push(l)
        }
        active_nodes.push(l.target.id);
      })
    active_nodes = Counter(active_nodes)

    var current_nodes = graph_active.nodes.map(n => {return n.id})
    d3.keys(active_nodes).forEach(n => {
      if (current_nodes.includes(n)) {
        var i = findNode(graph_active.nodes, n)
        graph_active.nodes[i]['size'] = active_nodes[n] | 1
      } else {
        var i = findNode(graph_daddy.nodes, n)
        n_daddy = graph_daddy.nodes[i]
        n_daddy['size'] = active_nodes[n] | 1
        graph_active.nodes.push(n_daddy)
      }
    })
}

function removeLinks(limits) {
  graph_active.links = graph_active.links.filter(l => (limits[0] < l.datetime && l.datetime < limits[1]) )

    var active_nodes = []
    graph_active.links.forEach(l => { active_nodes.push(l.target.id); })
    active_nodes = Counter(active_nodes)

    graph_active.nodes = graph_active.nodes.filter(n => n.id in active_nodes)
    graph_active.nodes.forEach((n, i) => { graph_active.nodes[i]['size'] = active_nodes[n.id] | 1})
}

function convertToJson(links) {
  var nodes = []
  var nodes_in_degree = []
  links.forEach(l => {
  	nodes.push(l.source)
  	nodes.push(l.target)
  	nodes_in_degree.push(l.target)
  });
  var nodes = Array.from(new Set(nodes))
  var nodes_in_degree = Counter(nodes_in_degree)

  var graph = {'nodes': [], 'links': links}
  nodes.forEach(k => {graph.nodes.push({'id': k, 'size': nodes_in_degree[k] | 1})})
  return graph;
}

function Counter(array) {
  var count = {};
  array.forEach(val => count[val] = (count[val] || 0) + 1);
  return count;
}

function hasLink(links, link) {
  for (l of links) {
    if (l.source == link.source && l.target == link.target && l.datetime == link.datetime) {
      return true;
    }
  }
  return false;
}

function findNode(nodes, node) {
  for (i of d3.range(nodes.length)) {
    if (nodes[i].id == node) return i
  }
}

function getNodeFromLinks(links, node) {
  for (l of links) {
    if (l.source.id == node.id) {
      return l.source
    } else if (l.target.id == node.id) {
      return l.target
    }
  }
}

function toggleActive(e) {
  if (e.getAttribute("class") != "btnActive") {
    if (e.getAttribute("class") == "btn") {
      e.setAttribute("class", "btnActive")
      for (id of ["likes", "retweets", "mentions"]) {
        if (id != e.getAttribute("id")) {
          document.getElementById(id).setAttribute("class", "btn")
        }
      }
    }
    document.getElementById("brush").innerHTML = ''
    restart("https://gist.githubusercontent.com/ulfaslak/2686ebe674b761e7947aacd2780b8384/raw/links_" + e.getAttribute("id") + ".csv")
  }

}


Date.prototype.addHours = function(h){
    this.setHours(this.getHours()+h);
    return this;
}