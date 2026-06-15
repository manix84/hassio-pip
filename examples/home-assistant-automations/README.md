# Home Assistant Automation Examples ⚙️

Automation examples use the Stage 5 `ha_tv_pip.show_camera` service.

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
```

Replace `receiver_device_id` and `camera_entity` with values from your Home Assistant instance. For Reolink cameras, a substream is often more Android TV-compatible than the main stream.
