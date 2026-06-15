package com.hatvpip.receiver

import org.junit.Assert.assertEquals
import org.junit.Test

class DiscoveryServiceDescriptorTest {
    @Test
    fun createBuildsMdnsDescriptorForReceiver() {
        val descriptor = DiscoveryServiceDescriptor.create(
            deviceId = "device-123",
            deviceName = "Nursery TV",
            appVersion = "0.6.0",
            port = 8765
        )

        assertEquals("HA TV PiP - Nursery TV", descriptor.serviceName)
        assertEquals("_ha-tv-pip._tcp.", descriptor.serviceType)
        assertEquals(8765, descriptor.port)
        assertEquals("device-123", descriptor.attributes["id"])
        assertEquals("Nursery TV", descriptor.attributes["name"])
        assertEquals("0.6.0", descriptor.attributes["version"])
        assertEquals("disabled", descriptor.attributes["pairing"])
        assertEquals("1", descriptor.attributes["api"])
    }

    @Test
    fun createFallsBackWhenDeviceNameIsBlank() {
        val descriptor = DiscoveryServiceDescriptor.create(
            deviceId = "device-123",
            deviceName = " ",
            appVersion = "0.6.0",
            port = 8765
        )

        assertEquals("HA TV PiP Receiver", descriptor.serviceName)
        assertEquals(" ", descriptor.attributes["name"])
    }
}
