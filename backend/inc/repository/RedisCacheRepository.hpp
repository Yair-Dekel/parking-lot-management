#pragma once

#include "ICacheRepository.hpp"

#include <string>

namespace parkpulse {

class RedisCacheRepository : public ICacheRepository {
public:
    RedisCacheRepository(const std::string& host, int port);
    ~RedisCacheRepository() override = default;

private:
    std::string host_;
    int port_ = 0;
};

} // namespace parkpulse
