// ---- Manage the Flame Graph view -------------------------------------------

const CELL_HEIGHT = 24;

String.prototype.toHHMMSS = function () {
  var sec_num = parseInt(this, 10); // don't forget the second param
  var hours = Math.floor(sec_num / 3600);
  var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
  var seconds = sec_num - (hours * 3600) - (minutes * 60);

  if (hours < 10) { hours = "0" + hours; }
  if (minutes < 10) { minutes = "0" + minutes; }
  if (seconds < 10) { seconds = "0" + seconds; }
  return hours + ':' + minutes + ':' + seconds;
}


function hslToHex(h, s, l) {
  l /= 100;
  const a = s * Math.min(l, 1 - l) / 100;
  const f = n => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, '0');   // convert to Hex and prefix "0" if needed
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}


var hash = function (text) {
  var hash = 0;
  for (var i = 0; i < text.length; i++) {
    hash = text.charCodeAt(i) + ((hash << 5) - hash);
  }
  return hash;
};

var stringToColour = function (data, highlight = false) {
  let name = data.name;
  let scope = data.data.name;
  let module = data.data.file;

  if (!module) {
    return hslToHex(0, 10, highlight ? 90 : 70);
  }

  if (!scope) {
    scope = name;
  }

  var sat = hash(scope) % 20;
  var hue;
  switch (scope.charAt(0)) {
    case 'P':
      hue = 120;
      break;
    case 'T':
      hue = 240;
      break;
    default:
      let h = hash(module) % 360;
      let s = hash(scope) % 10;
      let isPy = module.endsWith(".py");
      return hslToHex(h >= 0 ? h : -h, (isPy ? 60 : 20) + s, highlight ? 80 : 60);
  }

  return hslToHex(hue, 0 + sat, highlight ? 90 : 70);
};


function esc(text) {
  return text.replace("<", "&lt;").replace(">", "&gt;")
}

function time_label(d, parent) {
  return (
    esc(d.data.name) + " 🕘 " + d.data.value.toString() +
    " μs (" + (d.data.value / parent.data.value * 100).toFixed(2) + "%)" +
    (d.data.data.file ? " in " + d.data.data.file : "")
  );
}

function memory_label(d, parent) {
  value = d.data.value < 1024
    ? (d.data.value.toString() + " KB")
    : (d.data.value >> 10).toString() + " MB";

  return (
    esc(d.data.name) + " 📏 " + value +
    " (" + (d.data.value / parent.data.value * 100).toFixed(2) + "%)" +
    (d.data.data.file ? " in " + d.data.data.file : "")
  )
}

var label_map = { "t": time_label, "m": memory_label };

// ----------------------------------------------------------------------------

var flameGraph = d3.flamegraph()
  .height(0)
  .width(document.getElementById('chart').offsetWidth)
  .cellHeight(CELL_HEIGHT)
  .inverted(true)
  .transitionDuration(250)
  .minFrameSize(0)
  .transitionEase(d3.easeCubic)
  .title("")
  .label(function (d) {
    var c = ""
    for (var e in d) { c += " " + e; }
    var parent = d;
    try {
      while (parent.parent.parent) {
        parent = parent.parent;
      }
    }
    catch (err) {
      // parent.parent is undefied
    }
    return label(d, parent)
  }
  );

flameGraph.setHeight = function (height) {
  flameGraph.height(height * CELL_HEIGHT);
  d3.select("#chart svg").style("height", height * CELL_HEIGHT);
}

flameGraph.setWidth = function (width) {
  flameGraph.width(width);
  d3.select("#chart svg").style("width", width);
}

flameGraph.setColorMapper(function (d, originalColor) {
  if (!isNaN(+d.data.name)) {
    return '#808080';
  }
  // return stringToColour(d.data.name, d.highlight);
  return d.highlight ? "#F620F6" : stringToColour(d.data);
});

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
