// Host POSIX regression; same implementation as the PS4 target, no game files.
#include <platform.h>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <unistd.h>
#include <signal.h>

int main() {
    struct rlimit limit{0, 0};
    assert(setrlimit(RLIMIT_CORE, &limit) == 0);
    char tmp[] = "/tmp/kazuma-app0-root-XXXXXX";
    char* created = mkdtemp(tmp);
    assert(created);
    const std::string root = created;
    assert(setenv("KAZUMA_TEST_APP0_ROOT", root.c_str(), 1) == 0);

    // Missing real game data is a hard failure, not a fake empty game boot.
    const pid_t child = fork();
    assert(child >= 0);
    if (child == 0) {
        (void)nx::plat::data_root();
        _exit(70); // An invalid return would be caught as a test failure.
    }
    int status = 0;
    assert(waitpid(child, &status, 0) == child);
    assert(WIFSIGNALED(status) && WTERMSIG(status) == SIGABRT);

    const std::string analysis = root + "/analysis";
    const std::string extract = root + "/extract";
    const std::string romfs = extract + "/romfs";
    assert(mkdir(analysis.c_str(), 0700) == 0);
    assert(mkdir(extract.c_str(), 0700) == 0);
    assert(mkdir(romfs.c_str(), 0700) == 0);
    assert(nx::plat::data_root() == root);
    assert(nx::plat::setting("trace").empty());  // File optional.
    assert(nx::plat::setting("../trace").empty()); // Reject key traversal.
    const std::string config = root + "/kazuma-settings.cfg";
    FILE* f = std::fopen(config.c_str(), "wb");
    assert(f);
    const char cfg[] = "# private packaged settings\n trace = 1 \nrender_scale = 0.75\nfoo=bar\n";
    assert(std::fwrite(cfg, 1, sizeof(cfg)-1, f) == sizeof(cfg)-1);
    assert(std::fclose(f) == 0);
    assert(nx::plat::setting("trace") == "1");
    assert(nx::plat::setting("render_scale") == "0.75");
    assert(nx::plat::setting("foo") == "bar");
    assert(nx::plat::setting("missing").empty());
    nx::plat::log_line("100% test completed; no format string injection");
    assert(unlink(config.c_str()) == 0);
    assert(rmdir(romfs.c_str()) == 0);
    assert(rmdir(extract.c_str()) == 0);
    assert(rmdir(analysis.c_str()) == 0);
    assert(rmdir(root.c_str()) == 0);
}
