package com.hatvpip.receiver

import android.app.Service
import android.content.Intent
import android.graphics.BitmapFactory
import android.graphics.PixelFormat
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.view.Gravity
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.TextView
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import java.net.URL

class OverlayPlayerService : Service() {
    private lateinit var windowManager: WindowManager
    private var overlayView: FrameLayout? = null
    private var player: ExoPlayer? = null
    private var errorTextView: TextView? = null
    private var title: String = "HA TV PiP"
    private var url: String = PlayerActivity.TEST_STREAM_URL
    private var streamType: StreamType = StreamType.Hls
    private var durationSeconds: Int? = null
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
                streamType = when (intent?.getStringExtra(PlayerActivity.EXTRA_STREAM_TYPE)) {
                    StreamType.Snapshot.wireName -> StreamType.Snapshot
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

        val root = FrameLayout(this).apply {
            setBackgroundColor(android.graphics.Color.BLACK)
        }
        if (streamType == StreamType.Snapshot) {
            addSnapshotView(root)
        } else {
            addPlayerView(root)
        }

        errorTextView = TextView(this).apply {
            setTextColor(android.graphics.Color.WHITE)
            setBackgroundColor(0xCC000000.toInt())
            textSize = 14f
            gravity = Gravity.CENTER
            visibility = TextView.GONE
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }
        root.addView(errorTextView)

        val params = WindowManager.LayoutParams(
            OVERLAY_WIDTH_PX,
            OVERLAY_HEIGHT_PX,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.END
            x = OVERLAY_MARGIN_PX
            y = OVERLAY_MARGIN_PX
        }

        runCatching {
            windowManager.addView(root, params)
            overlayView = root
            updatePlaybackState(
                status = PlaybackStatus.Buffering,
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

    private fun addPlayerView(root: FrameLayout) {
        val overlayPlayer = buildReceiverPlayer(this).also { exoPlayer ->
            exoPlayer.addListener(
                object : Player.Listener {
                    override fun onPlaybackStateChanged(playbackState: Int) {
                        val playerError = exoPlayer.playerError
                        updatePlaybackState(
                            status = playerError?.let { PlaybackStatus.Error }
                                ?: playbackState.toPlaybackStatus(),
                            isPlaying = exoPlayer.isPlaying,
                            errorMessage = playerError?.toDisplayMessage()
                        )
                    }

                    override fun onIsPlayingChanged(isPlaying: Boolean) {
                        val playerError = exoPlayer.playerError
                        updatePlaybackState(
                            status = playerError?.let { PlaybackStatus.Error }
                                ?: exoPlayer.playbackState.toPlaybackStatus(),
                            isPlaying = isPlaying,
                            errorMessage = playerError?.toDisplayMessage()
                        )
                    }

                    override fun onPlayerError(error: PlaybackException) {
                        val message = error.toDisplayMessage()
                        updatePlaybackState(
                            status = PlaybackStatus.Error,
                            isPlaying = false,
                            errorMessage = message
                        )
                        errorTextView?.text = error.toOverlayMessage()
                        errorTextView?.visibility = TextView.VISIBLE
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

        root.addView(
            PlayerView(this).apply {
                layoutParams = FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
                useController = false
                this.player = overlayPlayer
            }
        )
    }

    private fun addSnapshotView(root: FrameLayout) {
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
                URL(url).openStream().use { stream ->
                    BitmapFactory.decodeStream(stream)
                        ?: error("Snapshot response was not a supported image")
                }
            }.onSuccess { bitmap ->
                mainHandler.post {
                    imageView.setImageBitmap(bitmap)
                    updatePlaybackState(
                        status = PlaybackStatus.Ready,
                        isPlaying = false,
                        errorMessage = null
                    )
                }
            }.onFailure { error ->
                mainHandler.post {
                    val message = error.message ?: "unknown snapshot error"
                    updatePlaybackState(
                        status = PlaybackStatus.Error,
                        isPlaying = false,
                        errorMessage = message
                    )
                    errorTextView?.text = "Snapshot unavailable"
                    errorTextView?.visibility = TextView.VISIBLE
                    AppLog.error("Snapshot overlay failed: $message", error)
                }
            }
        }.start()
    }

    private fun removeOverlay() {
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
                errorMessage = errorMessage
            )
        )
    }

    private fun scheduleAutoClose() {
        autoCloseHandler.removeCallbacksAndMessages(null)
        val duration = durationSeconds ?: return
        autoCloseHandler.postDelayed({ stopSelf() }, duration * 1_000L)
    }

    companion object {
        const val ACTION_SHOW = "com.hatvpip.receiver.action.SHOW_OVERLAY"
        const val ACTION_STOP = "com.hatvpip.receiver.action.STOP_OVERLAY"
        private const val OVERLAY_WIDTH_PX = 640
        private const val OVERLAY_HEIGHT_PX = 360
        private const val OVERLAY_MARGIN_PX = 48
    }
}

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

private fun PlaybackException.toOverlayMessage(): String =
    when (errorCode) {
        PlaybackException.ERROR_CODE_DECODER_INIT_FAILED ->
            "Unsupported video stream\nTry a compatible lower-resolution or H.264 stream"
        else -> "Playback error\n$errorCodeName"
    }
