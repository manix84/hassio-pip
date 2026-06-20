package com.hatvpip.receiver

import android.content.Context
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class RemoteReceiverClient(
    private val context: Context,
    private val onShow: (ShowCommand) -> Unit,
    private val onClose: () -> Unit,
    private val client: OkHttpClient = defaultClient()
) {
    private var webSocket: WebSocket? = null
    private var currentConfig: RemoteConnectionConfig? = null
    private var nextMessageId = 1
    private var registerMessageId: Int? = null

    fun connect(config: RemoteConnectionConfig) {
        disconnect()
        currentConfig = config

        if (!config.enabled) {
            RemoteConnectionRuntimeState.markDisabled(config.homeAssistantUrl.ifBlank { null })
            return
        }

        val pairingToken = PairingState.pairedToken(context)
        if (pairingToken.isNullOrBlank()) {
            RemoteConnectionRuntimeState.markDisconnected("receiver_not_paired")
            return
        }

        val webSocketUrl = runCatching {
            homeAssistantWebSocketUrl(config.homeAssistantUrl)
        }.getOrElse { error ->
            RemoteConnectionRuntimeState.markDisconnected(error.message ?: "invalid_url")
            return
        }

        RemoteConnectionRuntimeState.markConnecting(config.homeAssistantUrl)
        webSocket = client.newWebSocket(
            Request.Builder().url(webSocketUrl).build(),
            Listener(config, pairingToken)
        )
    }

    fun reconnect() {
        connect(RemoteConnectionSettings.load(context))
    }

    fun disconnect() {
        webSocket?.close(NORMAL_CLOSE_CODE, "receiver reconnect")
        webSocket = null
    }

    private fun sendAuthentication(webSocket: WebSocket, accessToken: String) {
        webSocket.send(
            JSONObject()
                .put("type", "auth")
                .put("access_token", accessToken)
                .toString()
        )
    }

    private fun sendRegistration(
        webSocket: WebSocket,
        config: RemoteConnectionConfig,
        pairingToken: String
    ) {
        val id = nextMessageId++
        registerMessageId = id
        webSocket.send(
            JSONObject()
                .put("id", id)
                .put("type", WS_TYPE_REGISTER)
                .put("device_id", ReceiverDeviceInfo.stableDeviceId(context))
                .put("name", ReceiverDeviceInfo.deviceName(context))
                .put("token", pairingToken)
                .toString()
        )
        AppLog.remoteConnectionEvent(
            event = "remote_registration_sent",
            state = RemoteConnectionStatus.Connecting.wireName
        )
    }

    private fun handleMessage(text: String, config: RemoteConnectionConfig, pairingToken: String) {
        val json = runCatching { JSONObject(text) }.getOrNull() ?: return
        when (json.optString("type")) {
            "auth_required" -> webSocket?.let {
                sendAuthentication(it, config.accessToken)
            }
            "auth_ok" -> webSocket?.let {
                sendRegistration(it, config, pairingToken)
            }
            "auth_invalid" -> {
                RemoteConnectionRuntimeState.markDisconnected("auth_invalid")
                AppLog.remoteConnectionEvent("remote_auth_invalid", RemoteConnectionStatus.Error.wireName)
            }
            "result" -> handleResult(json, config)
            "event" -> handleEvent(json)
        }
    }

    private fun handleResult(json: JSONObject, config: RemoteConnectionConfig) {
        if (json.optInt("id") != registerMessageId) return
        if (!json.optBoolean("success", true)) {
            RemoteConnectionRuntimeState.markDisconnected("registration_failed")
            AppLog.remoteConnectionEvent("remote_registration_failed", RemoteConnectionStatus.Error.wireName)
            return
        }
        RemoteConnectionRuntimeState.markConnected(config.homeAssistantUrl)
        AppLog.remoteConnectionEvent("remote_connected", RemoteConnectionStatus.Connected.wireName)
    }

    private fun handleEvent(json: JSONObject) {
        val event = json.optJSONObject("event") ?: return
        if (event.optString("event_type") != EVENT_RECEIVER_COMMAND) return
        val data = event.optJSONObject("data") ?: return
        when (data.optString("command")) {
            "show" -> {
                val payload = data.optJSONObject("payload") ?: return
                ShowCommand.fromJson(payload.toString())
                    .onSuccess { command ->
                        RemoteConnectionRuntimeState.markMessage()
                        onShow(command)
                    }
                    .onFailure { error ->
                        RemoteConnectionRuntimeState.markDisconnected(
                            error.message ?: "invalid_show_command"
                        )
                    }
            }
            "close" -> {
                RemoteConnectionRuntimeState.markMessage()
                onClose()
            }
            "status" -> {
                RemoteConnectionRuntimeState.markMessage()
                sendStatusResponse(data)
            }
        }
    }

    private fun sendStatusResponse(data: JSONObject) {
        val requestId = data.optInt("requestId", 0)
        if (requestId <= 0) return
        webSocket?.send(
            JSONObject()
                .put("id", nextMessageId++)
                .put("type", WS_TYPE_STATUS_RESPONSE)
                .put("device_id", ReceiverDeviceInfo.stableDeviceId(context))
                .put("request_id", requestId)
                .put("status", ReceiverStatusPayload.build(context))
                .toString()
        )
    }

    private inner class Listener(
        private val config: RemoteConnectionConfig,
        private val pairingToken: String
    ) : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            AppLog.remoteConnectionEvent("remote_socket_open", RemoteConnectionStatus.Connecting.wireName)
        }

        override fun onMessage(webSocket: WebSocket, text: String) {
            handleMessage(text, config, pairingToken)
        }

        override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
            RemoteConnectionRuntimeState.markDisconnected(reason.ifBlank { null })
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            RemoteConnectionRuntimeState.markDisconnected(t.message ?: "connection_failed")
            AppLog.error("Remote receiver connection failed", t)
        }
    }

    companion object {
        const val EVENT_RECEIVER_COMMAND = "ha_tv_pip/receiver_command"
        const val WS_TYPE_REGISTER = "ha_tv_pip/receiver/register"
        const val WS_TYPE_STATUS_RESPONSE = "ha_tv_pip/receiver/status_response"
        private const val NORMAL_CLOSE_CODE = 1000

        fun homeAssistantWebSocketUrl(homeAssistantUrl: String): String {
            val trimmed = homeAssistantUrl.trim().trimEnd('/')
            require(trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
                "Home Assistant URL must start with http:// or https://"
            }
            val scheme = if (trimmed.startsWith("https://")) "wss://" else "ws://"
            return scheme + trimmed.substringAfter("://") + "/api/websocket"
        }

        private fun defaultClient(): OkHttpClient =
            OkHttpClient.Builder()
                .pingInterval(30, TimeUnit.SECONDS)
                .retryOnConnectionFailure(true)
                .build()
    }
}
