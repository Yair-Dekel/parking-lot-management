#pragma once
#include <vector>
#include "Spot.hpp"

/*
 * Data Transfer Objects for handling requests and responses in the parking system.
 */

namespace parkpulse {

// What the Gate sends when a car requests entry.
struct EntryRequest {
    int parking_lot_id = 0;
    int gate_id = 0;
    
    bool wants_handicap = false;
    bool wants_electric = false;
};

// What the server sends back to the Gate.
struct EntryResponse {
    bool lot_has_space = false;
    int suggested_spot_id = -1;          // -1 if none
    std::vector<Spot> available_spots;  // full list, per the spec
};

// A sensor->sensor_server->MQTT->server occupancy update.
struct OccupancyEvent {
    int parking_lot_id = 0;
    int spot_id = 0;
    bool taken = false;
    long long timestamp_epoch_seconds = 0;
    std::string source_sensor_server_id;
};

} // namespace parkpulse
