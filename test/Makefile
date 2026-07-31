CXX ?= g++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -pedantic
LDFLAGS ?= -pthread

TARGET := test_epoll

SERVER_SRC := ../backend/src/server/MainServer.cpp
REPO_SRC := ../backend/src/repository/RedisCacheRepository.cpp
NETWORK_SRC := ../backend/src/network/PseudoClient.cpp
TEST_SRC := client/tests_epoll.cpp

SRCS := $(SERVER_SRC) $(REPO_SRC) $(NETWORK_SRC) $(TEST_SRC)

.PHONY: all build run clean

all: build

build: $(TARGET)

$(TARGET): $(SRCS)
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)
