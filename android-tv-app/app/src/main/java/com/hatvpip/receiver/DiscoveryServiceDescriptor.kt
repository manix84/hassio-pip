package com.hatvpip.receiver

data class DiscoveryServiceDescriptor(
    val serviceName: String,
    val serviceType: String,
    val port: Int,
    val attributes: Map<String, String>
) {
    companion object {
        const val SERVICE_TYPE = "_ha-tv-pip._tcp."
        const val API_VERSION = "1"

        fun create(
            deviceId: String,
            deviceName: String,
            appVersion: String,
            port: Int
        ): DiscoveryServiceDescriptor =
            DiscoveryServiceDescriptor(
                serviceName = sanitizeServiceName(deviceName),
                serviceType = SERVICE_TYPE,
                port = port,
                attributes = mapOf(
                    "id" to deviceId,
                    "name" to deviceName,
                    "version" to appVersion,
                    "pairing" to "disabled",
                    "api" to API_VERSION
                )
            )

        private fun sanitizeServiceName(deviceName: String): String {
            val trimmed = deviceName.trim()
            return if (trimmed.isBlank()) {
                "HA TV PiP Receiver"
            } else {
                "HA TV PiP - $trimmed"
            }
        }
    }
}
