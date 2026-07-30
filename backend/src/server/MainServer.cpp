#include "../../inc/network/GateServer.hpp"
#include "../../inc/network/SensorMqttClient.hpp"
#include "../../inc/server/MainServer.hpp"
#include "../repository/SqlParkingRepository.hpp"
#include "../repository/RedisCacheRepository.hpp"
#include <iostream>
#include <stdexcept>

#define SQL_CONNECTION_STRING "host=localhost dbname=parkpulse"
#define REDIS_HOST "localhost"
#define REDIS_PORT 6379
#define MQTT_BROKER_HOST "localhost"
#define MQTT_BROKER_PORT 1883

namespace parkpulse {

MainServer::MainServer() = default;
MainServer::~MainServer()
{ 
    stop(); 
}

void MainServer::start() {
    const std::string sql_connection_string = SQL_CONNECTION_STRING;
    const std::string redis_host = REDIS_HOST;
    const int redis_port = REDIS_PORT;
    const std::string mqtt_broker_host = MQTT_BROKER_HOST;
    const int mqtt_broker_port = MQTT_BROKER_PORT;

    sql_repository_ = std::make_shared<SqlParkingRepository>(sql_connection_string);
    cache_repository_ = std::make_shared<RedisCacheRepository>(redis_host, redis_port);

    std::cout << "ParkPulse main_server running. Ctrl+C to stop.\n";
}

void MainServer::stop() {

}

} // namespace parkpulse
