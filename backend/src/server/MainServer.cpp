#include "../../inc/network/GateServer.hpp"
#include "../../inc/network/SensorMqttClient.hpp"
#include "../../inc/server/MainServer.hpp"
#include "../repository/SqlParkingRepository.hpp"
#include "../repository/RedisCacheRepository.hpp"
#include "../../inc/models/Dto.hpp"

#include <iostream>
#include <stdexcept>

#define SQL_CONNECTION_STRING "host=localhost dbname=parkpulse"
#define REDIS_HOST "localhost"
#define REDIS_PORT 6379
#define MQTT_BROKER_HOST "localhost"
#define MQTT_BROKER_PORT 1883

namespace parkpulse {

MainServer::MainServer(int port) 
    : port_(port)
{

}

MainServer::~MainServer()
{ 
    stop(); 
}

void MainServer::start() 
{
    const std::string sql_connection_string = SQL_CONNECTION_STRING;
    const std::string redis_host = REDIS_HOST;
    const int redis_port = REDIS_PORT;

    cache_repository_ = std::make_unique<RedisCacheRepository>(redis_host, redis_port);

    setupSocket();
    run();

    std::cout << "ParkPulse main_server running. Ctrl+C to stop.\n";
}

void MainServer::stop() 
{
    close(server_fd_);
    close(epoll_fd_);
}

// Private methods
void MainServer::setupSocket() 
{
    server_fd_ = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(server_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port_);
    addr.sin_addr.s_addr = INADDR_ANY;

    bind(server_fd_, (sockaddr*)&addr, sizeof(addr));
    listen(server_fd_, SOMAXCONN);

    // non blocking socket
    fcntl(server_fd_, F_SETFL, O_NONBLOCK);

    epoll_fd_ = epoll_create1(0);

    epoll_event event{};
    event.events = EPOLLIN;
    event.data.fd = server_fd_;

    epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, server_fd_, &event);
}

void MainServer::run() 
{
    epoll_event events[10];

    while (true) {
        int count = epoll_wait(epoll_fd_, events, 10, -1);

        for (int i = 0; i < count; i++) {

            int fd = events[i].data.fd;

            if (fd == server_fd_) {
                acceptClient();
            }
            else {
                receiveMessage(fd);
            }
        }
    }
}

void MainServer::acceptClient() 
{
    sockaddr_in client{};
    socklen_t size = sizeof(client);

    int client_fd = accept(
        server_fd_,
        (sockaddr*)&client,
        &size
    );

    fcntl(client_fd, F_SETFL, O_NONBLOCK);

    epoll_event event{};
    event.events = EPOLLIN;
    event.data.fd = client_fd;

    epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, client_fd, &event);

    std::cout << "Client connected\n";
}


void MainServer::receiveMessage(int client_fd)
{
    char buffer[1024];

    int bytes = recv(client_fd, buffer, sizeof(buffer), 0);

    if (bytes <= 0) {
        close(client_fd);

        epoll_ctl(epoll_fd_, EPOLL_CTL_DEL, client_fd, nullptr);

        std::cout << "Client disconnected\n";
        return;
    }

    handle_message(buffer, bytes, client_fd);
}

void MainServer::handle_message(const char* buffer, int bytes, int client_fd)
{
    /*
    std::string message(buffer, bytes);

    EntryRequest* request = reinterpret_cast<EntryRequest*>(buffer);

    */
}

} // namespace parkpulse

