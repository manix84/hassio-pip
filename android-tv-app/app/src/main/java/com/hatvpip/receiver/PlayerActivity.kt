package com.hatvpip.receiver

import android.app.PictureInPictureParams
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.os.Bundle
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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        AppLog.activityCreated("PlayerActivity")
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        initializePlayer()

        setContent {
            HaTvTheme {
                PlayerScreen(
                    player = player,
                    playbackState = viewModel.playbackState,
                    isInPip = viewModel.isInPip,
                    onEnterPip = { enterPip(trigger = "button") }
                )
            }
        }
    }

    override fun onResume() {
        super.onResume()
        initializePlayer()
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
        releasePlayer()
    }

    override fun onUserLeaveHint() {
        super.onUserLeaveHint()
        if (!isFinishing && !viewModel.isInPip) {
            enterPip(trigger = "home")
        }
    }

    override fun onPictureInPictureModeChanged(
        isInPictureInPictureMode: Boolean,
        newConfig: Configuration
    ) {
        super.onPictureInPictureModeChanged(isInPictureInPictureMode, newConfig)
        viewModel.setPictureInPicture(isInPictureInPictureMode)
        if (isInPictureInPictureMode) {
            AppLog.enterPip(trigger = "system")
        } else {
            AppLog.exitPip()
        }
    }

    private fun initializePlayer() {
        if (player != null) return

        player = ExoPlayer.Builder(this).build().also { exoPlayer ->
            exoPlayer.addListener(
                object : Player.Listener {
                    override fun onPlaybackStateChanged(playbackStateValue: Int) {
                        viewModel.setPlaybackStatus(
                            status = playbackStateValue.toPlaybackStatus(),
                            isPlaying = exoPlayer.isPlaying
                        )
                    }

                    override fun onIsPlayingChanged(isPlaying: Boolean) {
                        viewModel.setIsPlaying(isPlaying)
                    }

                    override fun onPlayerError(error: PlaybackException) {
                        viewModel.setPlaybackError(error.errorCodeName)
                        AppLog.error("Playback failed: ${error.errorCodeName}", error)
                    }
                }
            )
            exoPlayer.setMediaItem(MediaItem.fromUri(TEST_STREAM_URL))
            exoPlayer.repeatMode = Player.REPEAT_MODE_ONE
            exoPlayer.playWhenReady = true
            exoPlayer.prepare()
            AppLog.playbackStart(TEST_STREAM_URL)
        }
    }

    private fun releasePlayer() {
        player?.release()
        player = null
        AppLog.playbackStop(reason = "player_released")
    }

    private fun enterPip(trigger: String) {
        if (!packageManager.hasSystemFeature(PackageManager.FEATURE_PICTURE_IN_PICTURE)) {
            AppLog.error("Picture-in-Picture is not supported on this device")
            return
        }

        val params = PictureInPictureParams.Builder()
            .setAspectRatio(Rational(16, 9))
            .build()

        setPictureInPictureParams(params)
        val entered = enterPictureInPictureMode(params)
        if (entered) {
            AppLog.enterPip(trigger = trigger)
        } else {
            AppLog.error("System rejected Picture-in-Picture request")
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

    companion object {
        const val TEST_STREAM_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    }
}

@Composable
private fun PlayerScreen(
    player: Player?,
    playbackState: PlayerPlaybackState,
    isInPip: Boolean,
    onEnterPip: () -> Unit
) {
    val pipButtonFocusRequester = remember { FocusRequester() }

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
                        text = "Playback state: ${playbackState.displayText}",
                        color = Color.White,
                        fontSize = 18.sp
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                        Button(
                            modifier = Modifier.focusRequester(pipButtonFocusRequester),
                            onClick = onEnterPip
                        ) {
                            Text(text = "Enter PiP")
                        }
                    }
                }
            }
        }
    }
}
