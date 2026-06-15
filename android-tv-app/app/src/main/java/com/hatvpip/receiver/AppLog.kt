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

    fun controlServerStarted(port: Int) {
        Log.i(TAG, "event=control_server_started port=$port")
    }

    fun controlServerStopped() {
        Log.i(TAG, "event=control_server_stopped")
    }

    fun controlRequest(method: String, path: String, status: Int) {
        Log.i(TAG, "event=control_request method=$method path=$path status=$status")
    }

    fun discoveryRegistered(serviceName: String, serviceType: String, port: Int) {
        Log.i(TAG, "event=discovery_registered serviceName=$serviceName serviceType=$serviceType port=$port")
    }

    fun discoveryStopped(serviceName: String) {
        Log.i(TAG, "event=discovery_stopped serviceName=$serviceName")
    }

    fun discoveryFailed(serviceName: String, message: String) {
        Log.w(TAG, "event=discovery_failed serviceName=$serviceName message=$message")
    }

    fun error(message: String, throwable: Throwable? = null) {
        Log.e(TAG, "event=error message=$message", throwable)
    }
}
