#include "nvn_shaders.h"
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 2) return 10;
    std::ifstream in(argv[1], std::ios::binary);
    if (!in) return 11;
    in.seekg(0, std::ios::end);
    const auto bytes = in.tellg();
    if (bytes <= 0 || (bytes % 4) != 0) return 12;
    in.seekg(0, std::ios::beg);
    std::vector<uint32_t> words(static_cast<size_t>(bytes) / 4);
    in.read(reinterpret_cast<char*>(words.data()), bytes);
    if (!in) return 13;

    nx::nvn::ShaderReflection reflection;
    std::string error;
    if (nx::nvn::reflect_spirv(words.data(), words.size(), reflection, &error)) {
        std::fprintf(stderr, "valid Geometry execution model unexpectedly accepted\n");
        return 1;
    }
    if (error != "unsupported SPIR-V execution model") {
        std::fprintf(stderr, "wrong rejection reason: %s\n", error.c_str());
        return 2;
    }
    std::puts("KAZUMA_ETAPA263_VALID_GEOMETRY_SPIRV_REJECTED_BY_FAILCLOSED=PASS");
    return 0;
}
