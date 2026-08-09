CXX ?= g++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -pedantic
CXXFLAGS += -I/usr/include
LDFLAGS ?= -pthread
LDFLAGS += -lmosquitto

TARGET := test_epoll

MAIN_SERVER_MAIN := ../backend/src/main.cpp
SERVER_SRC := ../backend/src/server/MainServer.cpp
REPO_SRC := ../backend/src/repository/RedisCacheRepository.cpp
NETWORK_SRC := ../backend/src/network/PseudoClient.cpp
TEST_SRC := client/tests_epoll.cpp

SRCS := $(SERVER_SRC) $(REPO_SRC) $(NETWORK_SRC) $(TEST_SRC)
MAIN_SERVER_SRCS := $(MAIN_SERVER_MAIN) $(SERVER_SRC) $(REPO_SRC)

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
#   make run-py inter_server_test
PY_TEST_GOAL := $(filter-out run-py,$(filter %_test,$(MAKECMDGOALS)))
PY_TEST_FILE := $(firstword $(wildcard */$(PY_TEST_GOAL).py))
PY_TEST_MODULE := $(patsubst %.py,%,$(subst /,.,$(PY_TEST_FILE)))

.PHONY: all build run clean run-py test-sensor test-mqtt test-inter-server test-python

all: build

build: $(TARGET)

main_server: $(MAIN_SERVER_SRCS)
	$(CXX) $(CXXFLAGS) $(MAIN_SERVER_SRCS) -o main_server $(LDFLAGS)

$(TARGET): $(SRCS)
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
	./$(TARGET)

run_main_server: main_server
	./main_server

clean:
	rm -f $(TARGET)
	rm -f mqtt/run_main_server
	rm -f main_server
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Run a single Python test file independently, e.g.:
#   make test-sensor
#   make test-mqtt
test-sensor:
	PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest sensor.sensor_test -v

test-mqtt:
	PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest sensor_server.mqtt_test -v

test-inter-server:
	$(MAKE) main_server
	PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest sensor_server.inter_server_test -v

# Run every Python test file in this directory.
test-python: main_server
	PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest discover -s . -p "*_test.py" -v

# Preferred Python test entry point.
# - `make run-py` runs all Python tests under test/
# - `make run-py sensor_test` runs test/sensor/sensor_test.py
# - `make run-py mqtt_test` runs test/sensor_server/mqtt_test.py
run-py:
	@if [ -z "$(PY_TEST_GOAL)" ] || [ "$(PY_TEST_GOAL)" = "inter_server_test" ]; then \
		$(MAKE) main_server; \
	fi
	@if [ -n "$(PY_TEST_GOAL)" ]; then \
		PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest $(PY_TEST_MODULE) -v; \
	else \
		PYTHONPATH=$(PYTHON_ROOT) $(PYTHON) -m unittest discover -s . -p "*_test.py" -v; \
	fi

%_test:
	@: