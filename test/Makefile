CXX ?= g++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -pedantic
CXXFLAGS += -I/usr/include
LDFLAGS ?= -pthread
LDFLAGS += -lmosquitto

TARGET := test_epoll

SERVER_SRC := ../backend/src/server/MainServer.cpp
REPO_SRC := ../backend/src/repository/RedisCacheRepository.cpp
NETWORK_SRC := ../backend/src/network/PseudoClient.cpp
TEST_SRC := client/tests_epoll.cpp

SRCS := $(SERVER_SRC) $(REPO_SRC) $(NETWORK_SRC) $(TEST_SRC)

# Python test setup.
# PYTHON_ROOT is added to PYTHONPATH so `import parking_lot...` resolves;
# override on the command line if your layout differs, e.g.:
#   make test-sensor PYTHON_ROOT=../..
PYTHON ?= python3
PYTHON_ROOT ?= ..

# Usage:
#   make run-py
#   make run-py sensor_test
#   make run-py mqtt_test
PY_TEST_GOAL := $(filter-out run-py,$(filter %_test,$(MAKECMDGOALS)))
PY_TEST_FILE := $(firstword $(wildcard */$(PY_TEST_GOAL).py))
PY_TEST_MODULE := $(patsubst %.py,%,$(subst /,.,$(PY_TEST_FILE)))

.PHONY: all build run clean run-py test-sensor test-mqtt test-python

all: build

build: $(TARGET)

$(TARGET): $(SRCS)
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)

# Run a single Python test file independently, e.g.:
#   make test-sensor
#   make test-mqtt
test-sensor:
	PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest sensor.sensor_test -v

test-mqtt:
	PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest sensor_server.mqtt_test -v

# Run every Python test file in this directory.
test-python:
	PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest discover -s . -p "*_test.py" -v

# Preferred Python test entry point.
# - `make run-py` runs all Python tests under test/
# - `make run-py sensor_test` runs test/sensor/sensor_test.py
# - `make run-py mqtt_test` runs test/sensor_server/mqtt_test.py
run-py:
	@if [ -n "$(PY_TEST_GOAL)" ]; then \
		PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest $(PY_TEST_MODULE) -v; \
	else \
		PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest discover -s . -p "*_test.py" -v; \
	fi

%_test:
	@: