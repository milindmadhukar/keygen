#include <string.h>

#include "kg_assets.h"
#include "kg_boot.h"
#include "kg_ui.h"

#define HISTORY 64       /* WPM samples on the right half's graph, one a second */
#define FADE_MS 400      /* boot animation into the status screen */
#define MENU_FADE_MS 160 /* status screen to and from the lighting menu */
#define SLIDE_MS 180     /* the right half's layer name changing */
#define WAKE_MS 280      /* the CRT power-on after idle */

/* layer names: short for the left half's strip, long with a hint for the right half */
static const char *const layer_short[KG_LAYERS] = {"BASE", "NAV", "FN", "SYS", "LED"};
static const char *const layer_long[KG_LAYERS] = {"BASE", "NAV", "FN", "SYSTEM", "LIGHT"};
static const char *const layer_hint[KG_LAYERS] = {
    "QWERTY", "ARROWS . HOME . END", "F-KEYS . NUMPAD . MEDIA", "BLUETOOTH . LEDS . RESET",
    "THE KNOB SETS THE LEDS"};

const char *const kg_effect_names[4] = {"SOLID", "BREATHE", "SPECTRUM", "SWIRL"};
static const char *const field_names[KG_FIELD_COUNT] = {"POWER", "EFFECT", "HUE",
                                                        "SAT",   "BRIGHT", "SPEED"};

static struct {
    enum kg_side side;
    uint32_t seed;
    uint32_t boot_at, wake_at;
    bool booting, woken;
    uint8_t history[HISTORY];
    uint32_t history_at;
    uint8_t layer, layer_from;
    uint32_t layer_at;
    bool menu;
    uint32_t menu_at;
} ui;

static kg_fb scratch;

static const char *num(char *buf, unsigned v, const char *suffix) {
    char tmp[6];
    int n = 0;
    do {
        tmp[n++] = '0' + v % 10;
        v /= 10;
    } while (v && n < 5);
    int i = 0;
    while (n) {
        buf[i++] = tmp[--n];
    }
    while (*suffix) {
        buf[i++] = *suffix++;
    }
    buf[i] = 0;
    return buf;
}

/* a battery with its fill, a bolt before it on USB power, and its percent ending at right */
static void battery(kg_fb fb, int x, int y, int right, uint8_t pct, bool charging) {
    char buf[8];
    if (charging) {
        kg_blit(fb, &kg_icon_bolt, x, y + 1, KG_SET);
    }
    kg_box(fb, x + 7, y, 14, 9, KG_SET);
    kg_fill(fb, x + 21, y + 3, 2, 3, KG_SET);
    const char *text = "--";
    if (pct != KG_BATTERY_UNKNOWN) {
        kg_fill(fb, x + 9, y + 2, 10 * (pct > 100 ? 100 : pct) / 100, 5, KG_SET);
        text = num(buf, pct, "%");
    }
    kg_text(fb, &kg_font3, text, right - kg_text_width(&kg_font3, text, 1), y + 2, 1, KG_SET);
}

static void history_update(const struct kg_state *s, uint32_t now) {
    if (now - ui.history_at > HISTORY * 1000) {
        memset(ui.history, 0, sizeof(ui.history));
        ui.history_at = now;
    }
    while (now - ui.history_at >= 1000) {
        memmove(ui.history, ui.history + 1, HISTORY - 1);
        ui.history[HISTORY - 1] = s->wpm;
        ui.history_at += 1000;
    }
}

static bool history_idle(const struct kg_state *s) {
    if (s->wpm) {
        return false;
    }
    for (int i = HISTORY - 8; i < HISTORY; i++) {
        if (ui.history[i]) {
            return false;
        }
    }
    return true;
}

