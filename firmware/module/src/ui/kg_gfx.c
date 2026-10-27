#include <string.h>

#include "kg_gfx.h"

static const uint8_t bayer4[4][4] = {
    {0, 8, 2, 10},
    {12, 4, 14, 6},
    {3, 11, 1, 9},
    {15, 7, 13, 5},
};

void kg_clear(kg_fb fb) { memset(fb, 0, KG_FB_SIZE); }

void kg_pixel(kg_fb fb, int x, int y, enum kg_ink ink) {
    if (x < 0 || y < 0 || x >= KG_W || y >= KG_H) {
        return;
    }
    uint8_t *b = &fb[y * KG_STRIDE + x / 8];
    uint8_t m = 0x80 >> (x & 7);
    switch (ink) {
    case KG_CLEAR:
        *b &= ~m;
        break;
    case KG_SET:
        *b |= m;
        break;
    case KG_XOR:
        *b ^= m;
        break;
    }
}

bool kg_get(const kg_fb fb, int x, int y) {
    if (x < 0 || y < 0 || x >= KG_W || y >= KG_H) {
        return false;
    }
    return fb[y * KG_STRIDE + x / 8] & (0x80 >> (x & 7));
}

void kg_hline(kg_fb fb, int x, int y, int w, enum kg_ink ink) {
    for (int i = 0; i < w; i++) {
        kg_pixel(fb, x + i, y, ink);
    }
}

void kg_vline(kg_fb fb, int x, int y, int h, enum kg_ink ink) {
    for (int i = 0; i < h; i++) {
        kg_pixel(fb, x, y + i, ink);
    }
}

void kg_line(kg_fb fb, int x0, int y0, int x1, int y1, enum kg_ink ink) {
    int dx = x1 > x0 ? x1 - x0 : x0 - x1, sx = x0 < x1 ? 1 : -1;
    int dy = y1 > y0 ? y0 - y1 : y1 - y0, sy = y0 < y1 ? 1 : -1;
    int err = dx + dy;
    for (;;) {
        kg_pixel(fb, x0, y0, ink);
        if (x0 == x1 && y0 == y1) {
            break;
        }
        int e2 = 2 * err;
        if (e2 >= dy) {
            err += dy;
            x0 += sx;
        }
        if (e2 <= dx) {
            err += dx;
            y0 += sy;
        }
    }
}

void kg_fill(kg_fb fb, int x, int y, int w, int h, enum kg_ink ink) {
    for (int j = 0; j < h; j++) {
        kg_hline(fb, x, y + j, w, ink);
    }
}

void kg_box(kg_fb fb, int x, int y, int w, int h, enum kg_ink ink) {
    kg_hline(fb, x, y, w, ink);
    kg_hline(fb, x, y + h - 1, w, ink);
    kg_vline(fb, x, y + 1, h - 2, ink);
    kg_vline(fb, x + w - 1, y + 1, h - 2, ink);
}

void kg_dotted_hline(kg_fb fb, int x, int y, int w) {
    for (int i = 0; i < w; i += 2) {
        kg_pixel(fb, x + i, y, KG_SET);
    }
}

void kg_dotted_box(kg_fb fb, int x, int y, int w, int h) {
    for (int i = 0; i < w; i += 2) {
        kg_pixel(fb, x + i, y, KG_SET);
        kg_pixel(fb, x + i, y + h - 1, KG_SET);
    }
    for (int j = 2; j < h - 1; j += 2) {
        kg_pixel(fb, x, y + j, KG_SET);
        kg_pixel(fb, x + w - 1, y + j, KG_SET);
    }
}

bool kg_bayer(int x, int y, int level) { return bayer4[y & 3][x & 3] < level; }

void kg_dither(kg_fb fb, int x, int y, int w, int h, int level) {
    for (int j = y; j < y + h; j++) {
        for (int i = x; i < x + w; i++) {
            kg_pixel(fb, i, j, kg_bayer(i, j, level) ? KG_SET : KG_CLEAR);
        }
    }
}

void kg_blit(kg_fb fb, const struct kg_bitmap *bm, int x, int y, enum kg_ink ink) {
    int stride = (bm->w + 7) / 8;
    for (int j = 0; j < bm->h; j++) {
        for (int i = 0; i < bm->w; i++) {
            if (bm->rows[j * stride + i / 8] & (0x80 >> (i & 7))) {
                kg_pixel(fb, x + i, y + j, ink);
            }
        }
    }
}

int kg_glyph(const struct kg_font *font, char c, const uint8_t **rows) {
    if (c >= 'a' && c <= 'z') {
        c -= 'a' - 'A';
    }
    int i = (unsigned char)c - font->first;
    if (i < 0 || i >= font->count) {
        i = '?' - font->first;
    }
    *rows = &font->rows[i * font->height];
    return font->widths[i];
}

int kg_text_width(const struct kg_font *font, const char *text, int scale) {
    int w = 0;
    const uint8_t *rows;
    for (const char *p = text; *p; p++) {
        w += (kg_glyph(font, *p, &rows) + 1) * scale;
    }
    return w ? w - scale : 0;
}

int kg_text(kg_fb fb, const struct kg_font *font, const char *text, int x, int y, int scale,
            enum kg_ink ink) {
    const uint8_t *rows;
    for (const char *p = text; *p; p++) {
        int w = kg_glyph(font, *p, &rows);
        for (int j = 0; j < font->height; j++) {
            for (int i = 0; i < w; i++) {
                if (rows[j] & (0x80 >> i)) {
                    kg_fill(fb, x + i * scale, y + j * scale, scale, scale, ink);
                }
            }
        }
        x += (w + 1) * scale;
    }
    return x;
}

void kg_text_center(kg_fb fb, const struct kg_font *font, const char *text, int cx, int y,
                    int scale, enum kg_ink ink) {
    kg_text(fb, font, text, cx - kg_text_width(font, text, scale) / 2, y, scale, ink);
}

void kg_dissolve(kg_fb dst, const kg_fb src, int level) {
    for (int y = 0; y < KG_H; y++) {
        for (int x = 0; x < KG_W; x++) {
            if (kg_bayer(x, y, level)) {
                kg_pixel(dst, x, y, kg_get(src, x, y) ? KG_SET : KG_CLEAR);
            }
        }
    }
}
