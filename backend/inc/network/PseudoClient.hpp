#pragma once

#include "../models/Dto.hpp"
#include "../server/MainServer.hpp"

#include <string>

namespace parkpulse {

class PseudoClient {
public:
    PseudoClient(const std::string& host = "127.0.0.1", int port = SERVER_PORT);
    ~PseudoClient();

    bool connectToServer();
    bool sendEntryRequest(const EntryRequest& request);
    void disconnect();

private:
    std::string host_;
    int port_ = SERVER_PORT;
    int socket_fd_ = -1;
};

} // namespace parkpulse
