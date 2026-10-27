/*
 * Runs the OLED screens (../src/ui) on a PC, through scripted scenes, and writes each scene's
 * frames for tools/render_oled.py: per frame a little-endian uint16 of milliseconds, then the
 * 1024-byte framebuffer. A scene's still is its last frame.
 *
 *     kg_sim OUTDIR      # OUTDIR/<scene>.frames
 */
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "kg_ui.h"

#define STEP 40
#define SEED 0x7f3a91c2u

static FILE *out;

static void emit(const kg_fb fb, unsigned ms) {
    uint8_t d[2] = {ms & 0xff, ms >> 8};
    fwrite(d, 1, 2, out);
    fwrite(fb, 1, KG_FB_SIZE, out);
}

/* the state in the renders: both halves on USB power, profile 1 connected, Base layer, idle */
static struct kg_state still(void) {
    struct kg_state s = {
        .output = KG_OUT_BLE,
        .profile = 0,
        .profiles = {KG_PROFILE_PAIRED, KG_PROFILE_PAIRED, KG_PROFILE_OPEN, KG_PROFILE_OPEN,
                     KG_PROFILE_OPEN},
        .host_connected = true,
        .battery = {87, 64},
        .usb_power = true,
        .linked = true,
        .light = {.on = true, .effect = 3, .hue = 200, .sat = 100, .brt = 30, .brt_max = 40},
    };
    return s;
}

typedef void (*script_fn)(struct kg_state *s, int t, uint32_t now);

/* plays a scene from t = 0 to length; warmup ms of it run before recording starts */
static void scene(const char *dir, const char *name, enum kg_side side, bool boot, int warmup,
                  int length, script_fn script) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s.frames", dir, name);
    out = fopen(path, "wb");
    if (!out) {
        perror(path);
        return;
    }
    uint32_t base = boot ? 0 : KG_BOOT_MS;
    kg_ui_init(side, SEED, 0);
    kg_fb fb;
    struct kg_state s = still();
    for (int t = -warmup; t < length; t += STEP) {
        uint32_t now = base + warmup + t;
        if (!boot && t == 0) {
            kg_ui_wake(now);
        }
        if (script) {
            script(&s, t, now);
        }
        kg_ui_render(fb, &s, now);
        if (t >= 0) {
            emit(fb, STEP);
        }
    }
    fclose(out);
}

#define AT(a, b) (t >= (a) && t < (b))

static void left_script(struct kg_state *s, int t, uint32_t now) {
    (void)now;
    s->wpm = t < 400 ? 0 : t < 3000 ? (t - 400) / 40 : 65;
    s->layer = AT(1200, 2000) ? 1 : AT(3200, 4000) ? 2 : AT(4400, 5200) ? 3 : 0;
    s->mods = AT(1300, 1900) ? 0x08 : AT(2300, 2900) ? 0x02 : AT(3400, 3900) ? 0x01 : 0;
    if (AT(4400, 5200) && t >= 4700) {
        s->profile = 1;
        s->host_connected = t >= 6000;
    }
    s->caps = AT(6400, 8000);
    s->output = AT(7200, 8800) ? KG_OUT_USB : KG_OUT_BLE;
    s->linked = !AT(9000, 10400);
}

static void right_script(struct kg_state *s, int t, uint32_t now) {
    (void)now;
    if (t < 0) {
        /* forty seconds of typing, so the graph has a history */
        float x = t / 1000.0f;
        s->wpm = (uint8_t)(52 + 14 * sinf(x * 0.45f) + 8 * sinf(x * 1.7f + 1) + 4 * sinf(x * 3.1f));
        return;
    }
    s->wpm = t < 6000 ? 60 + (t / 700) % 4 * 6 : t < 7000 ? 30 : 0;
    s->layer = AT(1000, 2000) ? 1 : AT(2600, 3400) ? 2 : AT(4000, 4800) ? 3 : 0;
    s->caps = AT(5200, 6400);
}

static void menu_script(struct kg_state *s, int t, uint32_t now) {
    static const struct {
        int at;
        char op; /* o open, c close, n next, + up, - down, b battery, u usb */
    } steps[] = {
        {600, 'o'},  {1300, 'n'}, {1800, '+'}, {2300, '+'}, {2800, '+'}, {3400, 'n'},
        {3600, '+'}, {3700, '+'}, {3800, '+'}, {3900, '+'}, {4000, '+'}, {4100, '+'},
        {4200, '+'}, {4300, '+'}, {4800, 'n'}, {5100, '-'}, {5300, '-'}, {5500, '-'},
        {6000, 'n'}, {6300, '+'}, {6600, '-'}, {6800, '-'}, {7000, '-'}, {7500, 'n'},
        {7800, '+'}, {8400, '-'}, {9000, 'b'}, {10600, 'u'}, {11200, 'c'},
    };
    if (t == -STEP || t < 0) {
        s->light = (struct kg_light){.on = true, .effect = 0, .hue = 0, .sat = 100, .brt = 30,
                                     .brt_max = 40};
        s->menu_open = false;
        s->menu_field = 0;
        return;
    }
    for (unsigned i = 0; i < sizeof(steps) / sizeof(steps[0]); i++) {
        if (t != steps[i].at) {
            continue;
        }
        struct kg_light *l = &s->light;
        int d = steps[i].op == '+' ? 1 : -1;
        switch (steps[i].op) {
        case 'o':
            s->menu_open = true;
            s->menu_field = KG_FIELD_POWER;
            break;
        case 'c':
            s->menu_open = false;
            break;
        case 'n':
            s->menu_field = (s->menu_field + 1) % KG_FIELD_COUNT;
            break;
        case 'b':
            s->usb_power = false;
            break;
        case 'u':
            s->usb_power = true;
            break;
        default:
            switch (s->menu_field) {
            case KG_FIELD_POWER:
                l->on = !l->on;
                break;
            case KG_FIELD_EFFECT:
                l->effect = (l->effect + 4 + d) % 4;
                break;
            case KG_FIELD_HUE:
                l->hue = (l->hue + 360 + d * 20) % 360;
                break;
            case KG_FIELD_SAT:
                l->sat = (uint8_t)(l->sat + d * 10);
                break;
            case KG_FIELD_BRIGHT:
                l->brt = (uint8_t)(l->brt + d * 5);
                break;
            case KG_FIELD_SPEED:
                l->speed_step = (int8_t)d;
                break;
            }
        }
        s->menu_stamp = now;
    }
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s OUTDIR\n", argv[0]);
        return 2;
    }
    const char *dir = argv[1];
    scene(dir, "boot-left", KG_SIDE_LEFT, true, 0, KG_BOOT_MS + 800, NULL);
    scene(dir, "boot-right", KG_SIDE_RIGHT, true, 0, KG_BOOT_MS + 800, NULL);
    scene(dir, "left", KG_SIDE_LEFT, false, 0, 11000, left_script);
    scene(dir, "right", KG_SIDE_RIGHT, false, 40000, 17000, right_script);
    scene(dir, "light-menu", KG_SIDE_RIGHT, false, 9000, 12000, menu_script);
    scene(dir, "still-left", KG_SIDE_LEFT, false, 0, 1000, NULL);
    scene(dir, "still-right", KG_SIDE_RIGHT, false, 0, 1000, NULL);
    return 0;
}
