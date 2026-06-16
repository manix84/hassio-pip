package com.hatvpip.receiver

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class RemoteConnectionRuntimeStateTest {
    @Test
    fun `remote runtime state tracks connection lifecycle`() {
        RemoteConnectionRuntimeState.markDisabled()
        assertEquals(RemoteConnectionStatus.Disabled, RemoteConnectionRuntimeState.snapshot().status)

        RemoteConnectionRuntimeState.markConnecting("https://home.example.test")
        assertEquals(RemoteConnectionStatus.Connecting, RemoteConnectionRuntimeState.snapshot().status)

        RemoteConnectionRuntimeState.markConnected("https://home.example.test", nowMillis = 10_000L)
        val connected = RemoteConnectionRuntimeState.snapshot()
        assertEquals(RemoteConnectionStatus.Connected, connected.status)
        assertEquals("https://home.example.test", connected.homeAssistantUrl)
        assertEquals(10_000L, connected.connectedAtMillis)

        RemoteConnectionRuntimeState.markDisconnected()
        val disconnected = RemoteConnectionRuntimeState.snapshot()
        assertEquals(RemoteConnectionStatus.Disconnected, disconnected.status)
        assertNull(disconnected.lastError)
    }
}
