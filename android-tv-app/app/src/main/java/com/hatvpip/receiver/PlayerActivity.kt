package com.hatvpip.receiver

import android.app.PictureInPictureParams
import android.content.Context
import android.content.Intent
import android.content.res.Configuration
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Rational
import android.view.ViewGroup
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView

class PlayerActivity : ComponentActivity() {
    private val viewModel: PlayerViewModel by viewModels()
    private var player: ExoPlayer? = null
    private lateinit var compatibility: DeviceCompatibility
    private var command: ShowCommand = ShowCommand.testVideo()
    private var currentDisplayMode: ReceiverPlaybackMode = ReceiverPlaybackMode.Idle
    private val autoCloseHandler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        AppLog.activityCreated("PlayerActivity")
        if (intent.action == ACTION_CLOSE) {
            ReceiverRuntimeState.markIdle()
            finish()
            return
        }

        compatibility = DeviceCompatibilityEvaluator.from(this)
        command = intent.toShowCommand()
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        initializePlayer()
        updatePictureInPictureParams()
        scheduleAutoClose()

        setContent {
            HaTvTheme {
                PlayerScreen(
                    player = player,
                    playbackState = viewModel.playbackState,
                    compatibility = compatibility,
                    isInPip = viewModel.isInPip,
                    onEnterPip = { enterPip(trigger = "button") }
                )
            }
        }

        if (command.enterPip) {
            autoCloseHandler.postDelayed({ enterPip(trigger = "remote") }, REMOTE_PIP_DELAY_MS)
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        if (intent.action == ACTION_CLOSE) {
            closePlayer(reason = "remote_close")
            return
        }

        setIntent(intent)
        command = intent.toShowCommand()
        player?.setMediaItem(MediaItem.fromUri(command.url))
        player?.prepare()
        player?.play()
        AppLog.playbackStart(command.url)
        scheduleAutoClose()
        if (command.enterPip) {
            autoCloseHandler.postDelayed({ enterPip(trigger = "remote") }, REMOTE_PIP_DELAY_MS)
        }
    }

    override fun onResume() {
        super.onResume()
        initializePlayer()
        updatePictureInPictureParams()
        player?.play()
    }

    override fun onStop() {
        super.onStop()
        if (!viewModel.isInPip) {
            player?.pause()
            AppLog.playbackStop(reason = "activity_stopped")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        autoCloseHandler.removeCallbacksAndMessages(null)
        releasePlayer()
    }

    override fun onUserLeaveHint() {
        super.onUserLeaveHint()
        if (!isFinishing && !viewModel.isInPip) {
            if (compatibility.recommendedMode == ReceiverDisplayMode.OverlayFallback) {
                enterPip(trigger = "home")
            } else if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
                enterPip(trigger = "home")
            } else {
                updatePictureInPictureParams()
            }
        }
    }

    override fun onPictureInPictureModeChanged(
        isInPictureInPictureMode: Boolean,
        newConfig: Configuration
    ) {
        super.onPictureInPictureModeChanged(isInPictureInPictureMode, newConfig)
        viewModel.setPictureInPicture(isInPictureInPictureMode)
        if (isInPictureInPictureMode) {
            updateRuntimeState(mode = ReceiverPlaybackMode.NativePictureInPicture)
            AppLog.enterPip(trigger = "system")
        } else {
            updateRuntimeState(mode = ReceiverPlaybackMode.FullScreen)
            AppLog.exitPip()
        }
    }

    private fun initializePlayer() {
        if (player != null) return

        player = buildReceiverPlayer(this).also { exoPlayer ->
            exoPlayer.addListener(
                object : Player.Listener {
                    override fun onPlaybackStateChanged(playbackStateValue: Int) {
                        viewModel.setPlaybackStatus(
                            status = playbackStateValue.toPlaybackStatus(),
                            isPlaying = exoPlayer.isPlaying
                        )
                        updateRuntimeState(mode = currentDisplayMode)
                    }

                    override fun onIsPlayingChanged(isPlaying: Boolean) {
                        viewModel.setIsPlaying(isPlaying)
                        updateRuntimeState(mode = currentDisplayMode)
                    }

                    override fun onPlayerError(error: PlaybackException) {
                        viewModel.setPlaybackError(error.errorCodeName)
                        updateRuntimeState(mode = currentDisplayMode)
                        AppLog.error("Playback failed: ${error.errorCodeName}", error)
                    }
                }
            )
            exoPlayer.setMediaItem(MediaItem.fromUri(command.url))
            exoPlayer.repeatMode = Player.REPEAT_MODE_ONE
            exoPlayer.playWhenReady = true
            exoPlayer.prepare()
            AppLog.playbackStart(command.url)
            updateRuntimeState(mode = ReceiverPlaybackMode.FullScreen)
        }
    }

