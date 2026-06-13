package com.hatvpip.receiver

enum class PlaybackStatus(val label: String) {
    Idle("Idle"),
    Buffering("Buffering"),
    Ready("Ready"),
    Ended("Ended"),
    Error("Error")
}

data class PlayerPlaybackState(
    val status: PlaybackStatus = PlaybackStatus.Idle,
    val isPlaying: Boolean = false,
    val errorMessage: String? = null
) {
    val displayText: String
        get() = buildString {
            append(status.label)
            append(if (isPlaying) " - playing" else " - paused")
            if (errorMessage != null) {
                append(" - ")
                append(errorMessage)
            }
        }
}
