package com.hatvpip.receiver

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo

class DiscoveryAdvertiser(private val context: Context) {
    private val nsdManager: NsdManager? =
        context.getSystemService(Context.NSD_SERVICE) as? NsdManager
    private var registrationListener: NsdManager.RegistrationListener? = null

    fun start(port: Int) {
        if (registrationListener != null) return

        val descriptor = DiscoveryServiceDescriptor.create(
            deviceId = ReceiverDeviceInfo.stableDeviceId(context),
            deviceName = ReceiverDeviceInfo.deviceName(context),
            appVersion = BuildConfig.VERSION_NAME,
            port = port
        )
        DiscoveryRuntimeState.markRegistering(descriptor)

        val manager = nsdManager
        if (manager == null) {
            DiscoveryRuntimeState.markFailed(
                serviceName = descriptor.serviceName,
                port = port,
                errorMessage = "Android NSD service unavailable"
            )
            AppLog.discoveryFailed(descriptor.serviceName, "Android NSD service unavailable")
            return
        }

        val serviceInfo = NsdServiceInfo().apply {
            serviceName = descriptor.serviceName
            serviceType = descriptor.serviceType
            this.port = descriptor.port
            descriptor.attributes.forEach { (key, value) ->
                setAttribute(key, value)
            }
        }

        val listener = object : NsdManager.RegistrationListener {
            override fun onServiceRegistered(info: NsdServiceInfo) {
                DiscoveryRuntimeState.markRegistered(info.serviceName, port)
                AppLog.discoveryRegistered(info.serviceName, descriptor.serviceType, port)
            }

            override fun onRegistrationFailed(info: NsdServiceInfo, errorCode: Int) {
                val message = "NSD registration failed with code $errorCode"
                DiscoveryRuntimeState.markFailed(descriptor.serviceName, port, message)
                AppLog.discoveryFailed(descriptor.serviceName, message)
                registrationListener = null
            }

            override fun onServiceUnregistered(info: NsdServiceInfo) {
                DiscoveryRuntimeState.markStopped()
                AppLog.discoveryStopped(info.serviceName)
                registrationListener = null
            }

            override fun onUnregistrationFailed(info: NsdServiceInfo, errorCode: Int) {
                AppLog.discoveryFailed(info.serviceName, "NSD unregistration failed with code $errorCode")
            }
        }

        registrationListener = listener
        manager.registerService(serviceInfo, NsdManager.PROTOCOL_DNS_SD, listener)
    }

    fun stop() {
        val listener = registrationListener ?: return
        runCatching {
            nsdManager?.unregisterService(listener)
        }.onFailure { error ->
            AppLog.error("Unable to unregister discovery service", error)
            DiscoveryRuntimeState.markStopped()
            registrationListener = null
        }
    }
}
