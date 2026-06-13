package com.hatvpip.receiver

import android.util.Log

object AppLog {
    private const val TAG = "HaTvPipReceiver"

    fun activityCreated(activityName: String) {
        Log.i(TAG, "event=activity_created activity=$activityName")
    }

    fun playbackStart(url: String) {
        Log.i(TAG, "event=playback_start url=$url")
    }

    fun playbackStop(reason: String) {
        Log.i(TAG, "event=playback_stop reason=$reason")
    }

    fun enterPip(trigger: String) {
        Log.i(TAG, "event=enter_pip trigger=$trigger")
    }

    fun exitPip() {
        Log.i(TAG, "event=exit_pip")
    }

    fun error(message: String, throwable: Throwable? = null) {
        Log.e(TAG, "event=error message=$message", throwable)
    }
}
