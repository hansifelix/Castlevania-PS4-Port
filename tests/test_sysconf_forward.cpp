#include <cassert>
#include <unistd.h>

extern "C" long orbis_sysconf(int);

int main() {
    const long expected = ::sysconf(_SC_PAGESIZE);
    const long actual = orbis_sysconf(_SC_PAGESIZE);
    assert(expected > 0);
    assert(actual == expected);
    return 0;
}
