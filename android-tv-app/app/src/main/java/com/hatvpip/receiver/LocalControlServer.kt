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
            request.method == "POST" && request.path == "/show" -> showResponse(request.body)
            request.method == "POST" && request.path == "/close" -> closeResponse()
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
                .put("pairingRequired", false)
                .put(
                    "endpoints",
                    JSONArray()
                        .put(endpoint("GET", "/", "API metadata"))
                        .put(endpoint("GET", "/status", "Receiver and playback status"))
                        .put(endpoint("POST", "/show", "Show an HLS stream"))
                        .put(endpoint("POST", "/close", "Close the active display"))
                )
        )

    private fun statusResponse(): HttpResponse {
        val playback = ReceiverRuntimeState.snapshot()
        val control = ControlRuntimeState.snapshot()
        val discovery = DiscoveryRuntimeState.snapshot()
        val lastRequest = control.lastRequest
        val body = JSONObject()
            .put("app", "HA TV PiP Receiver")
            .put("version", BuildConfig.VERSION_NAME)
            .put("deviceId", ReceiverDeviceInfo.stableDeviceId(context))
            .put("deviceName", ReceiverDeviceInfo.deviceName(context))
            .put("pairingRequired", false)
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

    private fun showResponse(body: String): HttpResponse {
        val command = ShowCommand.fromJson(body).getOrElse { error ->
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
                .put("durationSeconds", command.durationSeconds)
                .put("enterPip", command.enterPip)
        )
    }

    private fun closeResponse(): HttpResponse {
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

    private fun Socket.readHttpRequest(): HttpRequest {
        val reader = BufferedReader(InputStreamReader(getInputStream()))
        val requestLine = reader.readLine().orEmpty()
        val parts = requestLine.split(" ")
        val method = parts.getOrNull(0).orEmpty().uppercase(Locale.US)
        val path = parts.getOrNull(1).orEmpty().substringBefore("?")
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

        return HttpRequest(method = method, path = path, body = body)
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
        private val KNOWN_ENDPOINTS = setOf("/", "/status", "/show", "/close")
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
            "/show", "/close" -> put("POST")
        }
    }

private data class HttpRequest(
    val method: String,
    val path: String,
    val body: String
)

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
                    405 -> "Method Not Allowed"
                    404 -> "Not Found"
                    else -> "OK"
                },
                body = body.toString()
            )
    }
}
