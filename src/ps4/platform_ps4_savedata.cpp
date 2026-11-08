// Kazuma Traducoes — real PS4 mounted writable data root, never /app0.
// `data_root` remains package assets at /app0. The runtime HLE FS uses
// `writable_root()` for user/save and cache folders.
// Requires the strict, pinned platform.h patch in tools/ps4. No commercial data.
#include <platform.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <sys/stat.h>

#if defined(KAZUMA_PS4)
#include <orbis/SaveData.h>
#include <orbis/UserService.h>
#include <orbis/Sysmodule.h>
#elif !defined(KAZUMA_TEST_WRITABLE_ROOT)
#error "Writable root must be compiled for PS4 or an explicit Linux host test"
#endif

namespace nx::plat {
namespace {
bool directory(const std::string& path) {
    struct stat st{};
    return ::stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode);
}
[[noreturn]] void fail(const char* message) {
    log_line(message);
    std::abort(); // Do not return /app0 or claim a fake mounted save.
}
bool safe_mount(const std::string& p) {
    return !p.empty() && p[0] == '/' && p != "/app0" &&
           p.find("/../") == std::string::npos &&
           p.find("//") == std::string::npos &&
           p.size() < 128 && directory(p);
}
std::string mount_root() {
#if defined(KAZUMA_PS4)
    // Sony APIs come from actual PS4 UserService, Sysmodule and SaveData.
    const int service = sceUserServiceInitialize(nullptr);
    if (service < 0) fail("Kazuma PS4: UserService initialization failed");
    int32_t user = -1;
    if (sceUserServiceGetInitialUser(&user) < 0 || user < 0)
        fail("Kazuma PS4: no valid signed-in user for savedata");
    // Loading the SaveData library is necessary before its exported calls.
    const auto loaded = sceSysmoduleLoadModuleInternal(ORBIS_SYSMODULE_INTERNAL_SAVE_DATA);
    if (static_cast<int32_t>(loaded) < 0)
        fail("Kazuma PS4: SaveData system module load failed");
    if (sceSaveDataInitialize3(0) < 0)
        fail("Kazuma PS4: SaveData initialization failed");

    OrbisSaveDataDirName name{};
    std::strncpy(name.data, "KAZUMA_PS4", sizeof(name.data) - 1);
    OrbisSaveDataMount2 request{};
    request.userId = user;
    request.dirName = &name;
    request.blocks = 1024; // 32 MiB; PS4 save quota, not a copy of the ROM.
    request.mountMode = ORBIS_SAVE_DATA_MOUNT_MODE_RDWR |
                        ORBIS_SAVE_DATA_MOUNT_MODE_CREATE2;
    OrbisSaveDataMountResult result{};
    if (sceSaveDataMount2(&request, &result) < 0)
        fail("Kazuma PS4: real SaveData mount failed");
    const size_t n = strnlen(result.mountPathName, sizeof(result.mountPathName));
    if (n == 0 || n == sizeof(result.mountPathName))
        fail("Kazuma PS4: SaveData returned invalid mount pathname");
    const std::string root(result.mountPathName, n);
#else
    // Host-only verification; not compiled into a PS4 object.
    const char* test_mount = std::getenv("KAZUMA_TEST_SAVEDATA_MOUNT");
    const std::string root = test_mount ? test_mount : "";
#endif
    if (!safe_mount(root)) fail("Kazuma PS4: SaveData mount was not a real directory");
    return root;
}
} // namespace

std::string writable_root() {
    static const std::string root = [] {
        const std::string mount = mount_root();
        // HLE save/cache paths are underneath writable_root()/user/.
        if (!make_dirs(mount + "/user/save") ||
            !make_dirs(mount + "/user/cache0"))
            fail("Kazuma PS4: cannot initialize directories on SaveData mount");
        return mount;
    }();
    return root;
}
} // namespace nx::plat
