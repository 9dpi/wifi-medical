package com.example.wificensor.sensing

import android.app.*
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.example.wificensor.MainActivity
import com.example.wificensor.data.PresenceEvent
import com.example.wificensor.data.AlertEvent
import com.example.wificensor.data.WifiCensorDatabase
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

/**
 * Foreground service that:
 * 1. Keeps Wi-Fi scanning alive in the background (Android won't kill foreground services)
 * 2. Runs the PresenceEngine on each scan result
 * 3. Persists events to Room DB
 * 4. Emits live state via companion StateFlow (consumed by UI)
 * 5. Triggers anomaly alerts
 */
class SensingService : Service() {

    companion object {
        const val CHANNEL_ID    = "wificensor_sensing"
        const val NOTIF_ID      = 1001
        const val ACTION_START  = "START_SENSING"
        const val ACTION_STOP   = "STOP_SENSING"

        // Live state shared with UI (process-level singleton)
        val liveResult = MutableStateFlow<PresenceEngine.PresenceResult?>(null)
        val isRunning  = MutableStateFlow(false)
    }

    private val scope          = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private lateinit var scanner: WifiScanner
    private val presenceEngine = PresenceEngine()
    private val anomalyTracker = AnomalyTracker()
    private val db by lazy { WifiCensorDatabase.getInstance(this) }

    // Track current open event for DB lifecycle management
    private var openEventId: Long? = null
    private var lastPresence: PresenceEngine.PresenceState? = null

    // ── Lifecycle ─────────────────────────────────────────────────────

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        scanner = WifiScanner(this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> { stopSelf(); return START_NOT_STICKY }
            else        -> startForeground()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        scanner.stop()
        scope.cancel()
        isRunning.value = false
        super.onDestroy()
    }

    // ── Start Foreground ──────────────────────────────────────────────

    private fun startForeground() {
        val notification = buildNotification("🔍 Đang quan sát phòng...")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIF_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
        } else {
            startForeground(NOTIF_ID, notification)
        }

        scanner.start()
        isRunning.value = true
        observeScanResults()
        anomalyTracker.start()
    }

    // ── Observe Scan Results ──────────────────────────────────────────

    private fun observeScanResults() {
        scope.launch {
            scanner.scanResults
                .filter { it.isNotEmpty() }
                .collect { scanList ->
                    val result = presenceEngine.process(scanList)
                    liveResult.value = result

                    // Update notification
                    updateNotification(result)

                    // Persist events
                    persistPresenceEvent(result)

                    // Check anomalies
                    anomalyTracker.onResult(result) { alert ->
                        persistAlert(alert)
                    }
                }
        }
    }

    // ── Event Persistence ─────────────────────────────────────────────

    private suspend fun persistPresenceEvent(result: PresenceEngine.PresenceResult) {
        if (result.presence == PresenceEngine.PresenceState.UNKNOWN) return
        val now = System.currentTimeMillis()

        if (result.presence != lastPresence) {
            // Close previous open event
            openEventId?.let { id ->
                val open = db.presenceDao().getOpenEvent()
                open?.let { db.presenceDao().update(it.copy(endTime = now)) }
            }

            // Open new event
            val newId = db.presenceDao().insert(
                PresenceEvent(
                    startTime  = now,
                    eventType  = result.presence.name,
                    activity   = result.activity.name,
                    confidence = result.confidence,
                )
            )
            openEventId  = newId
            lastPresence = result.presence
        }
    }

    private suspend fun persistAlert(alert: AlertEvent) {
        db.alertDao().insert(alert)
        sendAlertNotification(alert)
    }

    // ── Notifications ─────────────────────────────────────────────────

    private fun updateNotification(result: PresenceEngine.PresenceResult) {
        val text = when (result.presence) {
            PresenceEngine.PresenceState.PRESENT ->
                "🟢 Có người · ${result.activity.name.lowercase().replaceFirstChar { it.uppercase() }} · ${(result.confidence * 100).toInt()}%"
            PresenceEngine.PresenceState.ABSENT  ->
                "⚪ Vắng phòng · ${(result.confidence * 100).toInt()}% chắc chắn"
            PresenceEngine.PresenceState.UNKNOWN ->
                "🔍 Đang hiệu chỉnh... ${(presenceEngine.calibrationProgress() * 100).toInt()}%"
        }
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        nm.notify(NOTIF_ID, buildNotification(text))
    }

    private fun sendAlertNotification(alert: AlertEvent) {
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val n = NotificationCompat.Builder(this, "wificensor_alerts")
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(alert.title)
            .setContentText(alert.message)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()
        nm.notify(System.currentTimeMillis().toInt(), n)
    }

    private fun buildNotification(contentText: String): Notification {
        val tapIntent = Intent(this, MainActivity::class.java)
        val pi = PendingIntent.getActivity(this, 0, tapIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        val stopIntent = Intent(this, SensingService::class.java).apply { action = ACTION_STOP }
        val stopPi = PendingIntent.getService(this, 1, stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setContentTitle("Wifi-Censor")
            .setContentText(contentText)
            .setOngoing(true)
            .setContentIntent(pi)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "Dừng", stopPi)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

            nm.createNotificationChannel(
                NotificationChannel(CHANNEL_ID, "Wifi Sensing", NotificationManager.IMPORTANCE_LOW).apply {
                    description = "Trạng thái giám sát phòng"
                    setShowBadge(false)
                }
            )
            nm.createNotificationChannel(
                NotificationChannel("wificensor_alerts", "Cảnh báo", NotificationManager.IMPORTANCE_HIGH).apply {
                    description = "Cảnh báo khẩn cấp từ Wifi-Censor"
                }
            )
        }
    }
}
