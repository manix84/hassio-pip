package com.hatvpip.receiver

import org.junit.Assert.assertEquals
import org.junit.Test

class PlayerPlaybackStateTest {
    @Test
    fun displayTextShowsPausedStatusByDefault() {
        val state = PlayerPlaybackState()

        assertEquals("Idle - paused", state.displayText)
    }

    @Test
    fun displayTextShowsPlayingStatus() {
        val state = PlayerPlaybackState(
            status = PlaybackStatus.Ready,
            isPlaying = true
        )

        assertEquals("Ready - playing", state.displayText)
    }

    @Test
    fun displayTextIncludesErrors() {
        val state = PlayerPlaybackState(
            status = PlaybackStatus.Error,
            errorMessage = "SOURCE_ERROR"
        )

        assertEquals("Error - paused - SOURCE_ERROR", state.displayText)
    }
}
