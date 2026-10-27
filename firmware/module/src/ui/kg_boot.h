#pragma once

#include "kg_gfx.h"

/* draw the boot animation t ms after boot into a cleared framebuffer */
void kg_boot_left(kg_fb fb, uint32_t t, uint32_t seed);
void kg_boot_right(kg_fb fb, uint32_t t, uint32_t seed);
