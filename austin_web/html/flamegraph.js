// ---- Manage the Flame Graph view -------------------------------------------

String.prototype.toHHMMSS = function () {
  var sec_num = parseInt(this, 10); // don't forget the second param
  var hours   = Math.floor(sec_num / 3600);
  var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
  var seconds = sec_num - (hours * 3600) - (minutes * 60);

  if (hours   < 10) {hours   = "0"+hours;}
  if (minutes < 10) {minutes = "0"+minutes;}
  if (seconds < 10) {seconds = "0"+seconds;}
  return hours+':'+minutes+':'+seconds;
}

function esc(text) {
  return text.replace("<", "&lt;").replace(">", "&gt;")
}

function time_label(d, parent) {
  return (
    esc(d.data.name) + " 🕘 " + (d.data.value/1000000).toString().toHHMMSS() +
    " (" + (d.data.value / parent.data.value * 100).toFixed(2) + "%)"
  )
}

function memory_label(d, parent) {
  value = d.data.value < 1024
    ? (d.data.value.toString() + " KB")
    : (d.data.value >> 10).toString() + " MB";

  return (
    esc(d.data.name) + " 📏 " + value +
    " (" + (d.data.value / parent.data.value * 100).toFixed(2) + "%)"
  )
}

var label_map = {"t": time_label, "m": memory_label};

// ----------------------------------------------------------------------------

var flameGraph = d3.flamegraph()
  .height(0)
  .width(document.getElementById('chart').offsetWidth)
  .cellHeight(18)
  .transitionDuration(250)
  .minFrameSize(0)
  .transitionEase(d3.easeCubic)
  .sort(true)
  .title("")
  .label(function (d) {
    var c = ""
    for (var e in d) {c += " " + e;}
    var parent = d;
    try {
      while (parent.parent.parent) {
        parent = parent.parent;
      }
    }
    catch(err) {
      // parent.parent is undefied
    }
    return label(d, parent)
  }
);

flameGraph.setHeight = function (height) {
  flameGraph.height(height * 18);
  d3.select("#chart svg").style("height", height * 18);
}

flameGraph.setWidth = function (width) {
  flameGraph.width(width);
  d3.select("#chart svg").style("width", width);
}

var details = document.getElementById("details");
flameGraph.setDetailsElement(details);

d3.select("#chart")
  .datum(data)
  .call(flameGraph);

document.getElementById("form").addEventListener("submit", function (event) {
  event.preventDefault();
  search();
});

function search() {
  var term = document.getElementById("term").value;
  if (term) {
    flameGraph.search(term);
  }
}

function onSearch() {
  var term = document.getElementById("term").value;
  if (!term) {
    clear();
  }
}

function clear() {
  // document.getElementById('term').value = '';
  flameGraph.clear();
}

function resetZoom() {
  flameGraph.resetZoom();
}

function onresize() {
  flameGraph.setWidth(document.getElementById('chart').offsetWidth);
}
