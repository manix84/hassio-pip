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
              "fallbackUrl": "https://example.com/api/camera_proxy_stream/camera.front_door",
              "fallbackStreamType": "mjpeg",
              "durationSeconds": 30,
              "enterPip": true
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals("Front Door", command.title)
        assertEquals("https://example.com/front-door.m3u8", command.url)
        assertEquals("https://example.com/front-door.jpg", command.previewUrl)
        assertEquals(
            "https://example.com/api/camera_proxy_stream/camera.front_door",
            command.fallbackUrl
        )
        assertEquals(StreamType.Mjpeg, command.fallbackStreamType)
        assertEquals(StreamType.Hls, command.streamType)
        assertEquals(30, command.durationSeconds)
        assertTrue(command.enterPip)
        assertEquals(false, command.showNotification)
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
    fun parsesMjpegShowRequest() {
        val command = ShowCommand.fromJson(
            """
            {
              "title": "Front Door",
              "url": "https://example.com/api/camera_proxy_stream/camera.front_door",
              "streamType": "mjpeg",
              "previewUrl": "https://example.com/api/camera_proxy/camera.front_door",
              "durationSeconds": 30,
              "enterPip": true
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals(StreamType.Mjpeg, command.streamType)
        assertEquals(
            "https://example.com/api/camera_proxy_stream/camera.front_door",
            command.url
        )
        assertEquals(
            "https://example.com/api/camera_proxy/camera.front_door",
            command.previewUrl
        )
        assertEquals(30, command.durationSeconds)
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
              "backgroundColor": "#B30F0E0E",
              "width": 512,
              "height": 240,
              "durationSeconds": 15,
              "enterPip": true
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals(StreamType.Notification, command.streamType)
        assertEquals("", command.url)
        assertEquals("Enhanced notifications", command.title)
        assertTrue(command.showNotification)
        assertEquals("Notifications can show text on the TV", command.message)
        assertEquals(NotificationPosition.BottomRight, command.style.position)
        assertEquals("#50BFF2", command.style.titleColor)
        assertEquals(26, command.style.titleSize)
        assertEquals("#fbf5f5", command.style.messageColor)
        assertEquals(18, command.style.messageSize)
        assertEquals("#B30F0E0E", command.style.backgroundColor)
        assertEquals(512, command.style.width)
        assertEquals(240, command.style.height)
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
              "backgroundColor": "#B30F0E0E",
              "textOverlay": true,
              "width": 720,
              "height": 360
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals(StreamType.Hls, command.streamType)
        assertTrue(command.showNotification)
        assertEquals("Someone is at the door", command.message)
        assertEquals(NotificationPosition.BottomLeft, command.style.position)
        assertEquals("#50BFF2", command.style.titleColor)
        assertEquals("#fbf5f5", command.style.messageColor)
        assertEquals("#B30F0E0E", command.style.backgroundColor)
        assertEquals(true, command.style.textOverlay)
        assertEquals(720, command.style.width)
        assertEquals(360, command.style.height)
    }

    @Test
    fun parsesCameraShowRequestWithTitleOnlyNotification() {
        val command = ShowCommand.fromJson(
            """
            {
              "title": "Front Door",
              "showNotification": true,
              "url": "https://example.com/front-door.m3u8",
              "streamType": "hls",
              "position": "top_right",
              "backgroundColor": "#B30F0E0E"
            }
            """.trimIndent()
        ).getOrThrow()

        assertEquals(StreamType.Hls, command.streamType)
        assertEquals("Front Door", command.title)
        assertTrue(command.showNotification)
        assertEquals(null, command.message)
        assertEquals(NotificationPosition.TopRight, command.style.position)
        assertEquals("#B30F0E0E", command.style.backgroundColor)
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
    fun rejectsInvalidFallbackUrl() {
        val result = ShowCommand.fromJson(
            """{"url":"https://example.com/video.m3u8","fallbackUrl":"file:///tmp/video.mjpeg"}"""
        )

        assertTrue(result.isFailure)
        assertEquals(
            "`fallbackUrl` must be an HTTP or HTTPS URL",
            result.exceptionOrNull()?.message
        )
    }

    @Test
    fun rejectsInvalidFallbackStreamType() {
        val result = ShowCommand.fromJson(
            """
            {
              "url": "https://example.com/video.m3u8",
              "fallbackUrl": "https://example.com/video.mjpeg",
              "fallbackStreamType": "webrtc"
            }
            """.trimIndent()
        )

        assertTrue(result.isFailure)
        assertEquals(
            "Unsupported `fallbackStreamType`: webrtc",
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
