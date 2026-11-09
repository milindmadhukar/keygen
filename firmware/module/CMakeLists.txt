# Keygen's ZMK module. The OLED screens in src/ui are not built into the firmware yet.
target_sources_ifdef(CONFIG_KEYGEN_BATTERY_LIGHTING app PRIVATE src/power/battery_lighting.c)
