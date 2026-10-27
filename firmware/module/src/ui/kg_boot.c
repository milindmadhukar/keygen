/*
 * The boot animation, after the cover of Martin Garrix's "Keygen": a stack of program windows with
 * boxed title bars. Left half: star dust, a crescent moon and the KEYGEN logo in outline, drawn in
 * by a scan line. Right half: a serial field and a GENERATE button between two spinning cubes; the
 * button presses itself and a serial churns out of noise and locks. Everything is a function of
 * the time since boot, so a frame can be drawn at any moment.
 */
#include <math.h>

#include "kg_assets.h"
#include "kg_boot.h"

#define WIN_W 122 /* the front window; the two behind it are offset 3 and 6 down and right */
#define WIN_H 58
#define DUST 90

static uint32_t hash(uint32_t x) {
    x ^= x >> 16;
    x *= 0x7feb352d;
    x ^= x >> 15;
    x *= 0x846ca68b;
    x ^= x >> 16;
    return x;
}

static float unit(uint32_t seed, int i) { return (hash(seed * 977 + i) & 0xffff) / 65535.0f; }

static float clamp01(float v) { return v < 0 ? 0 : v > 1 ? 1 : v; }

/* the windows pop up back to front, then the front one gets its title bar */
static void windows(kg_fb fb, uint32_t t, const char *title) {
    for (int k = 2; k >= 0; k--) {
        if (t < (uint32_t)(2 - k) * 120) {
            continue;
        }
        kg_fill(fb, k * 3, k * 3, WIN_W, WIN_H, KG_CLEAR);
        kg_box(fb, k * 3, k * 3, WIN_W, WIN_H, KG_SET);
    }
    if (t >= 240) {
        kg_box(fb, 2, 2, 107, 9, KG_SET);
        kg_text_center(fb, &kg_font5, title, 55, 3, 1, KG_SET);
        kg_box(fb, 111, 2, 9, 9, KG_SET);
        kg_blit(fb, &kg_icon_cross, 113, 4, KG_SET);
    }
}

/* star dust, thickest around the logo, twinkling */
static void dust(kg_fb fb, uint32_t t, float amount) {
    int n = (int)(DUST * amount);
    for (int i = 0; i < n; i++) {
        float u = unit(0xd057, i * 2), v = unit(0xd057, i * 2 + 1);
        int x, y;
        if (i % 3) {
            /* the nebula: two uniforms summed, a rough bell around the middle */
            x = 8 + (int)((u + unit(0xd057, i * 2 + 999)) * 50);
            y = 16 + (int)((v + unit(0xd057, i * 2 + 1999)) * 19);
        } else {
            x = 2 + (int)(u * (WIN_W - 4));
            y = 13 + (int)(v * (WIN_H - 15));
        }
        uint32_t h = hash(i * 7919 + t / 180);
        if ((h & 7) == 0) {
            continue;
        }
        kg_pixel(fb, x, y, KG_SET);
        if (i % 17 == 0 && (h & 8)) { /* a few bright stars, as crosses */
            kg_pixel(fb, x - 1, y, KG_SET);
            kg_pixel(fb, x + 1, y, KG_SET);
            kg_pixel(fb, x, y - 1, KG_SET);
            kg_pixel(fb, x, y + 1, KG_SET);
        }
    }
}

/* a crescent lit from the right, its dark side cut by a second circle; level 0-16 fades it in */
static void moon(kg_fb fb, int cx, int cy, int r, int level) {
    for (int y = cy - r; y <= cy + r; y++) {
        for (int x = cx - r; x <= cx + r; x++) {
            int dx = x - cx, dy = y - cy, ex = x - (cx - 5), ey = y - (cy - 2);
            if (dx * dx + dy * dy > r * r) {
                continue;
            }
            bool lit = ex * ex + ey * ey > r * r;
            bool crater = (hash(x * 131 + y * 71) & 15) == 0;
            if (lit && !crater && kg_bayer(x, y, level)) {
                kg_pixel(fb, x, y, KG_SET);
            } else {
                kg_pixel(fb, x, y, KG_CLEAR);
            }
        }
    }
}

/* the logo in outline, drawn in left to right up to column reveal, with a glint across it */
static void logo(kg_fb fb, int x0, int y0, int reveal, int glint) {
    const struct kg_bitmap *bm = &kg_icon_logo;
    int stride = (bm->w + 7) / 8;
#define LIT(i, j)                                                                                  \
    ((i) >= 0 && (j) >= 0 && (i) < bm->w && (j) < bm->h &&                                         \
     (bm->rows[(j) * stride + (i) / 8] & (0x80 >> ((i) & 7))))
    for (int j = -1; j <= bm->h; j++) {
        for (int i = -1; i <= bm->w && i < reveal; i++) {
            bool in = LIT(i, j);
            bool edge = in && !(LIT(i - 1, j) && LIT(i + 1, j) && LIT(i, j - 1) && LIT(i, j + 1));
            bool near = in || LIT(i - 1, j) || LIT(i + 1, j) || LIT(i, j - 1) || LIT(i, j + 1);
            int g = i - j / 2 - glint;
            bool shine = in && g >= 0 && g < 3;
            if (edge || shine) {
                kg_pixel(fb, x0 + i, y0 + j, KG_SET);
            } else if (near) {
                kg_pixel(fb, x0 + i, y0 + j, KG_CLEAR);
            }
        }
    }
#undef LIT
    if (reveal >= 0 && reveal < bm->w) {
        kg_vline(fb, x0 + reveal, y0 - 3, bm->h + 6, KG_SET);
    }
}

