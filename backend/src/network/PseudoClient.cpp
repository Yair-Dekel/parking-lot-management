#include "../../inc/network/PseudoClient.hpp"

#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

namespace parkpulse {

PseudoClient::PseudoClient(const std::string& host, int port)
    : host_(host), port_(port)
{
}

PseudoClient::~PseudoClient()
{
    disconnect();
}

bool PseudoClient::connectToServer()
{
    if (socket_fd_ >= 0) {
        return true;
    }

    socket_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (socket_fd_ < 0) {
        return false;
    }

    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port_);

    if (inet_pton(AF_INET, host_.c_str(), &server_addr.sin_addr) <= 0) {
        disconnect();
        return false;
    }

    if (connect(socket_fd_, reinterpret_cast<sockaddr*>(&server_addr), sizeof(server_addr)) < 0) {
        disconnect();
        return false;
    }

    return true;
}

bool PseudoClient::sendEntryRequest(const EntryRequest& request)
{
    if (socket_fd_ < 0 && !connectToServer()) {
        return false;
    }

    const char* payload = reinterpret_cast<const char*>(&request);
    const size_t total_size = sizeof(request);
    size_t sent_total = 0;

    while (sent_total < total_size) {
        const ssize_t sent = send(socket_fd_, payload + sent_total, total_size - sent_total, 0);
        if (sent <= 0) {
            return false;
        }

        sent_total += static_cast<size_t>(sent);
    }

    return true;
}

void PseudoClient::disconnect()
{
    if (socket_fd_ >= 0) {
        close(socket_fd_);
        socket_fd_ = -1;
    }
}

} // namespace parkpulse
