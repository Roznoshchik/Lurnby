FROM python:3

# Install requirements
RUN apt-get update
RUN apt-get -y install curl
RUN curl -sL https://deb.nodesource.com/setup_11.x | bash -
RUN apt install nodejs
RUN npm install
RUN pip install --upgrade pip
RUN apt-get install -y git

# Clone ReadabiliPy and install python packages
RUN git clone https://github.com/alan-turing-institute/ReadabiliPy
WORKDIR "/ReadabiliPy"
RUN git pull
RUN pip install -r requirements-dev.txt

# Run the benchmarks with Pytest
CMD pytest --benchmark-only
