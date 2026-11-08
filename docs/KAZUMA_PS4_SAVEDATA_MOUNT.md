# Operação Castlevania — SaveData real em vez de gravar no /app0

O runtime original MIT fixado em
`4043f21bb4f656d34cd17ba070238c7728d00631`
declara `writable_root() { return data_root(); }` fora do macOS.
A PR #119 fornece `data_root() == "/app0"` para recursos empacotados,
mas `/app0` **não deve ser usado para gravar save/cache no PS4**.

Esta etapa divide os caminhos reais:
- **Somente leitura:** `/app0/analysis`, `/app0/extract/romfs`,
  `/app0/kazuma-settings.cfg` (se existir).
- **Gravável:** `nx::plat::writable_root()` devolve o mount
  retornado de verdade por `sceSaveDataMount2` no console.
  `nx::plat::make_dirs` cria `user/save` e `user/cache0`
  no SaveData montado, nunca em `/app0`.

Para tornar as funções compatíveis, `tools/ps4/patch_writable_root.py`
aplica UMA alteração precisa no `runtime/src/platform.h` da **cópia
temporária** do upstream fixado no CI. Essa cópia passa a declarar
`writable_root()` para `KAZUMA_PS4` e
`KAZUMA_TEST_WRITABLE_ROOT`; as demais plataformas mantêm o
comportamento original. O patch falha se a linha upstream mudar.
O build privado do jogo deverá aplicar exatamente essa alteração
também aos objetos que usam `platform.h`; os testes públicos
NÃO garantem que esse pipeline privado já esteja integrado.

A fonte real `src/ps4/platform_ps4_savedata.cpp` usa:
- `sceUserServiceInitialize` e `sceUserServiceGetInitialUser`;
- `sceSysmoduleLoadModuleInternal` para SaveData;
- `sceSaveDataInitialize3` e `sceSaveDataMount2`;
- modo `ORBIS_SAVE_DATA_MOUNT_MODE_RDWR | CREATE2`,
  nome de diretório `KAZUMA_PS4`, 1024 blocos de 32 KiB (32 MiB).

Uma falha em serviço, montagem ou diretório lança diagnóstico e
interrompe o processo. Não há fallback para um caminho arbitrário,
não há exclusão de saves preexistentes e não há objetos proprietários.
Mount fica ativo durante o processo; ainda não validamos política de
sync/unmount e transições de suspensão do PS4.

O CI OpenOrbis v0.5.4/Clang 18 compila **27 arquivos públicos** e
verifica em `llvm-nm -C` a existência de `writable_root()` e
das 5 referências SDK acima. Host POSIX só simula um ponto de montagem
via diretório temporário e verifica falha em raiz inexistente,
escrita real em `user/save` e ausência de gravação em /app0.

**LIMITAÇÃO:** ABI compilada + link parcial NÃO provam que SaveData monta
na versão de firmware do usuário, que saves persistem corretamente, nem
que o jogo inicia. Sem PKG, eboot, NVN, SVE/STG ou link privado 1.916 AOT.
A execução PS4 real exigirá diagnóstico de retorno do serviço SaveData.
