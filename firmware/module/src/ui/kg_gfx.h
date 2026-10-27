/*
 * A 128 x 64, 1-bit framebuffer and the drawing on it: pixels, lines, boxes, dither, bitmaps and
 * the pixel fonts. Rows of 16 bytes, most significant bit leftmost (LVGL's I1 layout).
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#define KG_W 128
#define KG_H 64
#define KG_STRIDE (KG_W / 8)
#define KG_FB_SIZE (KG_STRIDE * KG_H)

typedef uint8_t kg_fb[KG_FB_SIZE];

enum kg_ink { KG_CLEAR, KG_SET, KG_XOR };

struct kg_font {
    uint8_t height, first, count;
    const uint8_t *widths;
    const uint8_t *rows; /* height bytes a glyph, MSB first */
};

struct kg_bitmap {
    uint8_t w, h;
    const uint8_t *rows; /* (w + 7) / 8 bytes a row, MSB first */
};

void kg_clear(kg_fb fb);
void kg_pixel(kg_fb fb, int x, int y, enum kg_ink ink);
bool kg_get(const kg_fb fb, int x, int y);
void kg_hline(kg_fb fb, int x, int y, int w, enum kg_ink ink);
void kg_vline(kg_fb fb, int x, int y, int h, enum kg_ink ink);
void kg_line(kg_fb fb, int x0, int y0, int x1, int y1, enum kg_ink ink);
void kg_fill(kg_fb fb, int x, int y, int w, int h, enum kg_ink ink);
void kg_box(kg_fb fb, int x, int y, int w, int h, enum kg_ink ink);
/* every other pixel, for dotted rules and outlines */
void kg_dotted_hline(kg_fb fb, int x, int y, int w);
void kg_dotted_box(kg_fb fb, int x, int y, int w, int h);
/* a 4 x 4 Bayer dither of level 0 (dark) to 16 (lit) */
void kg_dither(kg_fb fb, int x, int y, int w, int h, int level);
bool kg_bayer(int x, int y, int level);

void kg_blit(kg_fb fb, const struct kg_bitmap *bm, int x, int y, enum kg_ink ink);
int kg_text_width(const struct kg_font *font, const char *text, int scale);
/* draws text with its top left corner at (x, y); returns the x after it */
int kg_text(kg_fb fb, const struct kg_font *font, const char *text, int x, int y, int scale,
            enum kg_ink ink);
void kg_text_center(kg_fb fb, const struct kg_font *font, const char *text, int cx, int y,
                    int scale, enum kg_ink ink);
/* one glyph's rows, for effects that place pixels themselves; returns its width */
int kg_glyph(const struct kg_font *font, char c, const uint8_t **rows);

/* dst = src where the dither at level (0..16) is lit, for dissolves */
void kg_dissolve(kg_fb dst, const kg_fb src, int level);
