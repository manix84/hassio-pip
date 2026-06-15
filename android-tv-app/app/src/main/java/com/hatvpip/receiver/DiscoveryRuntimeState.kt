package com.hatvpip.receiver

import java.util.concurrent.atomic.AtomicReference

data class DiscoverySnapshot(
    val running: Boolean = false,
    val serviceName: String? = null,
    val serviceType: String = DiscoveryServiceDescriptor.SERVICE_TYPE,
    val port: Int = LocalControlServer.DEFAULT_PORT,
    val errorMessage: String? = null
)

object DiscoveryRuntimeState {
    private val current = AtomicReference(DiscoverySnapshot())

    fun snapshot(): DiscoverySnapshot = current.get()

    fun markRegistering(descriptor: DiscoveryServiceDescriptor) {
        current.set(
            DiscoverySnapshot(
                running = false,
                serviceName = descriptor.serviceName,
                serviceType = descriptor.serviceType,
                port = descriptor.port
            )
        )
    }

    fun markRegistered(serviceName: String, port: Int) {
        current.updateAndGet { snapshot ->
            snapshot.copy(
                running = true,
                serviceName = serviceName,
                port = port,
                errorMessage = null
            )
        }
    }

    fun markFailed(serviceName: String, port: Int, errorMessage: String) {
        current.updateAndGet { snapshot ->
            snapshot.copy(
                running = false,
                serviceName = serviceName,
                port = port,
                errorMessage = errorMessage
            )
        }
    }

    fun markStopped() {
        current.updateAndGet { snapshot ->
            snapshot.copy(running = false)
        }
    }
}
