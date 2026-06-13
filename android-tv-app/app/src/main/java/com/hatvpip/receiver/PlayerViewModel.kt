package com.hatvpip.receiver

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel

class PlayerViewModel : ViewModel() {
    var playbackState by mutableStateOf(PlayerPlaybackState())
        private set

    var isInPip by mutableStateOf(false)
        private set

    fun setPlaybackStatus(status: PlaybackStatus, isPlaying: Boolean) {
        playbackState = playbackState.copy(
            status = status,
            isPlaying = isPlaying,
            errorMessage = null
        )
    }

    fun setIsPlaying(isPlaying: Boolean) {
        playbackState = playbackState.copy(isPlaying = isPlaying)
    }

    fun setPlaybackError(errorCodeName: String) {
        playbackState = playbackState.copy(
            status = PlaybackStatus.Error,
            isPlaying = false,
            errorMessage = errorCodeName
        )
    }

    fun setPictureInPicture(active: Boolean) {
        isInPip = active
    }
}
