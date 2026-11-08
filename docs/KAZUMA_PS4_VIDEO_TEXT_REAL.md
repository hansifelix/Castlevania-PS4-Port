# Castlevania PS4 — native video resolution text (1.1.0 profile)

Public MIT upstream: `games/castlevania/video_options.cpp` at pinned commit
`4043f21bb4f656d34cd17ba070238c7728d00631`.

The callback `nx_castlevania_video_text(nx::CPU&, void(*)(nx::CPU&))`
reuses the original game's UTF-16 System.String allocator and only substitutes
a legacy "3840x2160" label with the actual native PS4 output width × height.
It tolerates spacing and Unicode multiplication signs as in the original.
If VideoOut is uninitialized, it fails explicitly instead of inventing a size.
All other labels and native 4K resolutions keep their original game behavior.

Host CTest uses synthetic CPU/guest memory and simulates the real guest string
allocator at `NX_BASE+0x418f160`. The separate GitHub Actions workflow checks
the implementation against *real pinned nx headers* and the OpenOrbis v0.5.4
toolchain, without importing commercial game data.

This is not a PS4 renderer or a working game. The private AOT link still needs
to verify this symbol, and NVN/SVE/STG/executable-image gates remain open.
