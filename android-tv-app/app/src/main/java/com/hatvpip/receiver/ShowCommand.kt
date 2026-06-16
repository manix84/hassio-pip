package com.hatvpip.receiver

import org.json.JSONException
import org.json.JSONObject

enum class StreamType(val wireName: String) {
    Hls("hls"),
    Snapshot("snapshot")
}

data class ShowCommand(
    val title: String,
    val url: String,
    val streamType: StreamType,
    val durationSeconds: Int?,
    val enterPip: Boolean
) {
    companion object {
        fun testVideo(): ShowCommand =
            ShowCommand(
                title = "Test Video",
                url = PlayerActivity.TEST_STREAM_URL,
                streamType = StreamType.Hls,
                durationSeconds = null,
                enterPip = false
            )

        fun fromJson(body: String): Result<ShowCommand> =
            runCatching {
                val json = JSONObject(body)
                val url = json.optString("url").trim()
                require(url.isNotEmpty()) { "`url` is required" }
                require(url.startsWith("http://") || url.startsWith("https://")) {
                    "`url` must be an HTTP or HTTPS URL"
                }

                val streamType = when (val value = json.optString("streamType", "hls")) {
                    StreamType.Hls.wireName -> StreamType.Hls
                    StreamType.Snapshot.wireName -> StreamType.Snapshot
                    else -> error("Unsupported `streamType`: $value")
                }

                val durationSeconds = if (json.has("durationSeconds") && !json.isNull("durationSeconds")) {
                    json.getInt("durationSeconds").also {
                        require(it > 0) { "`durationSeconds` must be greater than 0" }
                    }
                } else {
                    null
                }

                ShowCommand(
                    title = json.optString("title", "HA TV PiP").ifBlank { "HA TV PiP" },
                    url = url,
                    streamType = streamType,
                    durationSeconds = durationSeconds,
                    enterPip = json.optBoolean("enterPip", true)
                )
            }.recoverCatching { error ->
                if (error is JSONException) {
                    throw IllegalArgumentException("Request body must be valid JSON", error)
                }
                throw error
            }
    }
}
