#include "../../inc/server/MainServer.hpp"
#include "../../inc/repository/RedisCacheRepository.hpp"
#include "../../inc/models/Dto.hpp"

#include <mosquitto.h>
#include <nlohmann/json.hpp>

#include <iostream>
#include <stdexcept>

#define SQL_CONNECTION_STRING "host=localhost dbname=parkpulse"
#define REDIS_HOST "localhost"
#define REDIS_PORT 6379
#define MQTT_BROKER_HOST "localhost"
#define MQTT_BROKER_PORT 1883
#define MQTT_TOPIC_FILTER "parking/+/+/spot_update"

namespace parkpulse {

MainServer::MainServer(int port = SERVER_PORT, std::string redis_host = DEFAULT_REDIS_HOST, 
                       int redis_port = DEFAULT_REDIS_PORT, std::string mqtt_host = DEFAULT_MQTT_HOST, 
                       int mqtt_port = DEFAULT_MQTT_PORT)
    : port_(port)
    , redis_host_(std::move(redis_host))
    , redis_port_(redis_port)
    , mqtt_host_(std::move(mqtt_host))
    , mqtt_port_(mqtt_port)
{
}

MainServer::~MainServer()
{ 
    stop(); 
}

void MainServer::start() 
{
    cache_repository_ = std::make_unique<RedisCacheRepository>(redis_host_, redis_port_);

    setupSocket();
    setup_mqtt();

    std::cout << "ParkPulse main_server running on port " << port_
              << " (redis=" << redis_host_ << ":" << redis_port_
              << ", mqtt=" << mqtt_host_ << ":" << mqtt_port_
              << "). Ctrl+C to stop.\n";

    run();
}

void MainServer::stop() 
{
    if (mqtt_client_ != nullptr) {
        mosquitto_disconnect(mqtt_client_);
        mosquitto_destroy(mqtt_client_);
        mqtt_client_ = nullptr;

        mosquitto_lib_cleanup();
    }
    if (server_fd_ >= 0) {
        close(server_fd_);
        server_fd_ = -1;
    }

    if (epoll_fd_ >= 0) {
        close(epoll_fd_);
        epoll_fd_ = -1;
    }
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

void MainServer::setup_mqtt()
{
    mosquitto_lib_init();

    mqtt_client_ = mosquitto_new(nullptr, true, this);

    mosquitto_message_callback_set(mqtt_client_, on_mqtt_message);

    mosquitto_connect(mqtt_client_, MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60);
    mosquitto_subscribe(mqtt_client_, nullptr, MQTT_TOPIC_FILTER, 1);

    int mqtt_fd = mosquitto_socket(mqtt_client_);

    epoll_event event{};
    event.events = EPOLLIN;
    event.data.fd = mqtt_fd;

    epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, mqtt_fd, &event);
}

void MainServer::run() 
{
    epoll_event events[10];

    while (true) {
        // Finite timeout (instead of -1) so we can service mosquitto's
        // keepalive/misc work even when no fd is ready.
        int count = epoll_wait(epoll_fd_, events, 10, 1000);

        for (int i = 0; i < count; i++) {

            int fd = events[i].data.fd;

            if (fd == server_fd_) {
                acceptClient();
            } else if (mqtt_client_ != nullptr && fd == mosquitto_socket(mqtt_client_)) {
                mosquitto_loop_read(mqtt_client_, 1);

            } else {
                receiveMessage(fd);
            }
        }

        if (mqtt_client_ != nullptr) {
            mosquitto_loop_misc(mqtt_client_);

            if (mosquitto_want_write(mqtt_client_)) {
                mosquitto_loop_write(mqtt_client_, 1);
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

    if (client_fd < 0) {
        return;
    }

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
    (void)client_fd;
    std::string message(buffer, bytes);
    (void)message;
    
    const EntryRequest* request = reinterpret_cast<const EntryRequest*>(buffer);
    
    std::cout << "Received EntryRequest: parking_lot_id=" << request->parking_lot_id
              << ", gate_id=" << request->gate_id
              << ", wants_handicap=" << request->wants_handicap
              << ", wants_electric=" << request->wants_electric
              << std::endl;
    /*
    std::string message(buffer, bytes);

    EntryRequest* request = reinterpret_cast<EntryRequest*>(buffer);

    */
}

void MainServer::on_mqtt_message(mosquitto* mosq, void* obj, const mosquitto_message* message)
{
    (void)mosq;

    if (message->payloadlen <= 0) {
        return;
    }

    auto* self = static_cast<MainServer*>(obj);

    std::string payload(static_cast<const char*>(message->payload), message->payloadlen);

    self->handle_mqtt_message(payload);
}

void MainServer::handle_mqtt_message(const std::string& payload)
{
    try {
        const nlohmann::json json_payload = nlohmann::json::parse(payload);

        const std::string lot_id = json_payload.at("lot_id").get<std::string>();
        const std::string spot_id = json_payload.at("spot_id").get<std::string>();
        const bool is_occupied = json_payload.at("is_occupied").get<bool>();

        std::cout << "Spot update received: lot_id=" << lot_id
                  << ", spot_id=" << spot_id
                  << ", is_occupied=" << is_occupied
                  << std::endl;

        /*if (cache_repository_) {
            cache_repository_->update_spot_occupancy(lot_id, spot_id, is_occupied);
        }*/
    }
    catch (const std::exception& e) {
        std::cerr << "Failed to handle MQTT message: " << e.what() << std::endl;
    }
}

} // namespace parkpulse

