package com.hatvpip.receiver

import android.app.Service
import android.content.Intent
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import java.io.BufferedInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.URL

class OverlayPlayerService : Service() {
    private lateinit var windowManager: WindowManager
    private var overlayView: ViewGroup? = null
    private var player: ExoPlayer? = null
    private var errorTextView: TextView? = null
    private var title: String = ""
    private var url: String = PlayerActivity.TEST_STREAM_URL
    private var previewUrl: String? = null
    private var fallbackUrl: String? = null
    private var fallbackStreamType: StreamType? = null
    private var showNotification: Boolean = false
    private var message: String? = null
    private var style: NotificationStyle = NotificationStyle()
    private var streamType: StreamType = StreamType.Hls
    private var durationSeconds: Int? = null
    @Volatile private var mjpegRunning: Boolean = false
    private var mjpegThread: Thread? = null
    private val autoCloseHandler = Handler(Looper.getMainLooper())
    private val mainHandler = Handler(Looper.getMainLooper())

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> stopSelf()
            else -> {
                title = intent?.getStringExtra(PlayerActivity.EXTRA_TITLE) ?: title
                url = intent?.getStringExtra(PlayerActivity.EXTRA_URL) ?: url
                previewUrl = intent?.getStringExtra(PlayerActivity.EXTRA_PREVIEW_URL)
                fallbackUrl = intent?.getStringExtra(PlayerActivity.EXTRA_FALLBACK_URL)
                fallbackStreamType = when (
                    intent?.getStringExtra(PlayerActivity.EXTRA_FALLBACK_STREAM_TYPE)
                ) {
                    StreamType.Hls.wireName -> StreamType.Hls
                    StreamType.Mjpeg.wireName -> StreamType.Mjpeg
                    StreamType.Snapshot.wireName -> StreamType.Snapshot
                    else -> null
                }
                showNotification = intent?.getBooleanExtra(
                    PlayerActivity.EXTRA_SHOW_NOTIFICATION,
                    false
                ) ?: false
                message = intent?.getStringExtra(PlayerActivity.EXTRA_MESSAGE)
                style = NotificationStyle(
                    position = NotificationPosition.fromWire(
                        intent?.getStringExtra(PlayerActivity.EXTRA_POSITION)
                            ?: NotificationPosition.TopRight.wireName
                    ),
                    titleColor = intent?.getStringExtra(PlayerActivity.EXTRA_TITLE_COLOR) ?: "#50BFF2",
                    titleSize = intent?.getIntExtra(PlayerActivity.EXTRA_TITLE_SIZE, 24)?.coerceIn(10, 48) ?: 24,
                    messageColor = intent?.getStringExtra(PlayerActivity.EXTRA_MESSAGE_COLOR) ?: "#fbf5f5",
                    messageSize = intent?.getIntExtra(PlayerActivity.EXTRA_MESSAGE_SIZE, 18)?.coerceIn(10, 40) ?: 18,
                    backgroundColor = intent?.getStringExtra(PlayerActivity.EXTRA_BACKGROUND_COLOR) ?: DEFAULT_BACKGROUND_COLOR,
                    width = intent?.takeIf {
                        it.hasExtra(PlayerActivity.EXTRA_WIDTH)
                    }?.getIntExtra(PlayerActivity.EXTRA_WIDTH, 0)?.takeIf { it > 0 },
                    height = intent?.takeIf {
                        it.hasExtra(PlayerActivity.EXTRA_HEIGHT)
                    }?.getIntExtra(PlayerActivity.EXTRA_HEIGHT, 0)?.takeIf { it > 0 }
                )
                streamType = when (intent?.getStringExtra(PlayerActivity.EXTRA_STREAM_TYPE)) {
                    StreamType.Mjpeg.wireName -> StreamType.Mjpeg
                    StreamType.Snapshot.wireName -> StreamType.Snapshot
                    StreamType.Notification.wireName -> StreamType.Notification
                    else -> StreamType.Hls
                }
                durationSeconds = intent?.takeIf {
                    it.hasExtra(PlayerActivity.EXTRA_DURATION_SECONDS)
                }?.getIntExtra(PlayerActivity.EXTRA_DURATION_SECONDS, 0)?.takeIf { it > 0 }
                showOverlay()
            }
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        autoCloseHandler.removeCallbacksAndMessages(null)
        removeOverlay()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun showOverlay() {
        if (overlayView != null) {
            removeOverlay()
        }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBackground()
            // Overlay video uses a texture-backed PlayerView so the outer outline can clip
            // the whole notification into a single rounded glass container.
            clipToOutline = true
        }
        if (streamType == StreamType.Notification) {
            addNotificationContent(root, fillHeight = style.height != null)
        } else {
            val mediaContainer = FrameLayout(this).apply {
                setBackgroundColor(Color.BLACK)
                layoutParams = mediaLayoutParams()
            }
            if (streamType == StreamType.Snapshot) {
                addSnapshotView(mediaContainer, url, updateStateOnLoad = true)
            } else if (streamType == StreamType.Mjpeg) {
                addMjpegView(mediaContainer)
            } else {
                addPlayerView(mediaContainer)
            }

            errorTextView = buildErrorTextView()
            mediaContainer.addView(errorTextView)
            root.addView(mediaContainer)

            if (showNotification) {
                addNotificationContent(root, fillHeight = false)
            }
        }

