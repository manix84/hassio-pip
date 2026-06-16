package com.hatvpip.receiver

import android.content.Context
import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.net.SocketTimeoutException
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import org.json.JSONArray
import org.json.JSONObject

class LocalControlServer(
    private val context: Context,
    private val port: Int = DEFAULT_PORT,
    private val onShow: (ShowCommand) -> Unit,
    private val onClose: () -> Unit,
    private val onPairingChanged: () -> Unit = {},
    private val onStarted: (Int) -> Unit = {}
) {
    @Volatile
    private var running = false
    private var serverSocket: ServerSocket? = null
    private val executor: ExecutorService = Executors.newCachedThreadPool()

    fun start() {
        if (running) return
        running = true
        executor.execute {
            runCatching {
                ServerSocket(port, 0, InetAddress.getByName("0.0.0.0")).use { socket ->
                    serverSocket = socket
                    socket.soTimeout = ACCEPT_TIMEOUT_MS
                    ControlRuntimeState.markStarted(port)
                    onStarted(port)
                    AppLog.controlServerStarted(port)
                    while (running) {
                        try {
                            executor.execute(ClientHandler(socket.accept()))
                        } catch (_: SocketTimeoutException) {
                            // Timeout lets the loop observe `running` without blocking forever.
                        }
                    }
                }
            }.onFailure { error ->
                if (running) {
                    AppLog.error("Local control server failed", error)
                }
            }
        }
    }

    fun stop() {
        running = false
        runCatching { serverSocket?.close() }
        executor.shutdownNow()
        ControlRuntimeState.markStopped()
        AppLog.controlServerStopped()
    }

    private inner class ClientHandler(private val socket: Socket) : Runnable {
        override fun run() {
            socket.use { client ->
                val request = client.readHttpRequest()
                val response = handle(request)
                ControlRuntimeState.recordRequest(request.method, request.path, response.status)
                AppLog.controlRequest(request.method, request.path, response.status)
                client.writeHttpResponse(response)
            }
        }
    }

    private fun handle(request: HttpRequest): HttpResponse =
        when {
            request.method == "GET" && request.path == "/" -> rootResponse()
            request.method == "GET" && request.path == "/status" -> statusResponse()
            request.method == "POST" && request.path == "/pair/start" -> pairStartResponse(request.body)
            request.method == "POST" && request.path == "/pair/confirm" -> pairConfirmResponse(request.body)
            request.method == "POST" && request.path == "/show" -> showResponse(request)
            request.method == "POST" && request.path == "/close" -> closeResponse(request)
            request.path in KNOWN_ENDPOINTS -> HttpResponse.json(
                status = 405,
                body = JSONObject()
                    .put("error", "Method not allowed")
                    .put("method", request.method)
                    .put("path", request.path)
                    .put("allowedMethods", allowedMethodsFor(request.path))
            )
            else -> HttpResponse.json(
                status = 404,
                body = JSONObject()
                    .put("error", "Endpoint not found")
                    .put("path", request.path)
            )
        }

    private fun rootResponse(): HttpResponse =
        HttpResponse.json(
            status = 200,
            body = JSONObject()
                .put("app", "HA TV PiP Receiver")
                .put("version", BuildConfig.VERSION_NAME)
                .put("apiVersion", 1)
                .put("pairingRequired", PairingState.snapshot(context).pairingRequired)
                .put(
                    "endpoints",
                    JSONArray()
                        .put(endpoint("GET", "/", "API metadata"))
                        .put(endpoint("GET", "/status", "Receiver and playback status"))
                        .put(endpoint("POST", "/pair/start", "Start local pairing"))
                        .put(endpoint("POST", "/pair/confirm", "Confirm local pairing code"))
                        .put(endpoint("POST", "/show", "Show an HLS stream"))
                        .put(endpoint("POST", "/close", "Close the active display"))
                )
        )

    private fun statusResponse(): HttpResponse {
        val playback = ReceiverRuntimeState.snapshot()
        val control = ControlRuntimeState.snapshot()
        val discovery = DiscoveryRuntimeState.snapshot()
        val pairing = PairingState.snapshot(context)
        val lastRequest = control.lastRequest
        val body = JSONObject()
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
            .put("controlPort", port)
            .put("controlRunning", control.running)
            .put("controlUptimeSeconds", control.uptimeSeconds(System.currentTimeMillis()))
            .put("requestCount", control.requestCount)
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
            .put("error", playback.errorMessage)

        return HttpResponse.json(status = 200, body = body)
    }

    private fun pairStartResponse(body: String): HttpResponse {
        val request = parsePairingStartRequest(body).getOrElse { error ->
            return HttpResponse.json(
                status = 400,
                body = JSONObject().put("error", error.message ?: "Invalid pairing start request")
            )
        }

        val pairing = PairingState.startPairing(context, request).getOrElse { error ->
            return HttpResponse.json(
                status = 409,
                body = JSONObject().put("error", error.message ?: "Pairing failed")
            )
        }
        AppLog.pairingEvent("pairing_started", pairing.state.wireName)
        onPairingChanged()

        return HttpResponse.json(
            status = 202,
            body = JSONObject()
                .put("accepted", true)
                .put("pairingState", pairing.state.wireName)
                .put("expiresInSeconds", PAIRING_CODE_TTL_SECONDS)
        )
    }

    private fun pairConfirmResponse(body: String): HttpResponse {
        val request = parsePairingConfirmRequest(body).getOrElse { error ->
            return HttpResponse.json(
                status = 400,
                body = JSONObject().put("error", error.message ?: "Invalid pairing confirm request")
            )
        }

        val result = PairingState.confirmPairing(context, request).getOrElse { error ->
            return HttpResponse.json(
                status = 401,
                body = JSONObject().put("error", error.message ?: "Pairing failed")
            )
        }
        AppLog.pairingEvent("pairing_confirmed", PairingStatus.Paired.wireName)
        onPairingChanged()

        return HttpResponse.json(
            status = 200,
            body = JSONObject()
                .put("paired", true)
                .put("clientId", result.clientId)
                .put("clientName", result.clientName)
                .put("token", result.token)
        )
    }

    private fun showResponse(request: HttpRequest): HttpResponse {
        val authFailure = authorizeRequest(body = request.body, request = request)
        if (authFailure != null) return authFailure

        val command = ShowCommand.fromJson(request.body).getOrElse { error ->
            return HttpResponse.json(
                status = 400,
                body = JSONObject().put("error", error.message ?: "Invalid show request")
            )
        }

        val replacedExistingPlayback = ReceiverRuntimeState.snapshot().mode != ReceiverPlaybackMode.Idle
        ReceiverRuntimeState.update(
            ReceiverPlaybackSnapshot(
                status = PlaybackStatus.Buffering,
                isPlaying = false,
                mode = ReceiverPlaybackMode.FullScreen,
                title = command.title,
                url = command.url
            )
        )
        onShow(command)
        return HttpResponse.json(
            status = 202,
            body = JSONObject()
                .put("accepted", true)
                .put("replaced", replacedExistingPlayback)
                .put("title", command.title)
                .put("url", command.url)
                .put("streamType", command.streamType.wireName)
                .put("previewUrl", command.previewUrl)
                .put("durationSeconds", command.durationSeconds)
                .put("enterPip", command.enterPip)
        )
    }

    private fun closeResponse(request: HttpRequest): HttpResponse {
        val authFailure = authorizeRequest(body = request.body, request = request)
        if (authFailure != null) return authFailure

        val playback = ReceiverRuntimeState.snapshot()
        val wasActive = playback.mode != ReceiverPlaybackMode.Idle
        onClose()
        return HttpResponse.json(
            status = 202,
            body = JSONObject()
                .put("accepted", true)
                .put("closed", wasActive)
                .put("previousDisplayMode", playback.mode.wireName)
        )
    }

    private fun authorizeRequest(body: String, request: HttpRequest?): HttpResponse? {
        val pairing = PairingState.snapshot(context)
        if (pairing.pairingRequired) {
            return HttpResponse.json(
                status = 401,
                body = JSONObject()
                    .put("error", "pairing_required")
                    .put("pairingState", pairing.state.wireName)
            )
        }

        val token = request?.bearerToken ?: tokenFromBody(body)
        if (!PairingState.isAuthorized(context, token)) {
            return HttpResponse.json(
                status = 401,
                body = JSONObject().put("error", "unauthorized")
            )
        }

        return null
    }

    private fun Socket.readHttpRequest(): HttpRequest {
        val reader = BufferedReader(InputStreamReader(getInputStream()))
        val requestLine = reader.readLine().orEmpty()
        val parts = requestLine.split(" ")
        val method = parts.getOrNull(0).orEmpty().uppercase(Locale.US)
        val path = parts.getOrNull(1).orEmpty().substringBefore("?")
        val headers = mutableMapOf<String, String>()
        var contentLength = 0

        while (true) {
            val line = reader.readLine() ?: break
            if (line.isEmpty()) break
            val separatorIndex = line.indexOf(":")
            if (separatorIndex <= 0) continue
            val name = line.substring(0, separatorIndex).trim().lowercase(Locale.US)
            val value = line.substring(separatorIndex + 1).trim()
            if (name == "content-length") {
                contentLength = value.toIntOrNull() ?: 0
            }
            headers[name] = value
        }

        val body = if (contentLength > 0) {
            val buffer = CharArray(contentLength)
            var offset = 0
            while (offset < contentLength) {
                val read = reader.read(buffer, offset, contentLength - offset)
                if (read == -1) break
                offset += read
            }
            buffer.concatToString(endIndex = offset)
        } else {
            ""
        }

        return HttpRequest(method = method, path = path, headers = headers, body = body)
    }

    private fun Socket.writeHttpResponse(response: HttpResponse) {
        val writer = BufferedWriter(OutputStreamWriter(getOutputStream()))
        writer.write("HTTP/1.1 ${response.status} ${response.reason}\r\n")
        writer.write("Content-Type: application/json; charset=utf-8\r\n")
        writer.write("Content-Length: ${response.body.toByteArray().size}\r\n")
        writer.write("Connection: close\r\n")
        writer.write("\r\n")
        writer.write(response.body)
        writer.flush()
    }

    companion object {
        const val DEFAULT_PORT = 8765
        private const val ACCEPT_TIMEOUT_MS = 500
        private const val PAIRING_CODE_TTL_SECONDS = 300
        private val KNOWN_ENDPOINTS = setOf("/", "/status", "/pair/start", "/pair/confirm", "/show", "/close")
    }
}

