/*
 * Keygen's OLED screens, as plain C on a 1-bit framebuffer: the firmware fills a kg_state from ZMK
 * (src/display.c) and the simulator (sim/kg_sim.c) from a script, and both call kg_ui_render().
 *
 * Left half: output, Bluetooth profiles, both batteries, the link, layer, modifiers and WPM.
 * Right half: the link, its battery, the layer large, a WPM graph, and the lighting menu.
 */
#pragma once

#include "kg_gfx.h"

#define KG_PROFILES 5
#define KG_LAYERS 5
#define KG_BATTERY_UNKNOWN 0xff
#define KG_BOOT_MS 5000

enum kg_side { KG_SIDE_LEFT, KG_SIDE_RIGHT };
enum kg_output { KG_OUT_USB, KG_OUT_BLE };
enum kg_profile { KG_PROFILE_OPEN, KG_PROFILE_PAIRED };
enum kg_field { KG_FIELD_POWER, KG_FIELD_EFFECT, KG_FIELD_HUE, KG_FIELD_SAT, KG_FIELD_BRIGHT,
                KG_FIELD_SPEED, KG_FIELD_COUNT };

/* ZMK's underglow: effect is SOLID, BREATHE, SPECTRUM or SWIRL, hue 0-359, sat 0-100, brt
 * 0-brt_max. The speed can't be read back, so only the direction of its last change is kept. */
struct kg_light {
    bool on;
    uint8_t effect;
    uint16_t hue;
    uint8_t sat, brt, brt_max;
    int8_t speed_step;
};

struct kg_state {
    uint8_t output;                /* enum kg_output */
    uint8_t profile;               /* the active Bluetooth profile, 0-4 */
    uint8_t profiles[KG_PROFILES]; /* enum kg_profile */
    bool host_connected;           /* the active profile is connected */
    uint8_t battery[2];            /* percent, left and right; KG_BATTERY_UNKNOWN */
    bool usb_power;                /* this half is on USB power */
    bool linked;                   /* the halves are connected */
    uint8_t layer;                 /* the highest active layer */
    uint8_t mods;                  /* HID modifier bits, both sides */
    bool caps;                     /* caps lock, from the host */
    uint8_t wpm;
    struct kg_light light;
    bool menu_open;
    uint8_t menu_field;            /* enum kg_field */
    uint32_t menu_stamp;           /* ms of the last menu input */
};

void kg_ui_init(enum kg_side side, uint32_t seed, uint32_t now);
/* a key press ends the boot animation early */
void kg_ui_skip_boot(uint32_t now);
/* the screen comes back from idle: a short CRT power-on */
void kg_ui_wake(uint32_t now);
/* draws the screen at time now (ms); returns the ms until the next frame is due, 0 when only a
 * change of state needs one */
uint32_t kg_ui_render(kg_fb fb, const struct kg_state *s, uint32_t now);

extern const char *const kg_effect_names[4];
