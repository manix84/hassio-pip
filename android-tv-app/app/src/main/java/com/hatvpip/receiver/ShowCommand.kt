package com.hatvpip.receiver

import org.json.JSONException
import org.json.JSONObject

enum class StreamType(val wireName: String) {
    Hls("hls"),
    Snapshot("snapshot"),
    Notification("notification")
}

data class ShowCommand(
    val title: String,
    val url: String,
    val streamType: StreamType,
    val durationSeconds: Int?,
    val enterPip: Boolean,
    val previewUrl: String?,
    val message: String?,
    val style: NotificationStyle
) {
    companion object {
        fun testVideo(title: String = "Test Video"): ShowCommand =
            ShowCommand(
                title = title,
                url = PlayerActivity.TEST_STREAM_URL,
                streamType = StreamType.Hls,
                durationSeconds = null,
                enterPip = false,
                previewUrl = null,
                message = null,
                style = NotificationStyle()
            )

        fun fromJson(body: String): Result<ShowCommand> =
            runCatching {
                val json = JSONObject(body)
                val streamType = when (val value = json.optString("streamType", "hls")) {
                    StreamType.Hls.wireName -> StreamType.Hls
                    StreamType.Snapshot.wireName -> StreamType.Snapshot
                    StreamType.Notification.wireName -> StreamType.Notification
                    else -> error("Unsupported `streamType`: $value")
                }
                val url = json.optString("url").trim()
                if (streamType == StreamType.Notification) {
                    require(url.isEmpty() || url.startsWith("http://") || url.startsWith("https://")) {
                        "`url` must be an HTTP or HTTPS URL"
                    }
                } else {
                    require(url.isNotEmpty()) { "`url` is required" }
                    require(url.startsWith("http://") || url.startsWith("https://")) {
                        "`url` must be an HTTP or HTTPS URL"
                    }
                }

                val durationSeconds = if (json.has("durationSeconds") && !json.isNull("durationSeconds")) {
                    json.getInt("durationSeconds").also {
                        require(it > 0) { "`durationSeconds` must be greater than 0" }
                    }
                } else {
                    null
                }
                val previewUrl = json.optString("previewUrl").trim().ifBlank { null }
                if (previewUrl != null) {
                    require(previewUrl.startsWith("http://") || previewUrl.startsWith("https://")) {
                        "`previewUrl` must be an HTTP or HTTPS URL"
                    }
                }

                ShowCommand(
                    title = json.optString("title", "HA TV PiP").ifBlank { "HA TV PiP" },
                    url = url,
                    streamType = streamType,
                    durationSeconds = durationSeconds,
                    enterPip = json.optBoolean("enterPip", true),
                    previewUrl = previewUrl,
                    message = json.optString("message").trim().ifBlank { null },
                    style = NotificationStyle.fromJson(json)
                )
            }.recoverCatching { error ->
                if (error is JSONException) {
                    throw IllegalArgumentException("Request body must be valid JSON", error)
                }
                throw error
            }
    }
}

enum class NotificationPosition(val wireName: String, val fallbackIndex: Int) {
    TopRight("top_right", 0),
    TopLeft("top_left", 1),
    BottomRight("bottom_right", 2),
    BottomLeft("bottom_left", 3);

    companion object {
        fun fromWire(value: String): NotificationPosition =
            entries.firstOrNull { it.wireName == value }
                ?: value.toIntOrNull()?.let { index ->
                    entries.firstOrNull { it.fallbackIndex == index }
                }
                ?: TopRight
    }
}

data class NotificationStyle(
    val position: NotificationPosition = NotificationPosition.TopRight,
    val titleColor: String = "#50BFF2",
    val titleSize: Int = 24,
    val messageColor: String = "#fbf5f5",
    val messageSize: Int = 18,
    val backgroundColor: String = "#0f0e0e",
    val width: Int? = null,
    val height: Int? = null
) {
    companion object {
        fun fromJson(json: JSONObject): NotificationStyle =
            NotificationStyle(
                position = NotificationPosition.fromWire(json.optString("position", "top_right")),
                titleColor = json.optString("titleColor", "#50BFF2"),
                titleSize = json.optInt("titleSize", 24).coerceIn(10, 48),
                messageColor = json.optString("messageColor", "#fbf5f5"),
                messageSize = json.optInt("messageSize", 18).coerceIn(10, 40),
                backgroundColor = json.optString("backgroundColor", "#0f0e0e"),
                width = json.optionalDimension("width", 240, 1600),
                height = json.optionalDimension("height", 120, 900)
            )
    }
}

private fun JSONObject.optionalDimension(name: String, minimum: Int, maximum: Int): Int? =
    if (has(name) && !isNull(name)) {
        getInt(name).coerceIn(minimum, maximum)
    } else {
        null
    }
