#include "BoundedRing.h"

#include <cassert>
#include <chrono>
#include <string>

int main() {
    using easyaiot::bm1688::BoundedRing;
    BoundedRing<std::string> ring(2);
    bool dropped = false;
    assert(ring.pushDropOldest("one", &dropped) && !dropped);
    assert(ring.pushDropOldest("two", &dropped) && !dropped);
    assert(ring.pushDropOldest("three", &dropped) && dropped);
    assert(ring.size() == 2);

    std::string value;
    assert(ring.pop(value, std::chrono::milliseconds(1)) && value == "two");
    assert(ring.pop(value, std::chrono::milliseconds(1)) && value == "three");
    ring.close();
    assert(!ring.pop(value, std::chrono::milliseconds(1)));
    return 0;
}
