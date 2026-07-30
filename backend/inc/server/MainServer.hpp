#pragma once
#include <memory>
#include <string>

#include <sys/epoll.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>

#define SERVER_PORT 5000

namespace parkpulse {

class IParkingRepository;
class ICacheRepository;

class MainServer {
public:
    MainServer(int port = SERVER_PORT);
    ~MainServer();

    void start();
    void stop();

private:
    void setupSocket();
    void run();
    void acceptClient();
    void receiveMessage(int client_fd);

private:
    std::unique_ptr<ICacheRepository> cache_repository_;

    int port_ = SERVER_PORT;
    int server_fd_;
    int epoll_fd_;
};

} // namespace parkpulse