    private fun releasePlayer() {
        player?.release()
        player = null
        if (currentDisplayMode != ReceiverPlaybackMode.Overlay) {
            ReceiverRuntimeState.markIdle()
        }
        AppLog.playbackStop(reason = "player_released")
    }

    private fun updatePictureInPictureParams(): PictureInPictureParams {
        val paramsBuilder = PictureInPictureParams.Builder()
            .setAspectRatio(Rational(16, 9))

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            paramsBuilder
                .setTitle(getString(R.string.app_name))
                .setSubtitle(getString(R.string.pip_subtitle_camera_preview))
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            paramsBuilder.setAutoEnterEnabled(true)
        }

        val params = paramsBuilder.build()
        setPictureInPictureParams(params)
        return params
    }

    private fun enterPip(trigger: String) {
        if (compatibility.recommendedMode == ReceiverDisplayMode.OverlayFallback) {
            enterOverlayFallback()
            return
        }

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            val message = getString(R.string.error_pip_requires_android_o)
            viewModel.setPlaybackError(message)
            AppLog.error(message)
            return
        }

        try {
            val params = updatePictureInPictureParams()
            val entered = enterPictureInPictureMode(params)
            if (entered) {
                AppLog.enterPip(trigger = trigger)
            } else {
                val message = getString(R.string.error_pip_rejected)
                viewModel.setPlaybackError(message)
                AppLog.error(message)
            }
        } catch (error: IllegalStateException) {
            val message = getString(
                R.string.error_pip_request_failed,
                error.message ?: getString(R.string.error_unknown_reason)
            )
            viewModel.setPlaybackError(message)
            AppLog.error(message, error)
        } catch (error: IllegalArgumentException) {
            val message = getString(
                R.string.error_pip_params_rejected,
                error.message ?: getString(R.string.error_unknown_reason)
            )
            viewModel.setPlaybackError(message)
            AppLog.error(message, error)
        }
    }

    private fun enterOverlayFallback() {
        runCatching {
            startService(
                Intent(this, OverlayPlayerService::class.java)
                    .setAction(OverlayPlayerService.ACTION_SHOW)
                    .putExtra(EXTRA_TITLE, command.title)
                    .putExtra(EXTRA_URL, command.url)
                    .putExtra(EXTRA_STREAM_TYPE, command.streamType.wireName)
                    .putExtra(EXTRA_PREVIEW_URL, command.previewUrl)
                    .putExtra(EXTRA_SHOW_NOTIFICATION, command.showNotification)
                    .putExtra(EXTRA_MESSAGE, command.message)
                    .putExtra(EXTRA_POSITION, command.style.position.wireName)
                    .putExtra(EXTRA_TITLE_COLOR, command.style.titleColor)
                    .putExtra(EXTRA_TITLE_SIZE, command.style.titleSize)
                    .putExtra(EXTRA_MESSAGE_COLOR, command.style.messageColor)
                    .putExtra(EXTRA_MESSAGE_SIZE, command.style.messageSize)
                    .putExtra(EXTRA_BACKGROUND_COLOR, command.style.backgroundColor)
                    .apply {
                        command.style.width?.let { putExtra(EXTRA_WIDTH, it) }
                        command.style.height?.let { putExtra(EXTRA_HEIGHT, it) }
                        command.durationSeconds?.let { putExtra(EXTRA_DURATION_SECONDS, it) }
                    }
            )
            player?.pause()
            updateRuntimeState(mode = ReceiverPlaybackMode.Overlay)
            AppLog.playbackStop(reason = "overlay_fallback_started")
            moveTaskToBack(true)
        }.onFailure { error ->
            val message = getString(
                R.string.error_overlay_fallback_failed,
                error.message ?: getString(R.string.error_unknown_reason)
            )
            viewModel.setPlaybackError(message)
            AppLog.error(message, error)
        }
    }

    private fun scheduleAutoClose() {
        autoCloseHandler.removeCallbacksAndMessages(null)
        val durationSeconds = command.durationSeconds ?: return
        autoCloseHandler.postDelayed(
            { closePlayer(reason = "duration_elapsed") },
            durationSeconds * 1_000L
        )
    }

    private fun closePlayer(reason: String) {
        stopService(
            Intent(this, OverlayPlayerService::class.java)
                .setAction(OverlayPlayerService.ACTION_STOP)
        )
        AppLog.playbackStop(reason = reason)
        finishAndRemoveTask()
    }

    private fun updateRuntimeState(mode: ReceiverPlaybackMode) {
        currentDisplayMode = mode
        val playbackState = viewModel.playbackState
        ReceiverRuntimeState.update(
            ReceiverPlaybackSnapshot(
                status = playbackState.status,
                isPlaying = playbackState.isPlaying,
                mode = mode,
                title = command.title,
                url = command.url,
                previewUrl = command.previewUrl,
                streamType = command.streamType.wireName,
                errorMessage = playbackState.errorMessage
            )
        )
    }

    private fun Int.toPlaybackStatus(): PlaybackStatus =
        when (this) {
            Player.STATE_BUFFERING -> PlaybackStatus.Buffering
            Player.STATE_READY -> PlaybackStatus.Ready
            Player.STATE_ENDED -> PlaybackStatus.Ended
            Player.STATE_IDLE -> PlaybackStatus.Idle
            else -> PlaybackStatus.Idle
        }

    companion object {
        const val ACTION_CLOSE = "com.hatvpip.receiver.action.CLOSE_PLAYER"
        const val EXTRA_TITLE = "com.hatvpip.receiver.extra.TITLE"
        const val EXTRA_URL = "com.hatvpip.receiver.extra.URL"
        const val EXTRA_STREAM_TYPE = "com.hatvpip.receiver.extra.STREAM_TYPE"
        const val EXTRA_PREVIEW_URL = "com.hatvpip.receiver.extra.PREVIEW_URL"
        const val EXTRA_SHOW_NOTIFICATION = "com.hatvpip.receiver.extra.SHOW_NOTIFICATION"
        const val EXTRA_MESSAGE = "com.hatvpip.receiver.extra.MESSAGE"
        const val EXTRA_POSITION = "com.hatvpip.receiver.extra.POSITION"
        const val EXTRA_TITLE_COLOR = "com.hatvpip.receiver.extra.TITLE_COLOR"
        const val EXTRA_TITLE_SIZE = "com.hatvpip.receiver.extra.TITLE_SIZE"
        const val EXTRA_MESSAGE_COLOR = "com.hatvpip.receiver.extra.MESSAGE_COLOR"
        const val EXTRA_MESSAGE_SIZE = "com.hatvpip.receiver.extra.MESSAGE_SIZE"
        const val EXTRA_BACKGROUND_COLOR = "com.hatvpip.receiver.extra.BACKGROUND_COLOR"
        const val EXTRA_WIDTH = "com.hatvpip.receiver.extra.WIDTH"
        const val EXTRA_HEIGHT = "com.hatvpip.receiver.extra.HEIGHT"
        const val EXTRA_DURATION_SECONDS = "com.hatvpip.receiver.extra.DURATION_SECONDS"
        const val EXTRA_ENTER_PIP = "com.hatvpip.receiver.extra.ENTER_PIP"
        const val TEST_STREAM_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
        private const val REMOTE_PIP_DELAY_MS = 750L

        fun createShowIntent(context: Context, command: ShowCommand): Intent =
            Intent(context, PlayerActivity::class.java).apply {
                putExtra(EXTRA_TITLE, command.title)
                putExtra(EXTRA_URL, command.url)
                putExtra(EXTRA_STREAM_TYPE, command.streamType.wireName)
                putExtra(EXTRA_PREVIEW_URL, command.previewUrl)
                putExtra(EXTRA_SHOW_NOTIFICATION, command.showNotification)
                putExtra(EXTRA_MESSAGE, command.message)
                putExtra(EXTRA_POSITION, command.style.position.wireName)
                putExtra(EXTRA_TITLE_COLOR, command.style.titleColor)
                putExtra(EXTRA_TITLE_SIZE, command.style.titleSize)
                putExtra(EXTRA_MESSAGE_COLOR, command.style.messageColor)
                putExtra(EXTRA_MESSAGE_SIZE, command.style.messageSize)
                putExtra(EXTRA_BACKGROUND_COLOR, command.style.backgroundColor)
                command.style.width?.let { putExtra(EXTRA_WIDTH, it) }
                command.style.height?.let { putExtra(EXTRA_HEIGHT, it) }
                command.durationSeconds?.let { putExtra(EXTRA_DURATION_SECONDS, it) }
                putExtra(EXTRA_ENTER_PIP, command.enterPip)
            }
    }
}

