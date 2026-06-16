# Home Assistant Automation Examples ⚙️

Automation examples use the Stage 5 `ha_tv_pip.show_camera` service and Stage 6 `ha_tv_pip.show_snapshot` service.

Current Stage 5 service shape:

```yaml
alias: Show front door on TV
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_bell_visitor
    to: "on"
action:
  - service: ha_tv_pip.show_camera
    data:
      receiver_device_id: living_room_tv
      camera_entity: camera.front_door
      duration_seconds: 30
      enter_pip: true
      snapshot_fallback: true
      snapshot_camera_entity: camera.front_door_sub
```

Replace `receiver_device_id` and `camera_entity` with values from your Home Assistant instance. `snapshot_camera_entity` is optional and defaults to the main camera entity. For cameras with multiple stream profiles, use a TV-compatible H.264 or lower-resolution stream where possible; high-resolution main streams can exceed what Android TV devices can decode directly.

Snapshot alert example:

```yaml
alias: Show front door snapshot on TV
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_motion
    to: "on"
action:
  - service: ha_tv_pip.show_snapshot
    data:
      receiver_device_id: living_room_tv
      camera_entity: camera.front_door
      duration_seconds: 10
      enter_pip: true
```
