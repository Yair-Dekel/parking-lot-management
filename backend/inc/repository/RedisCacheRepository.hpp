#pragma once

#include "ICacheRepository.hpp"
#include <hiredis/hiredis.h>
#include <string>

namespace parkpulse
{

    /**
     * Redis-backed implementation of ICacheRepository.
     *
     * Responsible for:
     * - Connecting to the Redis server.
     * - Initializing parking data from a configuration file.
     * - Reading and writing parking spot state.
     */
    class RedisCacheRepository : public ICacheRepository
    {
    public:
        /**
         * Creates a repository and establishes a connection to Redis.
         *
         * @param host Redis server hostname or IP address.
         * @param port Redis server TCP port.
         * @throws std::runtime_error if the connection cannot be established.
         */
        RedisCacheRepository(const std::string &host, int port);

        /**
         * Releases the Redis connection.
         */
        ~RedisCacheRepository();

        void update_spot_occupancy(const std::string &lot_id, const std::string &spot_id, bool is_occupied) override;

        /**
         * Loads the initial parking-lot configuration from a JSON file and stores its spots in Redis.
         *
         * @param config_path Path to the parking-lot JSON configuration file.
         * @throws std::runtime_error if the file cannot be opened or parsed.
         */
        void initialize_from_config(const std::string &config_path) override;

        /**
         * Stores all fields of a single Spot as a Redis hash.
         *
         * Redis key format:
         * parking:<parking_lot_id>:spot:<spot_id>
         */
        void save_spot(const Spot &spot);

        /**
         * Reads a single Spot from Redis.
         *
         * @param parking_lot_id ID of the parking lot.
         * @param spot_id ID of the requested spot.
         * @return Spot populated with the values stored in Redis.
         * @throws std::runtime_error if the Redis command fails or the spot does not exist.
         */
        Spot get_spot(int parking_lot_id, int spot_id) override;

    private:
        std::string host_;
        int port_ = 0;
        redisContext *context_ = nullptr; // Active hiredis connection used by all repository operations
    };

} // namespace parkpulse
