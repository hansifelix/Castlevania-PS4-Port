#include "gameplay.h"
#include <math.h>
#include <string.h>

void elephant_reset(ElephantGame *g) {
    memset(g, 0, sizeof(*g));
    g->fence[0] = 0.90f;
    g->fence[1] = 1.60f;
    g->fence[2] = 2.30f;
}
ElephantEvents elephant_step(ElephantGame *g, float dt, int cross_down) {
    ElephantEvents events = {0, 0, 0};
    if (dt < 0.f) dt = 0.f;
    if (dt > .040f) dt = .040f;
    /* Disparo apenas quando X passa de solto para pressionado. */
    if (cross_down && !g->was_cross_down && g->y <= .0001f) {
        g->vy = 2.10f;
        events.jumped = 1;
    }
    g->was_cross_down = cross_down != 0;
    g->time += dt;
    g->scroll += .68f * dt;
    g->y += g->vy * dt;
    g->vy -= 5.6f * dt;
    if (g->y <= 0.f) { g->y = 0.f; g->vy = 0.f; }
    if (g->damage_flash > 0.f) g->damage_flash -= dt;
    for (int i=0; i<3; ++i) {
        float previous = g->fence[i];
        g->fence[i] -= .68f * dt;
        /* Elefante no x=-0.50. Detectamos cada cerca uma unica vez. */
        if (previous > -0.50f && g->fence[i] <= -0.50f) {
            if (g->y > .21f) { ++g->cleared; ++events.cleared_fence; }
            else { ++g->hits; ++events.hit_fence; g->damage_flash = .28f; }
        }
        if (g->fence[i] < -1.16f) g->fence[i] += 2.10f;
    }
    return events;
}
