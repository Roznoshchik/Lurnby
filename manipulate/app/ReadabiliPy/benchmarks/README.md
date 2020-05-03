Benchmarking [ReadabiliPy](https://github.com/alan-turing-institute/ReadabiliPy/tree/master) with containers
====

This directory contains a Dockerfile to build a benchmarking image for [ReadabiliPy](https://github.com/alan-turing-institute/ReadabiliPy/tree/master) as per the guidelines specified by the [Benchmarking with containers](https://alan-turing-institute.github.io/data-science-benchmarking/) project, at the Alan Turing Institute.

**Software:** [ReadabiliPy](https://github.com/alan-turing-institute/ReadabiliPy) - A simple HTML content extractor in Python. Can be run as a wrapper for Mozilla's Readability.js package or in pure-python mode.

**Benchmarks:** Benchmark the speed of core package functions at extracting information from an input HTML with [pytest](https://pypi.org/project/pytest-benchmark/). See [test_benchmarking.py](https://github.com/alan-turing-institute/ReadabiliPy/blob/master/tests/test_benchmarking.py).

Running benchmarks
----

Using the [pytest-benchmark](https://pypi.org/project/pytest-benchmark/) package, we benchmark some of the package functions, including extraction of titles and dates from article HTML and the full article content in JSON format.

Benchmarks can be run from the top directory of the package with the following command: ```pytest --benchmark-only```.

Building a Docker image for Benchmarking ReadabiliPy
----

The [Dockerfile](https://github.com/alan-turing-institute/ReadabiliPy/blob/master/benchmarks/Dockerfile) specifies an image that installs the requirements for ReadabiliPy, clones the package from GitHub, then runs the benchmarks with pytest.

Docker Hub Automated build
----

An image was built with this Dockerfile and pushed to [Docker Hub](https://cloud.docker.com/repository/docker/edwardchalstrey/readabilipy_benchmark) as ```edwardchalstrey/readabilipy_benchmark```. An automated build was set up so that the ```latest``` tag  is built whenever the master branch of the ReadabiliPy GitHub repo has a new commit.

Run the containerised benchmarks
----

The benchmark image can be pulled from the remote registry (Docker Hub), and run on any computing platform with Docker. Benchmarks can be run whenever new features are added.

### Results

I have benchmarked three of the html parsing features of ReadabiliPy on an example html file; see the tests in [ReadabiliPy](https://github.com/alan-turing-institute/ReadabiliPy/tree/master) repo within ```tests/test_benchmarking.py```.

Benchmarks run on these dates, are for the following [ReadabiliPy](https://github.com/alan-turing-institute/ReadabiliPy/tree/master) commits and measure **mean time ms**:
1. 2019-05-02 => [9ba2fdb7...](https://github.com/alan-turing-institute/ReadabiliPy/tree/9ba2fdb71b3b014f3252a29672ff41159203e45c)
2. 2019-05-14 => [d3b3c365...](https://github.com/alan-turing-institute/ReadabiliPy/tree/d3b3c365984aa26ce0a8f0fda6b3fd75b9e837a2)
3. 2019-05-31 => [73493922...](https://github.com/alan-turing-institute/ReadabiliPy/tree/734939221048041e545e3a4bd205a84e87631a3f)

**Benchmarks on a Macbook:**

| Date  | Date parse  | Title parse  | Full parse  |
|---|---|---|---|
| 2019-05-02  | 69.5056  | 55.5296  | 2140.0745  |
| 2019-05-14  | 44.4991  | 54.8936  | 1942.1609  |
| 2019-05-31  | 80.5528  | 94.9283  | 2290.3153  |


**Benchmarks on a Macbook in Docker container:**

| Date  | Date parse  | Title parse  | Full parse  |
|---|---|---|---|
| 2019-05-02  | 46.4389  | 40.2649  | 3065.2467  |
| 2019-05-14  | 32.8276  | 39.7405  | 2642.1735  |
| 2019-05-31  | 34.8774  | 41.2476  | 2838.9681  |