private fun Intent.toShowCommand(): ShowCommand =
    ShowCommand(
        title = getStringExtra(PlayerActivity.EXTRA_TITLE) ?: "Test Video",
        url = getStringExtra(PlayerActivity.EXTRA_URL) ?: PlayerActivity.TEST_STREAM_URL,
        streamType = when (getStringExtra(PlayerActivity.EXTRA_STREAM_TYPE)) {
            StreamType.Mjpeg.wireName -> StreamType.Mjpeg
            StreamType.Snapshot.wireName -> StreamType.Snapshot
            StreamType.Notification.wireName -> StreamType.Notification
            else -> StreamType.Hls
        },
        previewUrl = getStringExtra(PlayerActivity.EXTRA_PREVIEW_URL),
        showNotification = getBooleanExtra(PlayerActivity.EXTRA_SHOW_NOTIFICATION, false),
        message = getStringExtra(PlayerActivity.EXTRA_MESSAGE),
        style = NotificationStyle(
            position = NotificationPosition.fromWire(
                getStringExtra(PlayerActivity.EXTRA_POSITION) ?: NotificationPosition.TopRight.wireName
            ),
            titleColor = getStringExtra(PlayerActivity.EXTRA_TITLE_COLOR) ?: "#50BFF2",
            titleSize = getIntExtra(PlayerActivity.EXTRA_TITLE_SIZE, 24).coerceIn(10, 48),
            messageColor = getStringExtra(PlayerActivity.EXTRA_MESSAGE_COLOR) ?: "#fbf5f5",
            messageSize = getIntExtra(PlayerActivity.EXTRA_MESSAGE_SIZE, 18).coerceIn(10, 40),
            backgroundColor = getStringExtra(PlayerActivity.EXTRA_BACKGROUND_COLOR) ?: "#B30F0E0E",
            width = if (hasExtra(PlayerActivity.EXTRA_WIDTH)) {
                getIntExtra(PlayerActivity.EXTRA_WIDTH, 0).takeIf { it > 0 }
            } else {
                null
            },
            height = if (hasExtra(PlayerActivity.EXTRA_HEIGHT)) {
                getIntExtra(PlayerActivity.EXTRA_HEIGHT, 0).takeIf { it > 0 }
            } else {
                null
            }
        ),
        durationSeconds = if (hasExtra(PlayerActivity.EXTRA_DURATION_SECONDS)) {
            getIntExtra(PlayerActivity.EXTRA_DURATION_SECONDS, 0).takeIf { it > 0 }
        } else {
            null
        },
        enterPip = getBooleanExtra(PlayerActivity.EXTRA_ENTER_PIP, false)
    )

