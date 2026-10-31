// Production PS4 logger regression. Uses real POSIX file I/O, no game data.
#include "platform.h"
#include <sys/stat.h>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <thread>
#include <vector>
#define CHECK(x) do { if(!(x)) { std::fprintf(stderr,"LINGSHU180_FAILED line=%d %s\n",__LINE__,#x);return 1;} } while(0)
int main(int argc,char**) {
    using namespace nx::plat;
    const std::string root=data_root();
    CHECK(root[0]=='/');
    if(argc>1) {
        log_line("LINGSHU180_ROOT_INACCESSIBLE_FALLBACK");
        std::puts("LINGSHU180_STDERR_FALLBACK=PASSED_NO_GAME");
        return 0;
    }
    CHECK(mkdir(root.c_str(),0700)==0);
    // Simulate a previous huge boot log: the next message must rotate it.
    const std::string file=root+"/boot.log";
    {
        std::ofstream old(file,std::ios::binary);
        CHECK(bool(old));
        old.seekp(2*1024*1024);
        old.put('x');
    }
    log_line("LINGSHU180_BOOT_ENTRY");
    constexpr int workers=4;
    constexpr int per_worker=100;
    std::vector<std::thread> threads;
    for(int t=0;t<workers;++t) {
        threads.emplace_back([t]() {
            for(int i=0;i<per_worker;++i) {
                char msg[80];
                std::snprintf(msg,sizeof msg,"LINGSHU180_WORKER_%d_LINE_%d",t,i);
                nx::plat::log_line(msg);
            }
        });
    }
    for(auto& t:threads) t.join();
    log_line("LINGSHU180_BOOT_END");
    std::ifstream input(file);
    CHECK(bool(input));
    std::string line;
    int total=0,first=0,last=0,threadlines=0;
    while(std::getline(input,line)) {
        ++total;
        if(line=="LINGSHU180_BOOT_ENTRY") ++first;
        else if(line=="LINGSHU180_BOOT_END") ++last;
        else if(line.rfind("LINGSHU180_WORKER_",0)==0) ++threadlines;
        else { std::fprintf(stderr,"UNEXPECTED LOG LINE: %s\n",line.c_str()); return 1; }
    }
    CHECK(first==1 && last==1 && threadlines==workers*per_worker);
    CHECK(total==workers*per_worker+2);
    struct stat info{};
    CHECK(stat(file.c_str(),&info)==0 && info.st_size>0 && info.st_size<2*1024*1024);
    std::puts("LINGSHU180_REAL_PERSISTENT_BOOT_LOG=PASSED_ROTATION_402_LINES_4_THREADS_NO_GAME");
    return 0;
}
