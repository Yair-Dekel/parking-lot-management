#include "../../inc/repository/RedisCacheRepository.hpp"
#include "../../inc/models/Spot.hpp"
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>

namespace parkpulse
{

    RedisCacheRepository::RedisCacheRepository(const std::string &host, int port)
        : host_(host), port_(port)
    {
    }

    void RedisCacheRepository::update_spot_occupancy(
        const std::string &lot_id,
        const std::string &spot_id,
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

    void RedisCacheRepository::initialize_from_config(const std::string &config_path)
    {
        std::ifstream file(config_path);
        if (!file.is_open())
        {
            throw std::runtime_error("Failed to open config file: " + config_path);
        }

        nlohmann::json config;
        file >> config;

        for (const auto &lot_json : config["parking_lots"])
        {

            int lot_id = lot_json.at("id").get<int>();
            int lot_size = lot_json.at("size").get<int>();
            std::string lot_name = lot_json.at("name").get<std::string>();
            std::string location = lot_json.at("location").get<std::string>();
            std::string status = lot_json.at("status").get<std::string>();

            std::cout << "Lot " << lot_id << ", name=" << lot_name << std::endl;

            for (const auto &spot_json : lot_json["spots"])
            {

                Spot spot = spot_json.get<Spot>();
                std::cout
                    << "Spot " << spot.id << ", taken=" << spot.taken << ", handicap=" << spot.handicap
                    << ", electric=" << spot.electric << std::endl;

                // TODO: save_spot(spot);
            }

            // TODO: save_parking_lot(...)
        }
    }

} // namespace parkpulse
