package com.hatvpip.receiver

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ReceiverCapabilitiesTest {
    @Test
    fun capabilitiesDescribeSupportedReceiverProtocolFeatures() {
        val capabilities = ReceiverCapabilities.toJson()
        val streamTypes = capabilities.getJSONArray("streamTypes").toString()
        val positions = capabilities.getJSONArray("positions").toString()

        assertEquals(1, capabilities.getInt("capabilitiesVersion"))
        assertTrue(streamTypes.contains("hls"))
        assertTrue(streamTypes.contains("mjpeg"))
        assertTrue(streamTypes.contains("snapshot"))
        assertTrue(streamTypes.contains("notification"))
        assertTrue(positions.contains("top_right"))
        assertTrue(positions.contains("bottom_left"))
        assertTrue(capabilities.getBoolean("previewImage"))
        assertTrue(capabilities.getBoolean("playableFallback"))
        assertTrue(capabilities.getBoolean("overlayFallback"))
        assertTrue(capabilities.getBoolean("styledNotifications"))
        assertTrue(capabilities.getBoolean("mediaWithNotificationText"))
        assertTrue(capabilities.getBoolean("launcherManagement"))
        assertTrue(capabilities.getBoolean("localPairing"))
        assertTrue(capabilities.getBoolean("remoteReceiverSettings"))
    }
}