/* left half: output, profiles, batteries, link and caps, layers, modifiers, WPM */
static uint32_t draw_left(kg_fb fb, const struct kg_state *s, uint32_t now) {
    char buf[8];
    uint32_t next = 0;
    bool blink = (now / 500) % 2;

    if (s->output == KG_OUT_USB) {
        kg_fill(fb, 0, 0, 21, 9, KG_SET);
        kg_text(fb, &kg_font5, "USB", 2, 1, 1, KG_CLEAR);
    } else {
        kg_blit(fb, &kg_icon_bt, 0, 0, KG_SET);
        kg_text(fb, &kg_font5, num(buf, s->profile + 1, ""), 8, 1, 1, KG_SET);
        if (s->host_connected) {
            kg_blit(fb, &kg_icon_check, 16, 1, KG_SET);
        } else if (blink) {
            kg_blit(fb, &kg_icon_cross, 17, 2, KG_SET);
        }
        if (!s->host_connected) {
            next = 500;
        }
    }

    if (s->linked) {
        kg_blit(fb, &kg_icon_link, 88, 1, KG_SET);
    } else {
        if (blink) {
            kg_blit(fb, &kg_icon_link, 88, 1, KG_SET);
        }
        next = 500;
    }
    if (s->caps) {
        kg_fill(fb, 101, 0, 27, 9, KG_SET);
        kg_text(fb, &kg_font5, "CAPS", 103, 1, 1, KG_CLEAR);
    }
    kg_dotted_hline(fb, 0, 11, KG_W);

    /* the five Bluetooth profiles: lit when active, outlined when paired, dotted when open */
    for (int i = 0; i < KG_PROFILES; i++) {
        int x = i * 15;
        bool active = s->profile == i;
        if (active) {
            kg_fill(fb, x, 14, 13, 11, KG_SET);
        } else if (s->profiles[i] == KG_PROFILE_PAIRED) {
            kg_box(fb, x, 14, 13, 11, KG_SET);
        } else {
            kg_dotted_box(fb, x, 14, 13, 11);
        }
        kg_text(fb, &kg_font5, num(buf, i + 1, ""), x + 4, 16, 1, active ? KG_CLEAR : KG_SET);
    }
    const char *what;
    if (s->output == KG_OUT_USB) {
        what = "USB . BT STANDBY";
    } else if (s->host_connected) {
        what = "CONNECTED";
    } else if (s->profiles[s->profile] == KG_PROFILE_OPEN) {
        what = "PAIRING...";
    } else {
        what = "SEARCHING...";
    }
    kg_text(fb, &kg_font3, what, 0, 29, 1, KG_SET);

    /* both batteries; the bolt for this half on USB power */
    kg_text(fb, &kg_font5, "L", 82, 15, 1, KG_SET);
    kg_text(fb, &kg_font5, "R", 82, 27, 1, KG_SET);
    battery(fb, 88, 14, KG_W, s->battery[0], s->usb_power);
    battery(fb, 88, 26, KG_W, s->linked ? s->battery[1] : KG_BATTERY_UNKNOWN, false);
    kg_dotted_hline(fb, 0, 39, KG_W);

    /* the layers, the active one lit */
    int widths[KG_LAYERS], total = 0;
    for (int i = 0; i < KG_LAYERS; i++) {
        widths[i] = kg_text_width(&kg_font5, layer_short[i], 1) + 5;
        total += widths[i];
    }
    int gap = (KG_W - total) / (KG_LAYERS - 1), x = (KG_W - total - gap * (KG_LAYERS - 1)) / 2;
    for (int i = 0; i < KG_LAYERS; i++) {
        bool active = s->layer == i;
        if (active) {
            kg_fill(fb, x, 42, widths[i], 11, KG_SET);
        }
        kg_text(fb, &kg_font5, layer_short[i], x + 3, 44, 1, active ? KG_CLEAR : KG_SET);
        x += widths[i] + gap;
    }

    /* modifiers held, lit */
    static const struct kg_bitmap *const mod_icons[4] = {&kg_icon_shift, &kg_icon_ctrl,
                                                         &kg_icon_alt, &kg_icon_super};
    static const uint8_t mod_bits[4] = {0x22, 0x11, 0x44, 0x88};
    for (int i = 0; i < 4; i++) {
        int mx = i * 16;
        bool held = s->mods & mod_bits[i];
        if (held) {
            kg_fill(fb, mx, 55, 14, 9, KG_SET);
        } else {
            kg_dotted_box(fb, mx, 55, 14, 9);
        }
        kg_blit(fb, mod_icons[i], mx + 4, 56, held ? KG_CLEAR : KG_SET);
    }
    kg_text(fb, &kg_font3, "WPM", 92, 57, 1, KG_SET);
    const char *wpm = num(buf, s->wpm, "");
    kg_text(fb, &kg_font5, wpm, KG_W - kg_text_width(&kg_font5, wpm, 1), 56, 1, KG_SET);
    return next;
}

