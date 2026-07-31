#include "../../backend/inc/models/Dto.hpp"
#include "../../backend/inc/network/PseudoClient.hpp"
#include "../../backend/inc/server/MainServer.hpp"

#include <chrono>
#include <csignal>
#include <iostream>
#include <sys/types.h>
#include <sys/wait.h>
#include <thread>
#include <unistd.h>
#include <vector>

namespace {

constexpr int kTestPort = 5500;

bool waitForServerStart(int max_attempts, int delay_ms)
{
	for (int i = 0; i < max_attempts; ++i) {
		parkpulse::PseudoClient probe("127.0.0.1", kTestPort);
		if (probe.connectToServer()) {
			probe.disconnect();
			return true;
		}

		std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
	}

	return false;
}

bool sendOneEntryRequest(int gate_id)
{
	parkpulse::PseudoClient client("127.0.0.1", kTestPort);

	parkpulse::EntryRequest request;
	request.parking_lot_id = 1;
	request.gate_id = gate_id;
	request.wants_handicap = (gate_id % 2 == 0);
	request.wants_electric = (gate_id % 3 == 0);

	const bool sent = client.sendEntryRequest(request);
	client.disconnect();

	return sent;
}

} // namespace

int main()
{
	pid_t server_pid = fork();
	if (server_pid < 0) {
		std::cerr << "FAIL: could not fork server process\n";
		return 1;
	}

	if (server_pid == 0) {
		parkpulse::MainServer server(kTestPort);
		server.start();
		return 0;
	}

	if (!waitForServerStart(40, 50)) {
		std::cerr << "FAIL: server did not start in time\n";
		kill(server_pid, SIGTERM);
		waitpid(server_pid, nullptr, 0);
		return 1;
	}

	std::vector<std::thread> workers;
	std::vector<bool> results(8, false);

	for (size_t i = 0; i < results.size(); ++i) {
		workers.emplace_back([&results, i]() {
			results[i] = sendOneEntryRequest(static_cast<int>(i + 1));
		});
	}

	for (std::thread& worker : workers) {
		worker.join();
	}

	bool all_sent = true;
	for (bool sent : results) {
		if (!sent) {
			all_sent = false;
			break;
		}
	}

	const bool server_still_alive = (kill(server_pid, 0) == 0);

	kill(server_pid, SIGTERM);
	waitpid(server_pid, nullptr, 0);

	if (!all_sent) {
		std::cerr << "FAIL: at least one client failed to send request\n";
		return 1;
	}

	if (!server_still_alive) {
		std::cerr << "FAIL: server died while epoll test was running\n";
		return 1;
	}

	std::cout << "PASS: epoll accepted multiple clients and processed requests\n";
	return 0;
}




