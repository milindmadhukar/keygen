/*
 * Keygen: the per-key lighting on battery.
 *
 * On USB the lighting is ZMK's own. On battery it stays off unless lighting on battery is allowed
 * (&kg_bl, saved in settings). When allowed, its brightness is capped, halved on a low cell and the
 * lighting goes off on a nearly empty one. Whenever the lighting is off, so is the LED supply (the
 * 5 V boost, through ZMK's ext-power on P0.08): dark SK6812s still draw about 1 mA each.
 *
 * ZMK's idle handler can turn the lighting back on after a wake, so every relevant event schedules
 * one re-check of the whole policy rather than reacting to the event alone.
 */

#define DT_DRV_COMPAT keygen_behavior_battery_lighting

#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/settings/settings.h>
#include <zephyr/logging/log.h>

#include <drivers/behavior.h>
#include <drivers/ext_power.h>

#include <zmk/battery.h>
#include <zmk/behavior.h>
#include <zmk/event_manager.h>
#include <zmk/events/activity_state_changed.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/rgb_underglow.h>
#include <zmk/usb.h>

LOG_MODULE_REGISTER(keygen_battery_lighting, CONFIG_ZMK_LOG_LEVEL);

#define BRT_CAP CONFIG_KEYGEN_BATTERY_LIGHTING_BRT
#define DIM_BELOW CONFIG_KEYGEN_BATTERY_LIGHTING_DIM_BELOW
#define OFF_BELOW CONFIG_KEYGEN_BATTERY_LIGHTING_OFF_BELOW

static const struct device *const ext_power = DEVICE_DT_GET(DT_INST(0, zmk_ext_power_generic));

static bool allow;          /* lighting may run on battery; saved */
static bool forced_off;     /* this module turned the lighting off on battery */
static bool restore_on;     /* ...and it was on, so turn it back on when allowed or on USB */
static int saved_brt = -1;  /* the brightness before this module capped it, or -1 */

static void enforce(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(enforce_work, enforce);

static void schedule(int ms) { k_work_reschedule(&enforce_work, K_MSEC(ms)); }

static void set_brt(int b) {
    struct zmk_led_hsb c = zmk_rgb_underglow_calc_brt(0);
    if (c.b != b) {
        c.b = b;
        zmk_rgb_underglow_set_hsb(c);
    }
}

static void restore_brt(void) {
    if (saved_brt >= 0) {
        set_brt(saved_brt);
        saved_brt = -1;
    }
}

static void supply_off(void) {
    if (device_is_ready(ext_power) && ext_power_get(ext_power) > 0) {
        ext_power_disable(ext_power);
    }
}

static void enforce(struct k_work *work) {
    bool on = false;
    if (zmk_rgb_underglow_get_state(&on) != 0) {
        return;
    }

    if (zmk_usb_is_powered()) {
        restore_brt();
        if (forced_off) {
            forced_off = false;
            if (restore_on && !on) {
                zmk_rgb_underglow_on();
                on = true;
            }
            restore_on = false;
        }
        if (!on) {
            supply_off();
        }
        return;
    }

    uint8_t soc = zmk_battery_state_of_charge();
    if (!allow || soc < OFF_BELOW) {
        if (on) {
            restore_on = true;
            forced_off = true;
            zmk_rgb_underglow_off(); /* also turns the supply off */
        } else {
            supply_off();
        }
        return;
    }

    if (forced_off) {
        forced_off = false;
        if (restore_on && !on) {
            zmk_rgb_underglow_on();
            on = true;
        }
        restore_on = false;
    }
    if (!on) {
        supply_off();
        return;
    }

    int cap = soc < DIM_BELOW ? BRT_CAP / 2 : BRT_CAP;
    int b = saved_brt >= 0 ? saved_brt : zmk_rgb_underglow_calc_brt(0).b;
    if (b > cap) {
        if (saved_brt < 0) {
            saved_brt = b;
        }
        set_brt(cap);
    } else {
        restore_brt();
    }
}

static int battery_lighting_listener(const zmk_event_t *eh) {
    schedule(100);
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(keygen_battery_lighting, battery_lighting_listener);
ZMK_SUBSCRIPTION(keygen_battery_lighting, zmk_usb_conn_state_changed);
ZMK_SUBSCRIPTION(keygen_battery_lighting, zmk_battery_state_changed);
ZMK_SUBSCRIPTION(keygen_battery_lighting, zmk_activity_state_changed);

static int settings_set(const char *name, size_t len, settings_read_cb read_cb, void *cb_arg) {
    if (settings_name_steq(name, "allow", NULL) && len == sizeof(allow)) {
        int rc = read_cb(cb_arg, &allow, sizeof(allow));
        schedule(100);
        return MIN(rc, 0);
    }
    return -ENOENT;
}

SETTINGS_STATIC_HANDLER_DEFINE(keygen_battery_lighting, "kg/batlight", NULL, settings_set, NULL, NULL);

static void set_allow(bool value) {
    allow = value;
    settings_save_one("kg/batlight/allow", &allow, sizeof(allow));
    schedule(0);
}

static int battery_lighting_init(void) {
    /* after settings have loaded and the lighting has restored its state */
    schedule(2000);
    return 0;
}

SYS_INIT(battery_lighting_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);

/* &kg_bl: the central decides the new value, so both halves end up with the same one */
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

static int kg_bl_convert(struct zmk_behavior_binding *binding, struct zmk_behavior_binding_event event) {
    binding->param1 = !allow;
    return 0;
}

static int kg_bl_pressed(struct zmk_behavior_binding *binding, struct zmk_behavior_binding_event event) {
    set_allow(binding->param1 != 0);
    LOG_INF("lighting on battery %s", allow ? "allowed" : "off");
    return ZMK_BEHAVIOR_OPAQUE;
}

static int kg_bl_released(struct zmk_behavior_binding *binding, struct zmk_behavior_binding_event event) {
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api kg_bl_api = {
    .binding_convert_central_state_dependent_params = kg_bl_convert,
    .binding_pressed = kg_bl_pressed,
    .binding_released = kg_bl_released,
    .locality = BEHAVIOR_LOCALITY_GLOBAL,
};

BEHAVIOR_DT_INST_DEFINE(0, NULL, NULL, NULL, NULL, POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,
                        &kg_bl_api);

#endif
