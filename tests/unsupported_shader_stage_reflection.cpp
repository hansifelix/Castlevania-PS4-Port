#include "nvn_shaders.h"

#include <cstdint>
#include <cstdio>
#include <string>
#include <initializer_list>

using nx::nvn::ShaderReflection;
using nx::nvn::reflect_spirv;

static bool reflect_model(uint32_t model, ShaderReflection& out, std::string& error) {
    // SPIR-V header + OpEntryPoint with a two-word "main" string.
    const uint32_t words[] = {
        0x07230203u, 0x00010000u, 0u, 2u, 0u,
        (5u << 16) | 15u, model, 1u, 0x6e69616du, 0u,
    };
    return reflect_spirv(words, sizeof(words) / sizeof(words[0]), out, &error);
}

int main() {
    for (uint32_t model : {0u, 4u, 5u}) {
        ShaderReflection reflection;
        std::string error;
        if (!reflect_model(model, reflection, error)) {
            std::fprintf(stderr, "supported execution model %u rejected: %s\n", model, error.c_str());
            return 1;
        }
    }
    for (uint32_t model : {3u, 6u, 7u, 8u}) {
        ShaderReflection reflection;
        std::string error;
        if (reflect_model(model, reflection, error)) {
            std::fprintf(stderr, "unsupported execution model %u accepted\n", model);
            return 2;
        }
        if (error != "unsupported SPIR-V execution model") {
            std::fprintf(stderr, "wrong rejection for model %u: %s\n", model, error.c_str());
            return 3;
        }
    }
    std::puts("KAZUMA_ETAPA258_SPIRV_STAGE_HOST=PASS_VERTEX_FRAGMENT_COMPUTE_ONLY");
    return 0;
}
