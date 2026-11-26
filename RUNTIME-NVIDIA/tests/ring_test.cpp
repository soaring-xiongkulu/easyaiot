#include "BoundedRing.h"

#include <chrono>
#include <stdexcept>
#include <string>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
}  // namespace

int main() {
    easyaiot::nvidia::BoundedRing<std::string> ring(2);
    bool dropped = false;
    require(ring.pushDropOldest("one", &dropped) && !dropped, "first push failed");
    require(ring.pushDropOldest("two", &dropped) && !dropped, "second push failed");
    require(ring.pushDropOldest("three", &dropped) && dropped, "oldest item was not dropped");
    std::string value;
    require(ring.pop(value, std::chrono::milliseconds(1)) && value == "two",
            "ring order after drop is invalid");
    require(ring.pop(value, std::chrono::milliseconds(1)) && value == "three",
            "ring tail is invalid");
    ring.close();
    require(!ring.pop(value, std::chrono::milliseconds(1)), "closed ring returned an item");
    return 0;
}