void kg_boot_left(kg_fb fb, uint32_t t, uint32_t seed) {
    (void)seed;
    windows(fb, t, "KEYGEN.EXE");
    if (t < 300) {
        return;
    }
    dust(fb, t, clamp01((t - 300) / 700.0f));
    moon(fb, 104, 20, 8, (int)(16 * clamp01((t - 500) / 600.0f)));

    const struct kg_bitmap *bm = &kg_icon_logo;
    int reveal = t < 800 ? -1 : (int)((t - 800) * bm->w / 800);
    int glint = t > 2000 ? (int)((t - 2000) / 8) % 160 - 20 : -100;
    logo(fb, (WIN_W - bm->w) / 2, 29, reveal, glint);
}

/* the cube's 8 corners and 12 edges */
static const int8_t corner[8][3] = {{-1, -1, -1}, {1, -1, -1}, {1, 1, -1}, {-1, 1, -1},
                                    {-1, -1, 1},  {1, -1, 1},  {1, 1, 1},  {-1, 1, 1}};
static const uint8_t edge[12][2] = {{0, 1}, {1, 2}, {2, 3}, {3, 0}, {4, 5}, {5, 6},
                                    {6, 7}, {7, 4}, {0, 4}, {1, 5}, {2, 6}, {3, 7}};

static void cube(kg_fb fb, int cx, int cy, float size, float t) {
    float a = t * 1.3f, b = t * 0.9f, c = t * 0.5f;
    int px[8], py[8];
    for (int i = 0; i < 8; i++) {
        float x = corner[i][0], y = corner[i][1], z = corner[i][2];
        float x1 = x * cosf(a) - z * sinf(a), z1 = x * sinf(a) + z * cosf(a);
        float y1 = y * cosf(b) - z1 * sinf(b), z2 = y * sinf(b) + z1 * cosf(b);
        float x2 = x1 * cosf(c) - y1 * sinf(c), y2 = x1 * sinf(c) + y1 * cosf(c);
        float k = size / (3.2f + z2) * 3.2f;
        px[i] = cx + (int)(x2 * k);
        py[i] = cy + (int)(y2 * k);
    }
    for (int i = 0; i < 12; i++) {
        kg_line(fb, px[edge[i][0]], py[edge[i][0]], px[edge[i][1]], py[edge[i][1]], KG_SET);
    }
}

#define PRESS_AT 1000
#define CHURN_AT 1150
#define DIGIT_MS 100
#define DIGITS 15

void kg_boot_right(kg_fb fb, uint32_t t, uint32_t seed) {
    windows(fb, t, "ACTIVATION");
    if (t < 300) {
        return;
    }
    float s = t / 1000.0f;
    cube(fb, 16, 43, 5, s);
    cube(fb, 106, 43, 5, -s * 1.1f);

    /* the serial, 4-4-4-3 digits like the cover's: noise until each digit locks */
    kg_text(fb, &kg_font3, "SERIAL:", 4, 14, 1, KG_SET);
    uint32_t locked_at = CHURN_AT + DIGITS * DIGIT_MS;
    bool flash = t > locked_at && t < locked_at + 600 && ((t - locked_at) / 150) % 2 == 0;
    kg_fill(fb, 3, 21, 116, 11, flash ? KG_SET : KG_CLEAR);
    kg_box(fb, 3, 21, 116, 11, KG_SET);
    if (t < CHURN_AT) {
        if ((t / 250) % 2) {
            kg_fill(fb, 6, 23, 5, 7, KG_SET);
        }
    } else {
        char serial[] = "0000-0000-0000-000";
        int digit = 0;
        for (int i = 0; serial[i]; i++) {
            if (serial[i] == '-') {
                continue;
            }
            bool locked = t > CHURN_AT + (uint32_t)(digit + 1) * DIGIT_MS;
            uint32_t v = locked ? hash(seed + digit) : hash(seed + digit * 31 + t / 40);
            serial[i] = '0' + v % 10;
            digit++;
        }
        kg_text_center(fb, &kg_font5, serial, 61, 23, 1, flash ? KG_CLEAR : KG_SET);
    }

    /* the button, pressed */
    bool pressed = t >= PRESS_AT && t < PRESS_AT + 160;
    kg_fill(fb, 34, 37, 54, 13, pressed ? KG_SET : KG_CLEAR);
    kg_box(fb, 34, 37, 54, 13, KG_SET);
    if (!pressed) {
        kg_box(fb, 36, 39, 50, 9, KG_SET);
    }
    kg_text_center(fb, &kg_font5, "GENERATE", 61, 40, 1, pressed ? KG_CLEAR : KG_SET);

    const char *what = t < PRESS_AT    ? ""
                       : t < locked_at ? (t / 300) % 2 ? "GENERATING.." : "GENERATING..."
                                       : "SERIAL ACCEPTED";
    kg_text_center(fb, &kg_font3, what, 61, 52, 1, KG_SET);
}
