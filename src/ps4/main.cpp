// Native PS4 application entry point for the pinned upstream runtime.
// Upstream platform entry points call nx::boot(); this is the PS4 equivalent.
namespace nx {
void boot();
}

int main() {
    nx::boot();
    return 0;
}
