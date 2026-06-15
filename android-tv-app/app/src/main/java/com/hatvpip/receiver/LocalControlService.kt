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

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIFICATION_ID, buildNotification())
        discoveryAdvertiser = DiscoveryAdvertiser(applicationContext)
        server = LocalControlServer(
            context = applicationContext,
            onShow = ::showPlayer,
            onClose = ::closePlayer,
            onStarted = { port ->
                discoveryAdvertiser?.start(port)
            }
        ).also { it.start() }
    }

    override fun onDestroy() {
        discoveryAdvertiser?.stop()
        discoveryAdvertiser = null
        server?.stop()
        server = null
        super.onDestroy()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification() =
        NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle("HA TV PiP Receiver")
            .setContentText("Local control endpoint running on port ${LocalControlServer.DEFAULT_PORT}")
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
                        "Local Control",
                        NotificationManager.IMPORTANCE_LOW
                    )
                    getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
                }
            }
            .build()

    private fun showPlayer(command: ShowCommand) {
        val compatibility = DeviceCompatibilityEvaluator.from(this)
        if (command.enterPip && compatibility.recommendedMode == ReceiverDisplayMode.OverlayFallback) {
            startService(
                Intent(this, OverlayPlayerService::class.java)
                    .setAction(OverlayPlayerService.ACTION_SHOW)
                    .putExtra(PlayerActivity.EXTRA_TITLE, command.title)
                    .putExtra(PlayerActivity.EXTRA_URL, command.url)
                    .apply {
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

    companion object {
        private const val NOTIFICATION_ID = 1001
        private const val NOTIFICATION_CHANNEL_ID = "local_control"
    }
}