private fun endpoint(method: String, path: String, description: String): JSONObject =
    JSONObject()
        .put("method", method)
        .put("path", path)
        .put("description", description)

private fun allowedMethodsFor(path: String): JSONArray =
    JSONArray().apply {
        when (path) {
            "/", "/status" -> put("GET")
            "/pair/start", "/pair/confirm", "/show", "/close" -> put("POST")
        }
    }

private data class HttpRequest(
    val method: String,
    val path: String,
    val headers: Map<String, String>,
    val body: String
) {
    val bearerToken: String?
        get() {
            val authorization = headers["authorization"] ?: return null
            return authorization
                .takeIf { it.startsWith("Bearer ", ignoreCase = true) }
                ?.substringAfter(" ")
                ?.trim()
                ?.takeIf { it.isNotEmpty() }
        }
}

private data class HttpResponse(
    val status: Int,
    val reason: String,
    val body: String
) {
    companion object {
        fun json(status: Int, body: JSONObject): HttpResponse =
            HttpResponse(
                status = status,
                reason = when (status) {
                    200 -> "OK"
                    202 -> "Accepted"
                    400 -> "Bad Request"
                    401 -> "Unauthorized"
                    409 -> "Conflict"
                    405 -> "Method Not Allowed"
                    404 -> "Not Found"
                    else -> "OK"
                },
                body = body.toString()
            )
    }
}

private fun parsePairingStartRequest(body: String): Result<PairingStartRequest> =
    runCatching {
        val json = JSONObject(body.ifBlank { "{}" })
        PairingStartRequest(
            clientId = json.optString("clientId").ifBlank { "home-assistant" },
            clientName = json.optString("clientName").ifBlank { "Home Assistant" }
        )
    }

private fun parsePairingConfirmRequest(body: String): Result<PairingConfirmRequest> =
    runCatching {
        val json = JSONObject(body)
        PairingConfirmRequest(
            clientId = json.optString("clientId").ifBlank { "home-assistant" },
            clientName = json.optString("clientName").ifBlank { "Home Assistant" },
            code = json.getString("code").trim()
        )
    }

private fun tokenFromBody(body: String): String? =
    runCatching {
        JSONObject(body).optString("token").takeIf { it.isNotBlank() }
    }.getOrNull()
