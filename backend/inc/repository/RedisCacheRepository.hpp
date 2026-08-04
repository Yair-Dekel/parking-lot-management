#pragma once

#include "ICacheRepository.hpp"

#include <string>

namespace parkpulse {

class RedisCacheRepository : public ICacheRepository {
public:
    RedisCacheRepository(const std::string& host, int port);
    ~RedisCacheRepository() override = default;

    void update_spot_occupancy(
        const std::string& lot_id,
        const std::string& spot_id,
        bool is_occupied
    ) override;

private:
    std::string host_;
    int port_ = 0;
};

} // namespace parkpulse
