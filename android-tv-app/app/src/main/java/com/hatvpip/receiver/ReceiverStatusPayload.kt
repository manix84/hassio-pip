package com.hatvpip.receiver

import android.content.Context
import org.json.JSONObject

object ReceiverStatusPayload {
    fun build(
        context: Context,
        port: Int = LocalControlServer.DEFAULT_PORT
    ): JSONObject {
        val playback = ReceiverRuntimeState.snapshot()
        val control = ControlRuntimeState.snapshot()
        val service = ReceiverServiceRuntimeState.snapshot()
        val discovery = DiscoveryRuntimeState.snapshot()
        val pairing = PairingState.snapshot(context)
        val remote = RemoteConnectionRuntimeState.snapshot()
        val lastRequest = control.lastRequest

        return JSONObject()
            .put("app", "HA TV PiP Receiver")
            .put("version", BuildConfig.VERSION_NAME)
            .put("deviceId", ReceiverDeviceInfo.stableDeviceId(context))
            .put("deviceName", ReceiverDeviceInfo.deviceName(context))
            .put("pairingRequired", pairing.pairingRequired)
            .put(
                "pairing",
                JSONObject()
                    .put("state", pairing.state.wireName)
                    .put("pendingClientName", pairing.pendingClientName)
                    .put("pairedClientName", pairing.pairedClientName)
            )
            .put("apiVersion", 1)
            .put("capabilities", ReceiverCapabilities.toJson())
            .put("controlPort", port)
            .put("controlRunning", control.running)
            .put("controlUptimeSeconds", control.uptimeSeconds(System.currentTimeMillis()))
            .put("requestCount", control.requestCount)
            .put(
                "service",
                JSONObject()
                    .put("running", service.running)
                    .put("foreground", service.foreground)
                    .put("startCount", service.startCount)
                    .put("lastStartReason", service.lastStartReason)
                    .put("lastStartedAtMillis", service.lastStartedAtMillis)
                    .put("lastDestroyedAtMillis", service.lastDestroyedAtMillis)
                    .put("lastBootReceiverAction", service.lastBootReceiverAction)
                    .put("lastBootReceiverAtMillis", service.lastBootReceiverAtMillis)
            )
            .put(
                "management",
                JSONObject()
                    .put("launcherVisible", LauncherVisibility.isVisible(context))
                    .put("openPath", "/management/open")
                    .put("remotePath", "/management/remote")
            )
            .put(
                "discovery",
                JSONObject()
                    .put("running", discovery.running)
                    .put("serviceName", discovery.serviceName)
                    .put("serviceType", discovery.serviceType)
                    .put("port", discovery.port)
                    .put("error", discovery.errorMessage)
            )
            .put(
                "remote",
                JSONObject()
                    .put("status", remote.status.wireName)
                    .put("homeAssistantUrl", remote.homeAssistantUrl)
                    .put("lastError", remote.lastError)
                    .put("connectedAtMillis", remote.connectedAtMillis)
                    .put("lastMessageAtMillis", remote.lastMessageAtMillis)
                    .put("connectionAttemptCount", remote.connectionAttemptCount)
                    .put("successfulConnectionCount", remote.successfulConnectionCount)
                    .put("messageCount", remote.messageCount)
                    .put("lastConnectionAttemptAtMillis", remote.lastConnectionAttemptAtMillis)
                    .put("lastDisconnectedAtMillis", remote.lastDisconnectedAtMillis)
                    .put("lastDisconnectReason", remote.lastDisconnectReason)
            )
            .put(
                "lastRequest",
                lastRequest?.let {
                    JSONObject()
                        .put("method", it.method)
                        .put("path", it.path)
                        .put("status", it.status)
                }
            )
            .put("playbackState", playback.wirePlaybackState)
            .put("displayMode", playback.mode.wireName)
            .put("title", playback.title)
            .put("url", playback.url)
            .put("previewUrl", playback.previewUrl)
            .put("fallbackUrl", playback.fallbackUrl)
            .put("fallbackStreamType", playback.fallbackStreamType)
            .put("streamType", playback.streamType)
            .put("error", playback.errorMessage)
            .put(
                "playback",
                JSONObject()
                    .put("state", playback.wirePlaybackState)
                    .put("status", playback.status.name.lowercase())
                    .put("isPlaying", playback.isPlaying)
                    .put("displayMode", playback.mode.wireName)
                    .put("title", playback.title)
                    .put("url", playback.url)
                    .put("previewUrl", playback.previewUrl)
                    .put("fallbackUrl", playback.fallbackUrl)
                    .put("fallbackStreamType", playback.fallbackStreamType)
                    .put("streamType", playback.streamType)
                    .put("error", playback.errorMessage)
                    .put("updatedAtMillis", playback.updatedAtMillis)
            )
    }
}
