package com.hatvpip.receiver

import java.util.concurrent.atomic.AtomicReference

enum class ReceiverPlaybackMode(val wireName: String) {
    Idle("idle"),
    FullScreen("full_screen"),
    NativePictureInPicture("native_pip"),
    Overlay("overlay")
}

data class ReceiverPlaybackSnapshot(
    val status: PlaybackStatus = PlaybackStatus.Idle,
    val isPlaying: Boolean = false,
    val mode: ReceiverPlaybackMode = ReceiverPlaybackMode.Idle,
    val title: String? = null,
    val url: String? = null,
    val previewUrl: String? = null,
    val streamType: String? = null,
    val errorMessage: String? = null,
    val updatedAtMillis: Long = System.currentTimeMillis()
) {
    val wirePlaybackState: String
        get() = when {
            status == PlaybackStatus.Error -> "error"
            isPlaying -> "playing"
            status == PlaybackStatus.Buffering -> "buffering"
            else -> "idle"
        }
}

object ReceiverRuntimeState {
    private val currentPlayback = AtomicReference(ReceiverPlaybackSnapshot())

    fun snapshot(): ReceiverPlaybackSnapshot = currentPlayback.get()

    fun update(snapshot: ReceiverPlaybackSnapshot) {
        currentPlayback.set(snapshot)
    }

    fun markIdle() {
        currentPlayback.set(ReceiverPlaybackSnapshot())
    }
}
