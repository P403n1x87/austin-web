<p align="center">
  <br>
  <img width="320px" src="art/logo.png" alt="Austin Web">
  <br>
</p>

<h3 align="center">A Modern Web Interface for Austin</h3>

<p align="center">
  <a href="https://github.com/P403n1x87/austin-web/actions?workflow=Tests">
    <img src="https://github.com/P403n1x87/austin-web/workflows/Tests/badge.svg"
         alt="GitHub Actions: Tests">
  </a>
  <a href="https://travis-ci.com/P403n1x87/austin-web">
    <img src="https://travis-ci.com/P403n1x87/austin-web.svg?token=fzW2yzQyjwys4tWf9anS"
         alt="Travis CI">
  </a>
  <a href="https://codecov.io/gh/P403n1x87/austin-web">
    <img src="https://codecov.io/gh/P403n1x87/austin-web/branch/master/graph/badge.svg"
         alt="Codecov">
  </a>
  <a href="https://pypi.org/project/austin-web/">
    <img src="https://img.shields.io/pypi/v/austin-web.svg"
         alt="PyPI">
  </a>
  <!-- <a href="https://austin-web.readthedocs.io/">
    <img src="https://readthedocs.org/projects/austin-web/badge/"
         alt="Documentation">
  </a> -->
  <a href="https://github.com/P403n1x87/austin-web/blob/master/LICENSE.md">
    <img src="https://img.shields.io/badge/license-GPLv3-ff69b4.svg"
         alt="LICENSE">
  </a>
</p>

<p align="center">
  <a href="#synopsis"><b>Synopsis</b></a>&nbsp;&bull;
  <a href="#installation"><b>Installation</b></a>&nbsp;&bull;
  <a href="#usage"><b>Usage</b></a>&nbsp;&bull;
  <a href="#compatibility"><b>Compatibility</b></a>&nbsp;&bull;
  <!-- <a href="#documentation"><b>Documentation</b></a>&nbsp;&bull; -->
  <a href="#contribute"><b>Contribute</b></a>
</p>


# Synopsis

Austin Web is a modern web interface for Austin, based on
[D3.js](https://d3js.org/) and [tailwindcss](https://tailwindcss.com/). It is
yet another example of how to use Austin to make a visual profiling tool for
Python. The flame graph is generated using
[d3-flame-graph](https://github.com/spiermar/d3-flame-graph).

Austin Web offers two main functionalities. The default one is to serve a web
page that allows you to have a live view of the metrics collected by Austin. The
visualisation is a _live_ flame graph in your browser that refreshes every 3
seconds with newly collected data. Hence, Austin Web can also be used for
_remote_ profiling.

You can also run Austin Web in _compile_ mode to generate a static flame graph
HTML page, much like
[flamegraph.pl](https://github.com/brendangregg/FlameGraph), but with the full
Austin Web UI around it.


# Installation

If you want to give it a go you can install it using `pip` with

~~~ bash
pip install austin-web
~~~

> **NOTE** Austin Web relies on the
> [Austin](https://github.com/P403n1x87/austin) binary being available from the
> `PATH` environment variable. So make sure that Austin is properly installed on
> your system.


# Usage

You can run Austin Web simply with

~~~ bash
austin-web [OPTION...] command [ARG...]
~~~

to start serving on localhost over an ephemeral port. If you want to specify the
host and the port, you can pass the `--host` and `--port` options to the command
line.

If you want to compile the collected metrics into a static HTML page, you can
run Austin Web in compile mode by passing the `--compile` option, followed by
the destination file name, e.g.

~~~ bash
austin-web --compile output.html python3 myscript.py
~~~

<p align="center"><img src="art/austin-web.gif" style="box-shadow: #111 0px 0px 16px;"/></p>


# Contribute

If you want to help with the development, then have a look at the open issues
and have a look at the [contributing guidelines](CONTRIBUTING.md) before you
open a pull request.

You can also contribute by becoming a Sponsor :).
