// Registro real dos módulos de Castlevania. Produz a mesma ABI e ordem que
// games/castlevania/modules.cmake + CMakeLists.txt do upstream fixado.
//
// EXIGE as três tabelas AOT reais no link final. NÃO há weak symbols,
// ponteiros nulos artificiais ou implementação de fallback para mascarar ausência.
// Os símbolos são definidos pelos respectivos table.cpp PRIVADOS, não aqui.
#include <nx/module.h>

extern const nx::ModuleInfo nx_module_main;
extern const nx::ModuleInfo nx_module_sdk;
extern const nx::ModuleInfo nx_module_subsdk0;

namespace nx {
std::span<const ModuleInfo* const> linked_modules() {
    static const ModuleInfo* const modules[] = {
        &nx_module_main,
        &nx_module_sdk,
        &nx_module_subsdk0,
    };
    return modules;
}
} // namespace nx
