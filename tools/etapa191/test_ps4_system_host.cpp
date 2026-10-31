// Host-only verification of actual PS4 adapter logic; display provider mocked.
#include "platform.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
namespace nx::plat {
void desktop_size(uint32_t& w,uint32_t& h){w=1920;h=1080;}
void log_line(const char*) {}
}
#define CHECK(x) do {if(!(x)){std::fprintf(stderr,"LINGSHU191_FAILED line=%d %s\\n",__LINE__,#x);return 1;}}while(0)
int main() {
    using namespace nx::plat;
    int cases=0;
    CHECK(!make_dirs(""));++cases;
    CHECK(!make_dirs("./bad"));++cases;
    CHECK(!make_dirs("../bad"));++cases;
    char tmp[]="/tmp/kazuma191-XXXXXX";
    char* root=mkdtemp(tmp);
    CHECK(root);++cases;
    const std::string path=std::string(root)+"/nested/a/b";
    CHECK(make_dirs(path));++cases;
    CHECK(make_dirs(path));++cases;
    struct stat st{};
    CHECK(stat(path.c_str(),&st)==0 && S_ISDIR(st.st_mode));++cases;
    CHECK(make_dirs(std::string(root)+"//nested/a/"));++cases;
    int fd=open((std::string(root)+"/file").c_str(),O_WRONLY|O_CREAT|O_EXCL,0600);
    CHECK(fd>=0);++cases;
    close(fd);
    CHECK(!make_dirs(std::string(root)+"/file/nested"));++cases;
    CHECK(!make_dirs(std::string(root)+"/../escaped"));++cases;
    uint32_t w=0,h=0;
    window_size(w,h);
    CHECK(w==1920 && h==1080);++cases;
    screen_size(w,h);
    CHECK(w==1920 && h==1080);++cases;
    CHECK(default_render_scale()==1.0f);++cases;
    CHECK(!headless());++cases;
    OverlayShape shape{};
    CHECK(touch_overlay(&shape,1)==0);++cases;
    CHECK(memguard_overlap_ns(123,456)==0);++cases;
    start_memory_guard();++cases;
    std::puts("LINGSHU191_PS4_PLATFORM_SYSTEM_CONTRACTS=PASSED_17_CASES_NO_GPU_NO_GAME");
    unlink((std::string(root)+"/file").c_str());
    rmdir(path.c_str());rmdir((std::string(root)+"/nested/a").c_str());
    rmdir((std::string(root)+"/nested").c_str());rmdir(root);
    return 0;
}
