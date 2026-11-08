#include <platform.h>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <sys/stat.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <signal.h>
#include <unistd.h>

int main() {
    const rlimit limit{0,0}; assert(setrlimit(RLIMIT_CORE,&limit)==0);
    char tmp[]="/tmp/kazuma-save-XXXXXX"; char* p=mkdtemp(tmp); assert(p);
    const std::string base=p;
    const std::string assets=base+"/app0";
    const std::string mount=base+"/mountedSaveData";
    assert(mkdir(assets.c_str(),0700)==0);
    assert(mkdir(mount.c_str(),0700)==0);
    assert(setenv("KAZUMA_TEST_APP0_ROOT",assets.c_str(),1)==0);
    assert(setenv("KAZUMA_TEST_SAVEDATA_MOUNT",(base+"/missing").c_str(),1)==0);

    pid_t child=fork();assert(child>=0);
    if(child==0) { (void)nx::plat::writable_root(); _exit(71); }
    int status=0;assert(waitpid(child,&status,0)==child);
    assert(WIFSIGNALED(status)&&WTERMSIG(status)==SIGABRT);
    assert(setenv("KAZUMA_TEST_SAVEDATA_MOUNT",mount.c_str(),1)==0);

    assert(nx::plat::writable_root()==mount);
    assert(nx::plat::writable_root()!=assets);
    assert(nx::plat::writable_root()==mount); // cached root
    const std::string dir=mount+"/user/save";
    struct stat st{}; assert(stat(dir.c_str(),&st)==0&&S_ISDIR(st.st_mode));
    const std::string file=dir+"/progress.bin";
    FILE* f=nx::plat::fopen_utf8(file,"wb");
    assert(f); const char bytes[]="KAZUMA-SAVE";
    assert(fwrite(bytes,1,sizeof(bytes),f)==sizeof(bytes));
    assert(fclose(f)==0);
    assert(stat(file.c_str(),&st)==0&&S_ISREG(st.st_mode));
    assert(stat((assets+"/user/save/progress.bin").c_str(),&st)!=0);
    assert(unlink(file.c_str())==0);
    assert(rmdir(dir.c_str())==0);
    assert(rmdir((mount+"/user/cache0").c_str())==0);
    assert(rmdir((mount+"/user").c_str())==0);
    assert(rmdir(mount.c_str())==0);
    assert(rmdir(assets.c_str())==0);
    assert(rmdir(base.c_str())==0);
}
