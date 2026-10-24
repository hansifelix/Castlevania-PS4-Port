#include "gameplay.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    ElephantGame g;
    elephant_reset(&g);
    assert(g.fence[0] > 0 && g.y == 0);
    ElephantEvents a = elephant_step(&g,1.f/60.f,1);
    assert(a.jumped && g.y > 0);
    a = elephant_step(&g,1.f/60.f,1);
    assert(!a.jumped);
    for(int i=0;i<100;i++) elephant_step(&g,1.f/60.f,0);
    assert(g.y == 0);
    a = elephant_step(&g,1.f/60.f,1);
    assert(a.jumped);
    ElephantGame h; elephant_reset(&h);
    for(int i=0;i<200;i++) elephant_step(&h,1.f/60.f,0);
    assert(h.hits >= 1);
    assert(h.cleared == 0);
    printf("KAZUMA69: gameplay tests OK; grounded jumps, X edge, hit fences\n");
    return 0;
}
