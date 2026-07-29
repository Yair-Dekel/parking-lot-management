#pragma once
#include <string>
#include <cstdint>

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

} // namespace parkpulse
