// SPDX-License-Identifier: MIT
// Minimal PS4 forwarding provider, based on orbis-ports/orbis-compat's
// src/orbis_sysconf.cpp (MIT, commit 6922a7b6f4291a28edd239f1a4db50ed7aa00359).
//
// The platform headers map sysconf call sites to orbis_sysconf. Keep the
// underlying libc sysconf reachable and forward the query unchanged: in
// particular, _SC_PAGESIZE must remain a runtime query, not a guessed constant.
#include <unistd.h>

#ifdef sysconf
#undef sysconf
#endif

extern "C" long sysconf(int);

extern "C" long orbis_sysconf(int name) {
    return sysconf(name);
}
