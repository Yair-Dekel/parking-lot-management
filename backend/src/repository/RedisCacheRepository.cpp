#include "../../inc/repository/RedisCacheRepository.hpp"

namespace parkpulse {

RedisCacheRepository::RedisCacheRepository(const std::string& host, int port)
    : host_(host), port_(port)
{
}

} // namespace parkpulse
