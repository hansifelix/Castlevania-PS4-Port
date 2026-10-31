#!/usr/bin/env bash
# Lingshu 172: host regression test of the production preflight source.
# Fake ModuleInfo / platform APIs only; no commercial data or console required.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/nx" "$tmp/testroot/analysis"
cat > "$tmp/nx/module.h" <<'HEADER'
#pragma once
#include <span>
#include <cstdint>
namespace nx {
struct ModuleInfo {const char* name; uint64_t base; uint64_t text, text_size, ro, ro_size, data, data_size, bss, bss_size;};
std::span<const ModuleInfo* const> linked_modules();
}
HEADER
cat > "$tmp/platform.h" <<'HEADER'
#pragma once
#include <string>
#include <cstdio>
#include <cstdint>
namespace nx::plat {
std::string data_root();
FILE* fopen_utf8(const std::string&,const char*);
int fseek64(FILE*,int64_t,int);
int64_t ftell64(FILE*);
void log_line(const char*);
}
HEADER
cat > "$tmp/test.cpp" <<'TEST'
#include <nx/module.h>
#include <string>
#include <cstdio>
#include <filesystem>
#include <vector>
#include <cassert>
#include <cstdlib>
namespace fs=std::filesystem;
static std::string root;
static std::string message;
namespace nx::plat {
 std::string data_root(){return root;}
 FILE* fopen_utf8(const std::string& path,const char* mode){return std::fopen(path.c_str(),mode);}
 int fseek64(FILE* f,int64_t off,int origin){return fseek(f,off,origin);}
 int64_t ftell64(FILE* f){return ftell(f);}
 void log_line(const char* msg){message=msg;}
}
static nx::ModuleInfo a{"main",0,0,0,0,0,0,5,0,0};
static nx::ModuleInfo b{"sdk",0,0,0,0,0,0,8,0,0};
static nx::ModuleInfo c{"subsdk0",0,0,0,0,0,0,3,0,0};
namespace nx {std::span<const ModuleInfo* const> linked_modules(){static const ModuleInfo* const ar[]={&a,&b,&c};return ar;}}
extern "C" bool lingshu_ps4_boot_images_present();
int main(){
 root=std::getenv("LINGSHU172_TEST_ROOT");
 assert(!root.empty());
 assert(!lingshu_ps4_boot_images_present() && message.find("missing")!=std::string::npos);
 for(auto [name,n]:std::vector<std::pair<std::string,int>>{{"main",5},{"sdk",8},{"subsdk0",3}}){
   FILE* f=fopen((root+"/analysis/"+name+".bin").c_str(),"wb");
   assert(f);for(int i=0;i<n;i++) fputc(0,f);fclose(f);
 }
 assert(lingshu_ps4_boot_images_present());
 b.data_size=100;
 assert(!lingshu_ps4_boot_images_present() && message.find("wrong flat image length")!=std::string::npos);
 b.data_size=8;
 a.data=UINT64_MAX;
 assert(!lingshu_ps4_boot_images_present() && message.find("overflow")!=std::string::npos);
 a.data=0;
 a.name="unknown";
 assert(!lingshu_ps4_boot_images_present() && message.find("invalid AOT module table")!=std::string::npos);
 a.name="main";
 assert(lingshu_ps4_boot_images_present());
 puts("LINGSHU172_BOOT_PREFLIGHT_SYNTHETIC=PASSED_6_CASES_HOST_ONLY");
}
TEST
g++ -std=c++20 -O2 -Wall -Wextra -Werror \
    -I"$tmp" "$root/tools/etapa172/ps4_boot_images_preflight.cpp" \
    "$tmp/test.cpp" -o "$tmp/test-preflight"
LINGSHU172_TEST_ROOT="$tmp/testroot" "$tmp/test-preflight"
