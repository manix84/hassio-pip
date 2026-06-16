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
              "previewUrl": "https://example.com/front-door.jpg",
              "durationSeconds": 30,
              "enterPip": true
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals("Front Door", command.title)
        assertEquals("https://example.com/front-door.m3u8", command.url)
        assertEquals("https://example.com/front-door.jpg", command.previewUrl)
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
    fun parsesNotificationShowRequestWithoutUrl() {
        val command = ShowCommand.fromJson(
            """
            {
              "title": "Enhanced notifications",
              "message": "Notifications can show text on the TV",
              "streamType": "notification",
              "position": "bottom_right",
              "titleColor": "#50BFF2",
              "titleSize": 26,
              "messageColor": "#fbf5f5",
              "messageSize": 18,
              "backgroundColor": "#0f0e0e",
              "durationSeconds": 15,
              "enterPip": true
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals(StreamType.Notification, command.streamType)
        assertEquals("", command.url)
        assertEquals("Enhanced notifications", command.title)
        assertEquals("Notifications can show text on the TV", command.message)
        assertEquals(NotificationPosition.BottomRight, command.style.position)
        assertEquals("#50BFF2", command.style.titleColor)
        assertEquals(26, command.style.titleSize)
        assertEquals("#fbf5f5", command.style.messageColor)
        assertEquals(18, command.style.messageSize)
        assertEquals("#0f0e0e", command.style.backgroundColor)
    }

    @Test
    fun parsesCameraShowRequestWithNotificationStyle() {
        val command = ShowCommand.fromJson(
            """
            {
              "title": "Front Door",
              "message": "Someone is at the door",
              "url": "https://example.com/front-door.m3u8",
              "streamType": "hls",
              "position": "bottom_left",
              "titleColor": "#50BFF2",
              "messageColor": "#fbf5f5",
              "backgroundColor": "#0f0e0e"
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals(StreamType.Hls, command.streamType)
        assertEquals("Someone is at the door", command.message)
        assertEquals(NotificationPosition.BottomLeft, command.style.position)
        assertEquals("#50BFF2", command.style.titleColor)
        assertEquals("#fbf5f5", command.style.messageColor)
        assertEquals("#0f0e0e", command.style.backgroundColor)
    }

    @Test
    fun rejectsInvalidPreviewUrl() {
        val result = ShowCommand.fromJson(
            """{"url":"https://example.com/video.m3u8","previewUrl":"file:///tmp/image.jpg"}"""
        )

        assertTrue(result.isFailure)
        assertEquals(
            "`previewUrl` must be an HTTP or HTTPS URL",
            result.exceptionOrNull()?.message
        )
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
