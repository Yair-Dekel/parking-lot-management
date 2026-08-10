#include "../../inc/repository/RedisCacheRepository.hpp"
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>

namespace parkpulse
{

    RedisCacheRepository::RedisCacheRepository(const std::string &host, int port)
        : host_(host), port_(port)
    {
        // Establish one persistent Redis connection for this repository instance
        context_ = redisConnect(host_.c_str(), port_);

        if (context_ == nullptr || context_->err)
        {
            std::string error = context_ ? context_->errstr : "Cannot allocate Redis context";

            if (context_)
            {
                redisFree(context_);
            }

            throw std::runtime_error("Redis connection failed: " + error);
        }
    }

    RedisCacheRepository::~RedisCacheRepository()
    {
        if (context_)
        {
            redisFree(context_);
            context_ = nullptr;
        }
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

    /**
     * Initializes Redis from the static parking-lot configuration.
     *
     * The JSON file defines the parking lots and their spots.
     * Each spot is converted to a Spot object and persisted through save_spot().
     */
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

            for (const auto &spot_json : lot_json["spots"])
            {
                // Spot already provides JSON deserialization through from_json()
                Spot spot = spot_json.get<Spot>();

                // Persist the initial state of this spot in Redis
                save_spot(spot);
            }

            // TODO: save_parking_lot(...)
        }
    }

    /**
     * Retrieves a Spot from Redis using HGETALL and reconstructs the corresponding Spot object.
     */
    Spot RedisCacheRepository::get_spot(int parking_lot_id, int spot_id)
    {
        redisReply *reply = static_cast<redisReply *>(
            redisCommand(
                context_,
                "HGETALL parking:%d:spot:%d",
                parking_lot_id,
                spot_id));

        if (reply == nullptr)
        {
            throw std::runtime_error("Redis HGETALL failed");
        }

        if (reply->type != REDIS_REPLY_ARRAY || reply->elements == 0)
        {
            freeReplyObject(reply);
            throw std::runtime_error("Spot not found in Redis");
        }

        Spot spot{};

        // HGETALL returns alternating field/value entries
        for (size_t i = 0; i < reply->elements; i += 2)
        {
            std::string field = reply->element[i]->str;
            std::string value = reply->element[i + 1]->str;

            if (field == "parking_lot_id")
            {
                spot.parking_lot_id = std::stoi(value);
            }
            else if (field == "id")
            {
                spot.id = std::stoi(value);
            }
            else if (field == "taken")
            {
                spot.taken = std::stoi(value) != 0;
            }
            else if (field == "handicap")
            {
                spot.handicap = std::stoi(value) != 0;
            }
            else if (field == "electric")
            {
                spot.electric = std::stoi(value) != 0;
            }
            else if (field == "floor")
            {
                spot.floor = std::stoi(value);
            }
        }

        freeReplyObject(reply);

        return spot;
    }

    /**
     * Stores a Spot as a Redis hash.
     *
     * Example key: parking:1:spot:2
     *
     * This allows individual spot fields, such as "taken", to be updated later without rewriting the entire object.
     */
    void RedisCacheRepository::save_spot(const Spot &spot)
    {
        redisReply *reply = static_cast<redisReply *>(
            redisCommand(
                context_,
                "HSET parking:%d:spot:%d "
                "parking_lot_id %d "
                "id %d "
                "taken %d "
                "handicap %d "
                "electric %d "
                "floor %d",
                spot.parking_lot_id,
                spot.id,
                spot.parking_lot_id,
                spot.id,
                spot.taken ? 1 : 0,
                spot.handicap ? 1 : 0,
                spot.electric ? 1 : 0,
                spot.floor));

        if (reply == nullptr)
        {
            throw std::runtime_error(
                "Failed to save spot to Redis");
        }

        freeReplyObject(reply);
    }

} // namespace parkpulse