/* right half: link and battery, the layer large, the WPM graph or, idle, a starfield */
static uint32_t draw_right(kg_fb fb, const struct kg_state *s, uint32_t now) {
    uint32_t next = 0;

    if (s->layer != ui.layer) {
        ui.layer_from = ui.layer;
        ui.layer = s->layer;
        ui.layer_at = now;
    }
    uint32_t dt = now - ui.layer_at;
    if (dt < SLIDE_MS) {
        int off = 22 * (int)dt / SLIDE_MS;
        kg_text_center(fb, &kg_font5, layer_long[ui.layer_from], 64, 16 - off, 2, KG_SET);
        kg_text_center(fb, &kg_font5, layer_long[ui.layer], 64, 38 - off, 2, KG_SET);
        next = 30;
    } else {
        const char *name = layer_long[ui.layer];
        int w = kg_text_width(&kg_font5, name, 2);
        kg_text_center(fb, &kg_font5, name, 64, 16, 2, KG_SET);
        kg_hline(fb, 2, 22, 64 - w / 2 - 8, KG_SET);
        kg_hline(fb, 64 + w / 2 + 6, 22, 64 - w / 2 - 8, KG_SET);
        kg_text_center(fb, &kg_font3, layer_hint[ui.layer], 64, 33, 1, KG_SET);
    }
    kg_fill(fb, 0, 0, KG_W, 12, KG_CLEAR);
    kg_fill(fb, 0, 39, KG_W, KG_H - 39, KG_CLEAR);

    if (s->linked) {
        kg_blit(fb, &kg_icon_link, 0, 1, KG_SET);
        kg_text(fb, &kg_font5, "LINKED", 12, 1, 1, KG_SET);
    } else {
        if ((now / 500) % 2) {
            kg_blit(fb, &kg_icon_link, 0, 1, KG_SET);
        }
        kg_text(fb, &kg_font5, "SEARCH", 12, 1, 1, KG_SET);
        next = 500;
    }
    if (s->caps) {
        kg_fill(fb, 53, 0, 27, 9, KG_SET);
        kg_text(fb, &kg_font5, "CAPS", 55, 1, 1, KG_CLEAR);
    }
    battery(fb, 87, 0, KG_W, s->battery[1], s->usb_power);
    kg_dotted_hline(fb, 0, 11, KG_W);
    kg_dotted_hline(fb, 0, 40, KG_W);

    if (history_idle(s)) {
        /* parallax stars drifting left */
        for (int i = 0; i < 28; i++) {
            uint32_t h = (uint32_t)i * 2654435761u;
            int speed = 1 + (h >> 8) % 3;
            int y = 43 + (h >> 12) % 20;
            int x = KG_W - 1 - (int)(((h >> 4) + now / 125 * speed) % KG_W);
            kg_hline(fb, x, y, speed == 3 ? 2 : 1, KG_SET);
        }
        if (next == 0 || next > 125) {
            next = 125;
        }
    } else {
        for (int i = 0; i < HISTORY; i++) {
            int v = ui.history[i] > 120 ? 120 : ui.history[i];
            int h = v * 20 / 120;
            if (h) {
                kg_fill(fb, i * 2, 64 - h, 1, h, KG_SET);
            }
        }
        char buf[8];
        const char *wpm = num(buf, s->wpm, "");
        int w = kg_text_width(&kg_font5, wpm, 1);
        kg_fill(fb, 0, 42, 16 + w, 9, KG_CLEAR);
        kg_text(fb, &kg_font3, "WPM", 0, 44, 1, KG_SET);
        kg_text(fb, &kg_font5, wpm, 14, 43, 1, KG_SET);
        if (next == 0 || next > 1000) {
            next = 1000;
        }
    }
    return next;
}

