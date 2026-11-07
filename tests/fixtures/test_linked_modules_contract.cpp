#include <nx/module.h>
#include <cstring>
#include <cstdio>
extern const nx::ModuleInfo nx_module_main;
extern const nx::ModuleInfo nx_module_sdk;
extern const nx::ModuleInfo nx_module_subsdk0;

int main() {
    const auto modules = nx::linked_modules();
    if (modules.size() != 3) return 1;
    const nx::ModuleInfo* expected[] = {&nx_module_main, &nx_module_sdk, &nx_module_subsdk0};
    const char* names[] = {"main", "sdk", "subsdk0"};
    for (unsigned i = 0; i != 3; ++i) {
        if (modules[i] != expected[i] || modules[i] == nullptr) return 2;
        if (modules[i]->name == nullptr || std::strcmp(modules[i]->name, names[i])) return 3;
        for (unsigned j = 0; j < i; ++j) if (modules[i] == modules[j]) return 4;
    }
    std::puts("PASS: registrou 3 modulos em ordem main/sdk/subsdk0");
    return 0;
}
