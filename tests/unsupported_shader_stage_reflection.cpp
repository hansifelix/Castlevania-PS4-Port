#include "nvn_shaders.h"

#include <cstdint>
#include <cstdio>
#include <string>
#include <initializer_list>
#include <vector>

using nx::nvn::ShaderReflection;
using nx::nvn::reflect_spirv;

static void append_entrypoint(std::vector<uint32_t>& words, uint32_t model, uint32_t id, bool second) {
    // OpEntryPoint with two-word name ("main" or "other") and no interface IDs.
    words.push_back((5u << 16) | 15u);
    words.push_back(model);
    words.push_back(id);
    words.push_back(second ? 0x6568746fu : 0x6e69616du);
    words.push_back(second ? 0x00000072u : 0u);
}

static bool reflect_models(std::initializer_list<uint32_t> models, ShaderReflection& out, std::string& error) {
    std::vector<uint32_t> words = {0x07230203u, 0x00010000u, 0u, 3u, 0u};
    uint32_t id = 1;
    bool second = false;
    for (uint32_t model : models) {
        append_entrypoint(words, model, id++, second);
        second = true;
    }
    return reflect_spirv(words.data(), words.size(), out, &error);
}

static bool reflect_model(uint32_t model, ShaderReflection& out, std::string& error) {
    return reflect_models({model}, out, error);
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
    for (uint32_t model : {1u, 2u, 3u, 6u, 7u, 8u, 5267u, 5268u,
                           5313u, 5314u, 5315u, 5316u, 5317u, 5318u}) {
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

    // The runtime selects the first entry point; only that entry's stage is used.
    {
        ShaderReflection reflection;
        std::string error;
        if (!reflect_models({0u, 3u}, reflection, error) || reflection.stage != nx::nvn::ShaderStage::Vertex ||
            reflection.entry != "main") {
            std::fprintf(stderr, "supported first entry rejected or misclassified: %s\n", error.c_str());
            return 4;
        }
    }
    {
        ShaderReflection reflection;
        std::string error;
        if (reflect_models({3u, 0u}, reflection, error) || error != "unsupported SPIR-V execution model") {
            std::fprintf(stderr, "unsupported first entry accepted: %s\n", error.c_str());
            return 5;
        }
    }
    std::puts("KAZUMA_ETAPA258_SPIRV_STAGE_HOST=PASS_VERTEX_FRAGMENT_COMPUTE_UNSUPPORTED_AND_FIRST_ENTRY");
    return 0;
}