static const char *hue_name(const struct kg_light *l) {
    if (l->sat < 15) {
        return "WHITE";
    }
    static const struct {
        uint16_t below;
        const char *name;
    } hues[] = {{15, "RED"},   {45, "ORANGE"}, {70, "YELLOW"}, {160, "GREEN"}, {200, "CYAN"},
                {260, "BLUE"}, {300, "PURPLE"}, {340, "PINK"},  {361, "RED"}};
    for (unsigned i = 0; i < sizeof(hues) / sizeof(hues[0]); i++) {
        if (l->hue < hues[i].below) {
            return hues[i].name;
        }
    }
    return "RED";
}

static void bar(kg_fb fb, int x, int y, int w, int v, int max) {
    kg_box(fb, x, y, w, 7, KG_SET);
    kg_fill(fb, x + 2, y + 2, (w - 4) * v / (max ? max : 1), 3, KG_SET);
}

/* right half: the lighting menu, four of its fields at a time */
static uint32_t draw_menu(kg_fb fb, const struct kg_state *s, uint32_t now) {
    char buf[8];
    const struct kg_light *l = &s->light;
    uint32_t next = 0;

    kg_fill(fb, 0, 0, KG_W, 9, KG_SET);
    kg_text(fb, &kg_font5, "LIGHTING", 2, 1, 1, KG_CLEAR);
    num(buf, s->menu_field + 1, "/6");
    kg_text(fb, &kg_font3, buf, KG_W - 2 - kg_text_width(&kg_font3, buf, 1), 2, 1, KG_CLEAR);

    int first = s->menu_field < 1 ? 0 : s->menu_field - 1;
    if (first > KG_FIELD_COUNT - 4) {
        first = KG_FIELD_COUNT - 4;
    }
    for (int row = 0; row < 4; row++) {
        int f = first + row, y = 11 + row * 11;
        bool sel = f == s->menu_field;
        if (sel) {
            kg_fill(fb, 0, y, 41, 10, KG_SET);
        }
        kg_text(fb, &kg_font5, field_names[f], 2, y + 2, 1, sel ? KG_CLEAR : KG_SET);
        int vx = 45;
        switch (f) {
        case KG_FIELD_POWER:
            kg_box(fb, vx, y + 1, 19, 9, KG_SET);
            kg_fill(fb, l->on ? vx + 10 : vx + 2, y + 3, 7, 5, KG_SET);
            kg_text(fb, &kg_font5, l->on ? "ON" : "OFF", vx + 24, y + 2, 1, KG_SET);
            break;
        case KG_FIELD_EFFECT:
            if (sel) {
                kg_blit(fb, &kg_icon_left, vx, y + 3, KG_SET);
                kg_blit(fb, &kg_icon_right, KG_W - 4, y + 3, KG_SET);
            }
            kg_text_center(fb, &kg_font5, kg_effect_names[l->effect & 3], 86, y + 2, 1, KG_SET);
            break;
        case KG_FIELD_HUE:
            kg_box(fb, vx, y + 1, 50, 8, KG_SET);
            for (int i = 0; i < 46; i++) {
                if ((i % 6) == 0) {
                    kg_pixel(fb, vx + 2 + i, y + 7, KG_SET);
                }
            }
            kg_fill(fb, vx + 2 + l->hue * 45 / 359 - 1, y + 2, 3, 5, KG_SET);
            kg_text(fb, &kg_font3, hue_name(l), vx + 53, y + 3, 1, KG_SET);
            break;
        case KG_FIELD_SAT:
            bar(fb, vx, y + 2, 50, l->sat, 100);
            kg_text(fb, &kg_font3, num(buf, l->sat, "%"), vx + 53, y + 3, 1, KG_SET);
            break;
        case KG_FIELD_BRIGHT:
            bar(fb, vx, y + 2, 50, l->brt, l->brt_max);
            kg_text(fb, &kg_font3, num(buf, l->brt * 100 / (l->brt_max ? l->brt_max : 1), "%"),
                    vx + 53, y + 3, 1, KG_SET);
            break;
        case KG_FIELD_SPEED: {
            bool recent = s->menu_stamp && now - s->menu_stamp < 400 && sel;
            const char *what = !recent || !l->speed_step ? "SLOWER . FASTER"
                               : l->speed_step > 0      ? "FASTER"
                                                        : "SLOWER";
            kg_text_center(fb, &kg_font3, what, 86, y + 3, 1, KG_SET);
            if (recent) {
                next = 100;
            }
            break;
        }
        }
    }

    if (!s->usb_power) {
        if ((now / 600) % 2) {
            kg_fill(fb, 0, 56, KG_W, 8, KG_SET);
            kg_text_center(fb, &kg_font3, "LEDS LIGHT ON USB POWER", 64, 57, 1, KG_CLEAR);
        } else {
            kg_text_center(fb, &kg_font3, "LEDS LIGHT ON USB POWER", 64, 57, 1, KG_SET);
        }
        next = 600;
    } else {
        kg_dotted_hline(fb, 0, 55, KG_W);
        kg_text_center(fb, &kg_font3, "TURN: SET   PRESS: NEXT", 64, 58, 1, KG_SET);
    }
    return next;
}

