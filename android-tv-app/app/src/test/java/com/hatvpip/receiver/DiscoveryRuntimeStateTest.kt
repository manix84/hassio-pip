package com.hatvpip.receiver

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class DiscoveryRuntimeStateTest {
    @Test
    fun markRegisteredStoresAdvertisementState() {
        val descriptor = DiscoveryServiceDescriptor.create(
            deviceId = "device-123",
            deviceName = "Nursery TV",
            appVersion = "0.6.0",
            port = 8765
        )

        DiscoveryRuntimeState.markRegistering(descriptor)
        DiscoveryRuntimeState.markRegistered(serviceName = "HA TV PiP - Nursery TV", port = 8765)

        val snapshot = DiscoveryRuntimeState.snapshot()
        assertTrue(snapshot.running)
        assertEquals("HA TV PiP - Nursery TV", snapshot.serviceName)
        assertEquals("_ha-tv-pip._tcp.", snapshot.serviceType)
        assertEquals(8765, snapshot.port)
        assertNull(snapshot.errorMessage)
    }

    @Test
    fun markFailedStoresErrorAndClearsRunningState() {
        DiscoveryRuntimeState.markFailed(
            serviceName = "HA TV PiP - Nursery TV",
            port = 8765,
            errorMessage = "NSD registration failed with code 3"
        )

        val snapshot = DiscoveryRuntimeState.snapshot()
        assertFalse(snapshot.running)
        assertEquals("HA TV PiP - Nursery TV", snapshot.serviceName)
        assertEquals("NSD registration failed with code 3", snapshot.errorMessage)
    }
}
