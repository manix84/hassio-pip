package com.hatvpip.receiver

import org.json.JSONArray
import org.json.JSONObject

object ReceiverCapabilities {
    private val streamTypes = listOf(
        StreamType.Hls.wireName,
        StreamType.Mjpeg.wireName,
        StreamType.Snapshot.wireName,
        StreamType.Notification.wireName
    )
    private val positions = listOf(
        NotificationPosition.TopRight.wireName,
        NotificationPosition.TopLeft.wireName,
        NotificationPosition.BottomRight.wireName,
        NotificationPosition.BottomLeft.wireName
    )

    fun toJson(): JSONObject =
        JSONObject()
            .put("capabilitiesVersion", 1)
            .put("streamTypes", JSONArray(streamTypes))
            .put("positions", JSONArray(positions))
            .put("previewImage", true)
            .put("playableFallback", true)
            .put("nativePictureInPicture", true)
            .put("overlayFallback", true)
            .put("styledNotifications", true)
            .put("mediaWithNotificationText", true)
            .put("launcherManagement", true)
            .put("localPairing", true)
            .put("remoteReceiverSettings", true)
}
