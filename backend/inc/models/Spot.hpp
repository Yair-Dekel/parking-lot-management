#pragma once
#include <string>
#include <cstdint>
#include <nlohmann/json.hpp>

namespace parkpulse {

// Mirrors the `spot` table.
// parking_lot_id, id, taken, handicap, electric, floor
struct Spot {
    int parking_lot_id = 0;
    int id = 0;
    bool taken = false;
    bool handicap = false;
    bool electric = false;
    int floor = 0;
};

inline void from_json(const nlohmann::json& j, Spot& s)
{
    j.at("parking_lot_id").get_to(s.parking_lot_id);
    j.at("id").get_to(s.id);
    j.at("taken").get_to(s.taken);
    j.at("handicap").get_to(s.handicap);
    j.at("electric").get_to(s.electric);
    j.at("floor").get_to(s.floor);
}

inline void to_json(nlohmann::json& j, const Spot& s)
{
    j = nlohmann::json{
        {"parking_lot_id", s.parking_lot_id},
        {"id", s.id},
        {"taken", s.taken},
        {"handicap", s.handicap},
        {"electric", s.electric},
        {"floor", s.floor}
    };
}

} // namespace parkpulse
