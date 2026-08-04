#include "../../inc/repository/RedisCacheRepository.hpp"

namespace parkpulse {

RedisCacheRepository::RedisCacheRepository(const std::string& host, int port)
    : host_(host), port_(port)
{
}

void RedisCacheRepository::update_spot_occupancy(
    const std::string& lot_id,
    const std::string& spot_id,
    bool is_occupied)
{
    // TODO: replace with a real Redis client call once the Redis
    // integration is in place (e.g. a hiredis SET/HSET keyed on
    // lot_id + spot_id). This is a no-op stub for now so MainServer can
    // compile, run, and be tested end-to-end without a live Redis
    // instance.
    (void)lot_id;
    (void)spot_id;
    (void)is_occupied;
}

} // namespace parkpulse