static uint32_t draw_status(kg_fb fb, const struct kg_state *s, uint32_t now, bool menu) {
    kg_clear(fb);
    if (ui.side == KG_SIDE_LEFT) {
        return draw_left(fb, s, now);
    }
    return menu ? draw_menu(fb, s, now) : draw_right(fb, s, now);
}

void kg_ui_init(enum kg_side side, uint32_t seed, uint32_t now) {
    memset(&ui, 0, sizeof(ui));
    ui.side = side;
    ui.seed = seed;
    ui.boot_at = now;
    ui.booting = true;
    ui.history_at = now;
}

void kg_ui_skip_boot(uint32_t now) {
    if (ui.booting && now - ui.boot_at < KG_BOOT_MS - FADE_MS) {
        ui.boot_at = now - (KG_BOOT_MS - FADE_MS);
    }
}

void kg_ui_wake(uint32_t now) {
    ui.wake_at = now;
    ui.woken = true;
}

/* the CRT power-on: a line across the middle that opens up into the picture */
static void crt(kg_fb fb, uint32_t t) {
    int half = (int)t * 40 / WAKE_MS - 6;
    if (half < 1) {
        int w = (int)t * KG_W / (WAKE_MS * 6 / 40);
        kg_clear(fb);
        kg_hline(fb, 64 - w / 2, 32, w, KG_SET);
        return;
    }
    for (int y = 0; y < KG_H; y++) {
        if (y < 32 - half || y > 31 + half) {
            kg_hline(fb, 0, y, KG_W, KG_CLEAR);
        }
    }
}

uint32_t kg_ui_render(kg_fb fb, const struct kg_state *s, uint32_t now) {
    history_update(s, now);

    if (ui.booting) {
        uint32_t t = now - ui.boot_at;
        if (t < KG_BOOT_MS) {
            kg_clear(fb);
            if (ui.side == KG_SIDE_LEFT) {
                kg_boot_left(fb, t, ui.seed);
            } else {
                kg_boot_right(fb, t, ui.seed);
            }
            if (t > KG_BOOT_MS - FADE_MS) {
                draw_status(scratch, s, now, s->menu_open);
                kg_dissolve(fb, scratch, (t - (KG_BOOT_MS - FADE_MS)) * 17 / FADE_MS);
            }
            ui.menu = s->menu_open;
            ui.layer = s->layer;
            return 40;
        }
        ui.booting = false;
        ui.layer = s->layer;
        ui.menu = s->menu_open;
    }

    if (s->menu_open != ui.menu) {
        ui.menu = s->menu_open;
        ui.menu_at = now;
    }
    uint32_t next;
    if (ui.side == KG_SIDE_RIGHT && ui.menu_at && now - ui.menu_at < MENU_FADE_MS) {
        draw_status(fb, s, now, !ui.menu);
        draw_status(scratch, s, now, ui.menu);
        kg_dissolve(fb, scratch, (now - ui.menu_at) * 17 / MENU_FADE_MS);
        next = 30;
    } else {
        next = draw_status(fb, s, now, ui.menu);
    }

    if (ui.woken) {
        uint32_t t = now - ui.wake_at;
        if (t < WAKE_MS) {
            crt(fb, t);
            next = 20;
        } else {
            ui.woken = false;
        }
    }
    return next;
}
