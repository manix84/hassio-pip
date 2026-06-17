package com.hatvpip.receiver

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

class LocalControlService : Service() {
    private var server: LocalControlServer? = null
    private var discoveryAdvertiser: DiscoveryAdvertiser? = null
    private var remoteReceiverClient: RemoteReceiverClient? = null

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIFICATION_ID, buildNotification())
        discoveryAdvertiser = DiscoveryAdvertiser(applicationContext)
        remoteReceiverClient = RemoteReceiverClient(
            context = applicationContext,
            onShow = ::showPlayer
        ).also { it.reconnect() }
        server = LocalControlServer(
            context = applicationContext,
            onShow = ::showPlayer,
            onClose = ::closePlayer,
            onOpenManagement = ::openManagement,
            onRemoteSettingsChanged = ::refreshRemoteSettings,
            onPairingChanged = ::refreshDiscovery,
            onStarted = { port ->
                discoveryAdvertiser?.start(port)
            }
        ).also { it.start() }
    }

    override fun onDestroy() {
        remoteReceiverClient?.disconnect()
        remoteReceiverClient = null
        discoveryAdvertiser?.stop()
        discoveryAdvertiser = null
        server?.stop()
        server = null
        super.onDestroy()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_PAIRING_CHANGED) {
            refreshDiscovery()
            remoteReceiverClient?.reconnect()
        }
        if (intent?.action == ACTION_REMOTE_SETTINGS_CHANGED) {
            remoteReceiverClient?.reconnect()
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification() =
        NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_stat_ha_tv_pip)
            .setContentTitle(getString(R.string.notification_title))
            .setContentText(
                getString(
                    R.string.notification_local_control_running,
                    LocalControlServer.DEFAULT_PORT
                )
            )
            .setOngoing(true)
            .setContentIntent(
                PendingIntent.getActivity(
                    this,
                    0,
                    Intent(this, MainActivity::class.java),
                    PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
                )
            )
            .also {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    val channel = NotificationChannel(
                        NOTIFICATION_CHANNEL_ID,
                        getString(R.string.notification_channel_local_control),
                        NotificationManager.IMPORTANCE_LOW
                    )
                    getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
                }
            }
            .build()

    private fun showPlayer(command: ShowCommand) {
        val compatibility = DeviceCompatibilityEvaluator.from(this)
        if (
            command.streamType == StreamType.Notification ||
            command.streamType == StreamType.Mjpeg ||
            command.streamType == StreamType.Snapshot ||
            (command.enterPip && compatibility.recommendedMode == ReceiverDisplayMode.OverlayFallback)
        ) {
            startService(
                Intent(this, OverlayPlayerService::class.java)
                    .setAction(OverlayPlayerService.ACTION_SHOW)
                    .putExtra(PlayerActivity.EXTRA_TITLE, command.title)
                    .putExtra(PlayerActivity.EXTRA_URL, command.url)
                    .putExtra(PlayerActivity.EXTRA_STREAM_TYPE, command.streamType.wireName)
                    .putExtra(PlayerActivity.EXTRA_PREVIEW_URL, command.previewUrl)
                    .putExtra(PlayerActivity.EXTRA_FALLBACK_URL, command.fallbackUrl)
                    .putExtra(PlayerActivity.EXTRA_FALLBACK_STREAM_TYPE, command.fallbackStreamType?.wireName)
                    .putExtra(PlayerActivity.EXTRA_SHOW_NOTIFICATION, command.showNotification)
                    .putExtra(PlayerActivity.EXTRA_MESSAGE, command.message)
                    .putExtra(PlayerActivity.EXTRA_POSITION, command.style.position.wireName)
                    .putExtra(PlayerActivity.EXTRA_TITLE_COLOR, command.style.titleColor)
                    .putExtra(PlayerActivity.EXTRA_TITLE_SIZE, command.style.titleSize)
                    .putExtra(PlayerActivity.EXTRA_MESSAGE_COLOR, command.style.messageColor)
                    .putExtra(PlayerActivity.EXTRA_MESSAGE_SIZE, command.style.messageSize)
                    .putExtra(PlayerActivity.EXTRA_BACKGROUND_COLOR, command.style.backgroundColor)
                    .apply {
                        command.style.width?.let { putExtra(PlayerActivity.EXTRA_WIDTH, it) }
                        command.style.height?.let { putExtra(PlayerActivity.EXTRA_HEIGHT, it) }
                        command.durationSeconds?.let {
                            putExtra(PlayerActivity.EXTRA_DURATION_SECONDS, it)
                        }
                    }
            )
            return
        }

        val intent = PlayerActivity.createShowIntent(
            context = this,
            command = command
        ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)

        startActivity(intent)
    }

    private fun closePlayer() {
        val playback = ReceiverRuntimeState.snapshot()
        stopService(
            Intent(this, OverlayPlayerService::class.java)
                .setAction(OverlayPlayerService.ACTION_STOP)
        )

        if (playback.mode == ReceiverPlaybackMode.Idle || playback.mode == ReceiverPlaybackMode.Overlay) {
            if (playback.mode == ReceiverPlaybackMode.Idle) {
                ReceiverRuntimeState.markIdle()
            }
            return
        }

        startActivity(
            Intent(this, PlayerActivity::class.java)
                .setAction(PlayerActivity.ACTION_CLOSE)
                .addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK or
                        Intent.FLAG_ACTIVITY_SINGLE_TOP or
                        Intent.FLAG_ACTIVITY_CLEAR_TOP
                )
        )
    }

    private fun refreshDiscovery() {
        discoveryAdvertiser?.refresh()
    }

    private fun openManagement() {
        startActivity(
            Intent(this, MainActivity::class.java)
                .addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK or
                        Intent.FLAG_ACTIVITY_SINGLE_TOP or
                        Intent.FLAG_ACTIVITY_CLEAR_TOP
                )
        )
    }

    private fun refreshRemoteSettings() {
        remoteReceiverClient?.reconnect()
    }

    companion object {
        const val ACTION_PAIRING_CHANGED = "com.hatvpip.receiver.PAIRING_CHANGED"
        const val ACTION_REMOTE_SETTINGS_CHANGED = "com.hatvpip.receiver.REMOTE_SETTINGS_CHANGED"
        private const val NOTIFICATION_ID = 1001
        private const val NOTIFICATION_CHANNEL_ID = "local_control"
    }
}
