# Home Assistant Automation Examples ⚙️

Automation examples use the Stage 7 `ha_tv_pip.show_camera` stream type options, the Stage 6 `ha_tv_pip.show_snapshot` service, and the Stage 11 `ha_tv_pip.show_notification` service.

Replace `receiver_device_id`, `camera_entity`, and trigger entity ids with values from your Home Assistant instance. Use a compatible H.264/HLS camera stream where possible; lower-resolution secondary streams are often more reliable on Android TV devices than high-resolution main streams.

## Camera Popup With Snapshot Preview And Footer 📹

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
      title: Front door
      message: Someone is at the door
      position: top_right
      background_color: "#B30F0E0E"
      width: 720
      height: 405
```

`stream_type` defaults to `auto`; use `hls` to force video or `snapshot` to force a still image through the camera service. `snapshot_camera_entity` is optional and defaults to the main camera entity. Optional notification fields such as `title`, `message`, `position`, colors, `width`, and `height` add text below the video or snapshot inside the same rounded glass popup and can resize the receiver overlay.

## Snapshot Popup With Footer 🖼️

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
      title: Front door
      message: Motion detected
      position: top_right
      background_color: "#B30F0E0E"
```

Snapshot mode is useful when you want a fast alert and do not need live playback.

## Text-Only Notification 🔔

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
      background_color: "#B30F0E0E"
      width: 512
      height: 240
```

## Resize-Only Camera Popup 📐

Use width and height without `title` or `message` when you want to resize the media popup without showing a footer.

```yaml
alias: Show compact driveway camera on TV
trigger:
  - platform: state
    entity_id: binary_sensor.driveway_motion
    to: "on"
action:
  - service: ha_tv_pip.show_camera
    data:
      receiver_device_id: living_room_tv
      camera_entity: camera.driveway
      duration_seconds: 20
      enter_pip: true
      stream_type: auto
      snapshot_fallback: true
      width: 480
      height: 270
```
