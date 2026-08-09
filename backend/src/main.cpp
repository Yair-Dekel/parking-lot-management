#include "../inc/server/MainServer.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

namespace {

void print_usage(const char* program_name)
{
    std::cout << "Usage: " << program_name << " [options]\n"
              << "  --port <n>         TCP port for gate connections (default 5000)\n"
              << "  --redis-host <h>   Redis host (default localhost)\n"
              << "  --redis-port <n>   Redis port (default 6379)\n"
              << "  --mqtt-host <h>    MQTT broker host (default localhost)\n"
              << "  --mqtt-port <n>    MQTT broker port (default 1883)\n";
}

} // namespace

int main(int argc, char** argv)
{
    int port = 5000;
    std::string redis_host = "localhost";
    int redis_port = 6379;
    std::string mqtt_host = "localhost";
    int mqtt_port = 1883;

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];

        auto next_value = [&](const char* flag_name) -> std::string {
            if (i + 1 >= argc) {
                std::cerr << "Missing value for " << flag_name << "\n";
                std::exit(1);
            }
            return argv[++i];
        };

        if (arg == "--port") {
            port = std::stoi(next_value("--port"));
        } else if (arg == "--redis-host") {
            redis_host = next_value("--redis-host");
        } else if (arg == "--redis-port") {
            redis_port = std::stoi(next_value("--redis-port"));
        } else if (arg == "--mqtt-host") {
            mqtt_host = next_value("--mqtt-host");
        } else if (arg == "--mqtt-port") {
            mqtt_port = std::stoi(next_value("--mqtt-port"));
        } else if (arg == "--help" || arg == "-h") {
            print_usage(argv[0]);
            return 0;
        } else {
            std::cerr << "Unknown argument: " << arg << "\n";
            print_usage(argv[0]);
            return 1;
        }
    }

    parkpulse::MainServer server(port, redis_host, redis_port, mqtt_host, mqtt_port);
    server.start();

    return 0;
}
