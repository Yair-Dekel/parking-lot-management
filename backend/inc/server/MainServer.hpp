#pragma once
#include <memory>
#include <string>

#define SERVER_PORT 5000

namespace parkpulse {

class IParkingRepository;
class ICacheRepository;

class MainServer {
public:
    MainServer();
    ~MainServer();

    void start();
    void stop();

private:
    std::shared_ptr<IParkingRepository> sql_repository_;
    std::shared_ptr<ICacheRepository> cache_repository_;

    int port_ = SERVER_PORT;
};

} // namespace parkpulse
