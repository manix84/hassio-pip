package com.hatvpip.receiver

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ShowCommandTest {
    @Test
    fun parsesValidShowRequest() {
        val command = ShowCommand.fromJson(
            """
            {
              "title": "Front Door",
              "url": "https://example.com/front-door.m3u8",
              "streamType": "hls",
              "durationSeconds": 30,
              "enterPip": true
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals("Front Door", command.title)
        assertEquals("https://example.com/front-door.m3u8", command.url)
        assertEquals(StreamType.Hls, command.streamType)
        assertEquals(30, command.durationSeconds)
        assertTrue(command.enterPip)
    }

    @Test
    fun rejectsMissingUrl() {
        val result = ShowCommand.fromJson("""{"streamType":"hls"}""")

        assertTrue(result.isFailure)
        assertEquals("`url` is required", result.exceptionOrNull()?.message)
    }

    @Test
    fun parsesSnapshotShowRequest() {
        val command = ShowCommand.fromJson(
            """
            {
              "title": "Front Door",
              "url": "https://example.com/front-door.jpg",
              "streamType": "snapshot",
              "durationSeconds": 10,
              "enterPip": true
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals(StreamType.Snapshot, command.streamType)
        assertEquals("https://example.com/front-door.jpg", command.url)
        assertEquals(10, command.durationSeconds)
    }

    @Test
    fun rejectsUnsupportedStreamType() {
        val result = ShowCommand.fromJson(
            """{"url":"https://example.com/video.mp4","streamType":"mp4"}"""
        )

        assertTrue(result.isFailure)
        assertEquals("Unsupported `streamType`: mp4", result.exceptionOrNull()?.message)
    }
}
