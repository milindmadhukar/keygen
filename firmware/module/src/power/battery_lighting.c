/*
 * Keygen: when the per-key lighting is on, and how bright.
 *
 * This module alone turns the lighting on and off (ZMK's own USB and idle auto-off are disabled),
 * so the decisions can't fight. It keeps what the user asked for, the lighting on or off and its
 * brightness, in its own settings, and applies:
 *   - idle or asleep: off;
 *   - on USB: as the user set it;
 *   - on battery: off unless allowed (&kg_bl, saved); when allowed, the brightness is capped at
 *     KEYGEN_BATTERY_LIGHTING_BRT, halved below DIM_BELOW % charge and off below OFF_BELOW %, each
 *     with 5 % of hysteresis, so the cell's sag under load can't make the lighting flap.
 * Whenever the lighting is off, so is the LED supply (the 5 V boost, ZMK's ext-power on P0.08):
 * dark SK6812s still draw about 1 mA each.
 *
 * A change the module didn't make (an &rgb_ug key, or the central's command on the peripheral) is
 * taken as the user's wish. Every relevant event schedules one re-check of the whole policy.
 */

#define DT_DRV_COMPAT keygen_behavior_battery_lighting

#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/settings/settings.h>
#include <zephyr/logging/log.h>

#include <drivers/behavior.h>
#include <drivers/ext_power.h>

#include <zmk/activity.h>
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
#define HYSTERESIS 5

static const struct device *const ext_power = DEVICE_DT_GET(DT_INST(0, zmk_ext_power_generic));

/* what the user asked for; saved */
static struct {
    bool allow;   /* lighting may run on battery */
    bool want_on; /* the lighting is switched on */
    int8_t brt;   /* brightness, 0-100 of ZMK's scale; -1 until first seen */
} user = {.allow = false, .want_on = false, .brt = -1};

static bool loaded;       /* settings read (or none stored) */
static bool have_soc;     /* a battery reading has arrived */
static bool low, dim;     /* latched charge thresholds, on battery */
static int applied_on = -1, applied_brt = -1; /* what this module last set */

static void enforce(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(enforce_work, enforce);
static void save(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(save_work, save);

static void schedule(int ms) { k_work_reschedule(&enforce_work, K_MSEC(ms)); }

static void save(struct k_work *work) { settings_save_one("kg/batlight/user", &user, sizeof(user)); }

static void changed(void) { k_work_reschedule(&save_work, K_SECONDS(10)); }

static void supply_off(void) {
    if (device_is_ready(ext_power) && ext_power_get(ext_power) > 0) {
        ext_power_disable(ext_power);
    }
}

static void enforce(struct k_work *work) {
    bool on = false;
    /* before the saved wishes are read, ZMK's own restored state isn't the user's */
    if ((!loaded && k_uptime_get() < 5000) || zmk_rgb_underglow_get_state(&on) != 0) {
        return;
    }
    int brt = zmk_rgb_underglow_calc_brt(0).b;

    /* anything the module didn't do was the user (or the central, on the right half) */
    if (applied_on >= 0 && on != (bool)applied_on && on != user.want_on) {
        user.want_on = on;
        changed();
    }
    if (user.brt < 0 || (applied_brt >= 0 && brt != applied_brt && brt != user.brt)) {
        user.brt = brt;
        changed();
    }

    bool usb = zmk_usb_is_powered();
    bool active = zmk_activity_get_state() == ZMK_ACTIVITY_ACTIVE;
    int target = user.brt;
    bool powered = usb;
    if (!usb) {
        if (!have_soc && user.allow) {
            return; /* wait for the first battery reading before deciding */
        }
        uint8_t soc = zmk_battery_state_of_charge();
        if (soc < OFF_BELOW) low = true;
        else if (soc >= OFF_BELOW + HYSTERESIS) low = false;
        if (soc < DIM_BELOW) dim = true;
        else if (soc >= DIM_BELOW + HYSTERESIS) dim = false;
        powered = user.allow && !low;
        int cap = dim ? BRT_CAP / 2 : BRT_CAP;
        if (target > cap) target = cap;
    } else {
        low = dim = false;
    }

    bool should_on = user.want_on && active && powered;
    if (should_on && brt != target) {
        struct zmk_led_hsb c = zmk_rgb_underglow_calc_brt(0);
        c.b = target;
        zmk_rgb_underglow_set_hsb(c);
        brt = target;
    }
    if (should_on && !on) {
        zmk_rgb_underglow_on();
    } else if (!should_on && on) {
        zmk_rgb_underglow_off(); /* also turns the supply off */
    }
    if (!should_on) {
        supply_off();
    }
    applied_on = should_on;
    applied_brt = brt;
}

static int battery_lighting_listener(const zmk_event_t *eh) {
    if (as_zmk_battery_state_changed(eh)) {
        have_soc = true;
    }
    schedule(100);
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(keygen_battery_lighting, battery_lighting_listener);
ZMK_SUBSCRIPTION(keygen_battery_lighting, zmk_usb_conn_state_changed);
ZMK_SUBSCRIPTION(keygen_battery_lighting, zmk_battery_state_changed);
ZMK_SUBSCRIPTION(keygen_battery_lighting, zmk_activity_state_changed);

static int bl_settings_set(const char *name, size_t len, settings_read_cb read_cb, void *cb_arg) {
    if (settings_name_steq(name, "user", NULL) && len == sizeof(user)) {
        int rc = read_cb(cb_arg, &user, sizeof(user));
        return MIN(rc, 0);
    }
    return -ENOENT;
}

static int bl_settings_commit(void) {
    loaded = true;
    schedule(500);
    return 0;
}

SETTINGS_STATIC_HANDLER_DEFINE(keygen_battery_lighting, "kg/batlight", NULL, bl_settings_set,
                               bl_settings_commit, NULL);

static int battery_lighting_init(void) {
    /* a fallback in case no settings commit arrives */
    k_work_reschedule(&enforce_work, K_SECONDS(6));
    return 0;
}

SYS_INIT(battery_lighting_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);

/* &kg_bl: the central decides the new value, so both halves end up with the same one */
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

static int kg_bl_convert(struct zmk_behavior_binding *binding, struct zmk_behavior_binding_event event) {
    binding->param1 = !user.allow;
    return 0;
}

static int kg_bl_pressed(struct zmk_behavior_binding *binding, struct zmk_behavior_binding_event event) {
    user.allow = binding->param1 != 0;
    changed();
    schedule(0);
    LOG_INF("lighting on battery %s", user.allow ? "allowed" : "off");
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
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .get_parameter_metadata = zmk_behavior_get_empty_param_metadata,
#endif
};

BEHAVIOR_DT_INST_DEFINE(0, NULL, NULL, NULL, NULL, POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,
                        &kg_bl_api);

#endif