@Composable
private fun PlayerScreen(
    player: Player?,
    playbackState: PlayerPlaybackState,
    compatibility: DeviceCompatibility,
    isInPip: Boolean,
    onEnterPip: () -> Unit
) {
    val pipButtonFocusRequester = remember { FocusRequester() }
    val displayActionLabel = when (compatibility.recommendedMode) {
        ReceiverDisplayMode.NativePictureInPicture -> stringResource(R.string.action_enter_pip)
        ReceiverDisplayMode.OverlayFallback -> stringResource(R.string.action_show_overlay)
        ReceiverDisplayMode.FullScreenFallback -> stringResource(R.string.action_try_pip)
    }

    LaunchedEffect(Unit) {
        pipButtonFocusRequester.requestFocus()
    }

    Surface(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
        color = Color.Black
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { context ->
                    PlayerView(context).apply {
                        layoutParams = ViewGroup.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT
                        )
                        // Android TV D-pad focus can be trapped by Media3's built-in controller.
                        // Phase 1 keeps playback in Media3 and exposes TV-friendly controls in Compose.
                        useController = false
                        isFocusable = false
                        isFocusableInTouchMode = false
                        descendantFocusability = ViewGroup.FOCUS_BLOCK_DESCENDANTS
                        this.player = player
                    }
                },
                update = { playerView ->
                    playerView.player = player
                    playerView.useController = false
                }
            )

            if (!isInPip) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .align(Alignment.BottomCenter)
                        .background(Color(0xB0000000))
                        .padding(horizontal = 32.dp, vertical = 20.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = playbackState.localizedDisplayText(),
                        color = Color.White,
                        fontSize = 18.sp
                    )
                    Text(
                        text = compatibility.localizedStatusText(),
                        color = Color.White,
                        fontSize = 16.sp
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                        Button(
                            modifier = Modifier.focusRequester(pipButtonFocusRequester),
                            onClick = onEnterPip
                        ) {
                            Text(text = displayActionLabel)
                        }
                    }
                }
            }
        }
    }
}