        val params = WindowManager.LayoutParams(
            overlayWidth(),
            overlayHeight(),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = overlayGravity()
            x = OVERLAY_MARGIN_PX
            y = OVERLAY_MARGIN_PX
        }

        runCatching {
            windowManager.addView(root, params)
            overlayView = root
            updatePlaybackState(
                status = if (streamType == StreamType.Notification) PlaybackStatus.Ready else PlaybackStatus.Buffering,
                isPlaying = false,
                errorMessage = null
            )
            AppLog.playbackStart(url)
            scheduleAutoClose()
        }.onFailure { error ->
            AppLog.error("Unable to show overlay fallback", error)
            player?.release()
            player = null
            stopSelf()
        }
    }

    private fun roundedBackground(): GradientDrawable =
        GradientDrawable().apply {
            setColor(parseColorOrDefault(style.backgroundColor, DEFAULT_BACKGROUND_COLOR_INT))
            cornerRadius = NOTIFICATION_CORNER_RADIUS_PX
        }

    private fun buildErrorTextView(): TextView =
        TextView(this).apply {
            setTextColor(Color.WHITE)
            setBackgroundColor(0xCC000000.toInt())
            textSize = 14f
            gravity = Gravity.CENTER
            setPadding(16, 12, 16, 12)
            visibility = TextView.GONE
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM
            )
        }

    private fun addNotificationContent(root: LinearLayout, fillHeight: Boolean) {
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 20, 24, 20)
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                if (fillHeight) {
                    ViewGroup.LayoutParams.MATCH_PARENT
                } else {
                    ViewGroup.LayoutParams.WRAP_CONTENT
                }
            )
        }
        TextView(this).apply {
            text = title.ifBlank { getString(R.string.notification_default_title) }
            setTextColor(parseColorOrDefault(style.titleColor, Color.rgb(80, 191, 242)))
            textSize = style.titleSize.toFloat()
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            includeFontPadding = false
            content.addView(this)
        }
        message?.takeIf { it.isNotBlank() }?.let { body ->
            TextView(this).apply {
                text = body
                setTextColor(parseColorOrDefault(style.messageColor, Color.rgb(251, 245, 245)))
                textSize = style.messageSize.toFloat()
                setPadding(0, 10, 0, 0)
                includeFontPadding = false
                content.addView(this)
            }
        }
        root.addView(content)
    }

    private fun addPlayerView(root: FrameLayout) {
        val previewImageView = previewUrl?.let { imageUrl ->
            addSnapshotView(root, imageUrl, updateStateOnLoad = false)
        }
        lateinit var playerView: PlayerView
        var fallbackStarted = false
        val overlayPlayer = buildReceiverPlayer(this).also { exoPlayer ->
            exoPlayer.addListener(
                object : Player.Listener {
                    override fun onPlaybackStateChanged(playbackState: Int) {
                        val playerError = exoPlayer.playerError
                        if (playerError == null && playbackState == Player.STATE_READY) {
                            playerView.alpha = 1f
                            previewImageView?.visibility = ImageView.GONE
                        }
                        updatePlaybackState(
                            status = playerError?.let { PlaybackStatus.Error }
                                ?: playbackState.toPlaybackStatus(),
                            isPlaying = exoPlayer.isPlaying,
                            errorMessage = playerError?.toDisplayMessage()
                        )
                    }

                    override fun onIsPlayingChanged(isPlaying: Boolean) {
                        val playerError = exoPlayer.playerError
                        if (playerError == null && isPlaying) {
                            playerView.alpha = 1f
                            previewImageView?.visibility = ImageView.GONE
                        }
                        updatePlaybackState(
                            status = playerError?.let { PlaybackStatus.Error }
                                ?: exoPlayer.playbackState.toPlaybackStatus(),
                            isPlaying = isPlaying,
                            errorMessage = playerError?.toDisplayMessage()
                        )
                    }

                    override fun onPlayerError(error: PlaybackException) {
                        val message = error.toDisplayMessage()
                        val playableFallbackUrl = fallbackUrl
                        if (
                            !fallbackStarted &&
                            playableFallbackUrl != null &&
                            fallbackStreamType == StreamType.Mjpeg
                        ) {
                            fallbackStarted = true
                            AppLog.error(
                                "Overlay playback failed, starting MJPEG fallback: $message",
                                error
                            )
                            exoPlayer.release()
                            playerView.visibility = PlayerView.GONE
                            url = playableFallbackUrl
                            streamType = StreamType.Mjpeg
                            updatePlaybackState(
                                status = PlaybackStatus.Buffering,
                                isPlaying = false,
                                errorMessage = message
                            )
                            addMjpegView(root, previewImageView)
                            return
                        }
                        val hasPreviewFallback = previewImageView != null
                        if (hasPreviewFallback) {
                            playerView.alpha = 0f
                            previewImageView.visibility = ImageView.VISIBLE
                        }
                        updatePlaybackState(
                            status = PlaybackStatus.Error,
                            isPlaying = false,
                            errorMessage = if (hasPreviewFallback) {
                                getString(R.string.snapshot_fallback_after_video_error, message)
                            } else {
                                message
                            }
                        )
                        errorTextView?.text = error.toOverlayMessage(this@OverlayPlayerService)
                        errorTextView?.visibility = if (hasPreviewFallback) {
                            TextView.GONE
                        } else {
                            TextView.VISIBLE
                        }
                        AppLog.error("Overlay playback failed: $message", error)
                    }
                }
            )
            exoPlayer.setMediaItem(MediaItem.fromUri(url))
            exoPlayer.repeatMode = Player.REPEAT_MODE_ONE
            exoPlayer.playWhenReady = true
            exoPlayer.prepare()
        }
        player = overlayPlayer

        playerView = LayoutInflater.from(this)
            .inflate(R.layout.overlay_player_view, root, false) as PlayerView
        playerView.apply {
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            useController = false
            this.player = overlayPlayer
            alpha = if (previewImageView == null) 1f else 0.01f
        }
        root.addView(playerView)
    }

    private fun addMjpegView(root: FrameLayout, existingPreviewImageView: ImageView? = null) {
        val previewImageView = existingPreviewImageView ?: previewUrl?.let { imageUrl ->
            addSnapshotView(root, imageUrl, updateStateOnLoad = false)
        }
        val streamImageView = ImageView(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            adjustViewBounds = true
            scaleType = ImageView.ScaleType.FIT_CENTER
            setBackgroundColor(Color.BLACK)
            alpha = if (previewImageView == null) 1f else 0.01f
        }
        root.addView(streamImageView)

        mjpegRunning = true
        mjpegThread = Thread {
            var firstFrameRendered = false
            runCatching {
                val connection = URL(url).openConnection().apply {
                    connectTimeout = MJPEG_CONNECT_TIMEOUT_MS
                    readTimeout = MJPEG_READ_TIMEOUT_MS
                }
                BufferedInputStream(connection.getInputStream()).use { stream ->
                    while (mjpegRunning) {
                        val frame = readJpegFrame(stream) ?: break
                        val bitmap = BitmapFactory.decodeByteArray(frame, 0, frame.size)
                            ?: error(getString(R.string.error_snapshot_unsupported_image))
                        mainHandler.post {
                            streamImageView.setImageBitmap(bitmap)
                            streamImageView.alpha = 1f
                            previewImageView?.visibility = ImageView.GONE
                            if (!firstFrameRendered) {
                                firstFrameRendered = true
                                updatePlaybackState(
                                    status = PlaybackStatus.Ready,
                                    isPlaying = true,
                                    errorMessage = null
                                )
                            }
                        }
                    }
                }
            }.onFailure { error ->
                mainHandler.post {
                    val message = error.message ?: getString(R.string.error_unknown_snapshot)
                    val hasPreviewFallback = previewImageView != null
                    if (hasPreviewFallback) {
                        streamImageView.alpha = 0f
                        previewImageView.visibility = ImageView.VISIBLE
                    }
                    updatePlaybackState(
                        status = PlaybackStatus.Error,
                        isPlaying = false,
                        errorMessage = if (hasPreviewFallback) {
                            getString(R.string.snapshot_fallback_after_video_error, message)
                        } else {
                            message
                        }
                    )
                    errorTextView?.text = getString(R.string.snapshot_unavailable)
                    errorTextView?.visibility = if (hasPreviewFallback) {
                        TextView.GONE
                    } else {
                        TextView.VISIBLE
                    }
                    AppLog.error("MJPEG stream failed: $message", error)
                }
            }
        }.apply { start() }
    }

    private fun readJpegFrame(stream: BufferedInputStream): ByteArray? {
        val frame = ByteArrayOutputStream()
        var previous = -1
        var inFrame = false

        while (mjpegRunning) {
            val current = stream.read()
            if (current == -1) {
                return null
            }

            if (!inFrame) {
                if (previous == JPEG_MARKER && current == JPEG_START_MARKER) {
                    frame.reset()
                    frame.write(JPEG_MARKER)
                    frame.write(JPEG_START_MARKER)
                    inFrame = true
                }
            } else {
                frame.write(current)
                if (frame.size() > MAX_MJPEG_FRAME_BYTES) {
                    throw IOException(
                        getString(
                            R.string.error_mjpeg_frame_too_large,
                            MAX_MJPEG_FRAME_BYTES
                        )
                    )
                }
                if (previous == JPEG_MARKER && current == JPEG_END_MARKER) {
                    return frame.toByteArray()
                }
            }
            previous = current
        }
        return null
    }

    private fun addSnapshotView(
        root: FrameLayout,
        imageUrl: String,
        updateStateOnLoad: Boolean
    ): ImageView {
        val imageView = ImageView(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            adjustViewBounds = true
            scaleType = ImageView.ScaleType.FIT_CENTER
            setBackgroundColor(android.graphics.Color.BLACK)
        }
        root.addView(imageView)

        Thread {
            runCatching {
                val connection = URL(imageUrl).openConnection().apply {
                    connectTimeout = SNAPSHOT_CONNECT_TIMEOUT_MS
                    readTimeout = SNAPSHOT_READ_TIMEOUT_MS
                }
                connection.getInputStream().use { stream ->
                    BitmapFactory.decodeStream(stream)
                        ?: error(getString(R.string.error_snapshot_unsupported_image))
                }
            }.onSuccess { bitmap ->
                mainHandler.post {
                    imageView.setImageBitmap(bitmap)
                    if (updateStateOnLoad) {
                        updatePlaybackState(
                            status = PlaybackStatus.Ready,
                            isPlaying = false,
                            errorMessage = null
                        )
                    }
                }
            }.onFailure { error ->
                mainHandler.post {
                    val message = error.message ?: getString(R.string.error_unknown_snapshot)
                    if (updateStateOnLoad) {
                        updatePlaybackState(
                            status = PlaybackStatus.Error,
                            isPlaying = false,
                            errorMessage = message
                        )
                        errorTextView?.text = getString(R.string.snapshot_unavailable)
                        errorTextView?.visibility = TextView.VISIBLE
                    }
                    AppLog.error("Snapshot load failed: $message", error)
                }
            }
        }.start()
        return imageView
    }

    private fun removeOverlay() {
        mjpegRunning = false
        mjpegThread?.interrupt()
        mjpegThread = null
        overlayView?.let { view ->
            runCatching { windowManager.removeView(view) }
        }
        overlayView = null
        errorTextView = null
        player?.release()
        player = null
        ReceiverRuntimeState.markIdle()
        AppLog.playbackStop(reason = "overlay_service_stopped")
    }

    private fun updatePlaybackState(
        status: PlaybackStatus,
        isPlaying: Boolean,
        errorMessage: String?
    ) {
        ReceiverRuntimeState.update(
            ReceiverPlaybackSnapshot(
                status = status,
                isPlaying = isPlaying,
                mode = ReceiverPlaybackMode.Overlay,
                title = title,
                url = url,
                previewUrl = previewUrl,
                streamType = streamType.wireName,
                errorMessage = errorMessage
            )
        )
    }

    private fun scheduleAutoClose() {
        autoCloseHandler.removeCallbacksAndMessages(null)
        val duration = durationSeconds ?: return
        autoCloseHandler.postDelayed({ stopSelf() }, duration * 1_000L)
    }

    private fun overlayGravity(): Int =
        when (style.position) {
            NotificationPosition.TopRight -> Gravity.TOP or Gravity.END
            NotificationPosition.TopLeft -> Gravity.TOP or Gravity.START
            NotificationPosition.BottomRight -> Gravity.BOTTOM or Gravity.END
            NotificationPosition.BottomLeft -> Gravity.BOTTOM or Gravity.START
        }

    private fun overlayWidth(): Int =
        style.width ?: if (streamType == StreamType.Notification) {
            NOTIFICATION_WIDTH_PX
        } else {
            OVERLAY_WIDTH_PX
        }

    private fun overlayHeight(): Int =
        style.height ?: if (streamType == StreamType.Notification) {
            WindowManager.LayoutParams.WRAP_CONTENT
        } else if (showNotification) {
            WindowManager.LayoutParams.WRAP_CONTENT
        } else {
            OVERLAY_HEIGHT_PX
        }

    private fun mediaLayoutParams(): LinearLayout.LayoutParams =
        if (showNotification && style.height == null) {
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                OVERLAY_HEIGHT_PX
            )
        } else {
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
        }

    companion object {
        const val ACTION_SHOW = "com.hatvpip.receiver.action.SHOW_OVERLAY"
        const val ACTION_STOP = "com.hatvpip.receiver.action.STOP_OVERLAY"
        private const val OVERLAY_WIDTH_PX = 640
        private const val OVERLAY_HEIGHT_PX = 360
        private const val NOTIFICATION_WIDTH_PX = 512
        private const val NOTIFICATION_CORNER_RADIUS_PX = 18f
        private const val OVERLAY_MARGIN_PX = 48
        private const val DEFAULT_BACKGROUND_COLOR = "#B30F0E0E"
        private const val MJPEG_CONNECT_TIMEOUT_MS = 5_000
        private const val MJPEG_READ_TIMEOUT_MS = 5_000
        private const val SNAPSHOT_CONNECT_TIMEOUT_MS = 5_000
        private const val SNAPSHOT_READ_TIMEOUT_MS = 5_000
        private const val MAX_MJPEG_FRAME_BYTES = 8 * 1024 * 1024
        private const val JPEG_MARKER = 0xFF
        private const val JPEG_START_MARKER = 0xD8
        private const val JPEG_END_MARKER = 0xD9
        private val DEFAULT_BACKGROUND_COLOR_INT = 0xB30F0E0E.toInt()
    }
}

private fun parseColorOrDefault(value: String, defaultColor: Int): Int =
    runCatching { Color.parseColor(value) }.getOrDefault(defaultColor)

private fun Int.toPlaybackStatus(): PlaybackStatus =
    when (this) {
        Player.STATE_BUFFERING -> PlaybackStatus.Buffering
        Player.STATE_READY -> PlaybackStatus.Ready
        Player.STATE_ENDED -> PlaybackStatus.Ended
        Player.STATE_IDLE -> PlaybackStatus.Idle
        else -> PlaybackStatus.Idle
    }

private fun PlaybackException.toDisplayMessage(): String =
    "$errorCodeName: ${message ?: "unknown playback error"}"

private fun PlaybackException.toOverlayMessage(context: android.content.Context): String =
    when (errorCode) {
        PlaybackException.ERROR_CODE_DECODER_INIT_FAILED ->
            context.getString(R.string.error_unsupported_video_stream)
        else -> context.getString(R.string.error_playback_error_code, errorCodeName)
    }
