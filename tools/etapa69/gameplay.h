#ifndef KAZUMA69_GAMEPLAY_H
#define KAZUMA69_GAMEPLAY_H
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float y, vy, time, scroll, damage_flash;
    float fence[3];
    unsigned int cleared, hits;
    int was_cross_down;
} ElephantGame;

typedef struct {
    int jumped, cleared_fence, hit_fence;
} ElephantEvents;

void elephant_reset(ElephantGame *g);
ElephantEvents elephant_step(ElephantGame *g, float dt, int cross_down);
#ifdef __cplusplus
}
#endif
#endif
