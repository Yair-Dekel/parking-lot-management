#pragma once
#include <string>

namespace parkpulse {

enum class LotStatus {
    OPEN,
    FULL,
    CLOSED,
    MAINTENANCE
};

// Mirrors the `parking_lot` table.
// id, size, name, location, status
struct ParkingLot {
    int id = 0;
    int size = 0;          // total number of spots
    std::string name;
    std::string location = "";
    LotStatus status = LotStatus::OPEN;
};

} // namespace parkpulse
