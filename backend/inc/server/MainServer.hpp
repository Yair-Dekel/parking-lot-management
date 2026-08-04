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

struct mosquitto;
struct mosquitto_message;

namespace parkpulse {

class ICacheRepository;

class MainServer {
public:
    MainServer(
        int port = SERVER_PORT,
        std::string redis_host = DEFAULT_REDIS_HOST,
        int redis_port = DEFAULT_REDIS_PORT,
        std::string mqtt_host = DEFAULT_MQTT_HOST,
        int mqtt_port = DEFAULT_MQTT_PORT
    );
    ~MainServer();

    void start();
    void stop();

private:
    void setupSocket();
    void setup_mqtt();
    void run();
    void acceptClient();
    void receiveMessage(int client_fd);
    void handle_message(const char* buffer, int bytes, int client_fd);
    void handle_mqtt_message(const std::string& payload);

    static void on_mqtt_message(mosquitto* mosq, void* obj, const mosquitto_message* message);

private:
    std::unique_ptr<ICacheRepository> cache_repository_;

    int port_ = SERVER_PORT;
    std::string redis_host_ = DEFAULT_REDIS_HOST;
    int redis_port_ = DEFAULT_REDIS_PORT;
    std::string mqtt_host_ = DEFAULT_MQTT_HOST;
    int mqtt_port_ = DEFAULT_MQTT_PORT;

    int server_fd_ = -1;
    int epoll_fd_ = -1;

    mosquitto* mqtt_client_ = nullptr;
};

} // namespace parkpulse
