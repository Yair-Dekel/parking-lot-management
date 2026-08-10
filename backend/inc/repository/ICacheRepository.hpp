#pragma once

#include <string>
#include "../../inc/models/Spot.hpp"

namespace parkpulse
{

    class ICacheRepository
    {
    public:
        virtual ~ICacheRepository() = default;

        virtual void update_spot_occupancy(
            const std::string &lot_id,
            const std::string &spot_id,
            bool is_occupied) = 0;

        virtual void initialize_from_config(const std::string &config_path) = 0;

        virtual Spot get_spot(int parking_lot_id, int spot_id) = 0;
    };

} // namespace parkpulse
