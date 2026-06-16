# Home Assistant Automation Examples ⚙️

Automation examples use the Stage 7 `ha_tv_pip.show_camera` stream type options, the Stage 6 `ha_tv_pip.show_snapshot` service, and the Stage 11 `ha_tv_pip.show_notification` service.

Current Stage 7 service shape:

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
      stream_type: auto
      snapshot_fallback: true
      snapshot_camera_entity: camera.front_door_sub
      message: Someone is at the door
      position: top_right
      width: 720
      height: 405
```

Replace `receiver_device_id` and `camera_entity` with values from your Home Assistant instance. `stream_type` defaults to `auto`; use `hls` to force video or `snapshot` to force a still image through the camera service. `snapshot_camera_entity` is optional and defaults to the main camera entity. Optional notification fields such as `message`, `position`, colors, `width`, and `height` add a rounded text card over the video or snapshot popup and can resize the receiver overlay. For cameras with multiple stream profiles, use a TV-compatible H.264 or lower-resolution stream where possible; high-resolution main streams can exceed what Android TV devices can decode directly.

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

Styled notification example:

```yaml
alias: Show doorbell notification on TV
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_bell_visitor
    to: "on"
action:
  - service: ha_tv_pip.show_notification
    data:
      receiver_device_id: living_room_tv
      title: Front door
      message: Someone is at the door
      duration_seconds: 15
      position: top_right
      title_color: "#50BFF2"
      title_size: 24
      message_color: "#fbf5f5"
      message_size: 18
      background_color: "#0f0e0e"
      width: 512
      height: 240
```
