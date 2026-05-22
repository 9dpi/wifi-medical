/*
 * Copyright 2025 - 2026 Vu Quang Cuong
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.example.wificensor.data

import androidx.room.*
import kotlinx.coroutines.flow.Flow

// ─── Entities ──────────────────────────────────────────────────────────

@Entity(tableName = "rssi_snapshots")
data class RssiSnapshot(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val timestamp: Long,
    val bssid: String,
    val ssid: String,
    val rssi: Int,          // dBm, typically -30 to -90
    val frequency: Int,     // MHz
    val presenceLabel: String = "UNKNOWN"  // PRESENT / ABSENT / UNKNOWN
)

@Entity(tableName = "presence_events")
data class PresenceEvent(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val startTime: Long,
    val endTime: Long? = null,
    val eventType: String,          // PRESENT / ABSENT / FALL_SUSPECTED / ANOMALY
    val activity: String = "",      // WALKING / STATIONARY / SLEEPING / MOVING
    val confidence: Float = 0f,
    val notes: String = ""
)

@Entity(tableName = "alert_events")
data class AlertEvent(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val timestamp: Long,
    val level: String,              // WARN / DANGER
    val title: String,
    val message: String,
    val acknowledged: Boolean = false
)

// ─── DAOs ───────────────────────────────────────────────────────────────

@Dao
interface RssiSnapshotDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(snapshot: RssiSnapshot)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(snapshots: List<RssiSnapshot>)

    @Query("SELECT * FROM rssi_snapshots ORDER BY timestamp DESC LIMIT :limit")
    fun observeLatest(limit: Int = 200): Flow<List<RssiSnapshot>>

    @Query("SELECT * FROM rssi_snapshots WHERE timestamp > :since ORDER BY timestamp ASC")
    suspend fun getSince(since: Long): List<RssiSnapshot>

    @Query("DELETE FROM rssi_snapshots WHERE timestamp < :before")
    suspend fun deleteOlderThan(before: Long)

    @Query("SELECT AVG(rssi) FROM rssi_snapshots WHERE bssid = :bssid AND timestamp > :since")
    suspend fun avgRssiFor(bssid: String, since: Long): Float?
}

@Dao
interface PresenceEventDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(event: PresenceEvent): Long

    @Update
    suspend fun update(event: PresenceEvent)

    @Query("SELECT * FROM presence_events ORDER BY startTime DESC LIMIT :limit")
    fun observeRecent(limit: Int = 50): Flow<List<PresenceEvent>>

    @Query("SELECT * FROM presence_events WHERE startTime > :since ORDER BY startTime ASC")
    suspend fun getSince(since: Long): List<PresenceEvent>

    @Query("SELECT * FROM presence_events WHERE endTime IS NULL ORDER BY startTime DESC LIMIT 1")
    suspend fun getOpenEvent(): PresenceEvent?

    @Query("""
        SELECT SUM(COALESCE(endTime, :now) - startTime) / 60000
        FROM presence_events
        WHERE eventType = :type AND startTime > :dayStart
    """)
    suspend fun totalMinutesToday(type: String, dayStart: Long, now: Long): Long?
}

@Dao
interface AlertEventDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(alert: AlertEvent): Long

    @Query("SELECT * FROM alert_events ORDER BY timestamp DESC LIMIT 20")
    fun observeRecent(): Flow<List<AlertEvent>>

    @Query("UPDATE alert_events SET acknowledged = 1 WHERE id = :id")
    suspend fun acknowledge(id: Long)

    @Query("DELETE FROM alert_events WHERE timestamp < :before")
    suspend fun deleteOlderThan(before: Long)
}

// ─── Database ───────────────────────────────────────────────────────────

@Database(
    entities = [RssiSnapshot::class, PresenceEvent::class, AlertEvent::class],
    version = 1,
    exportSchema = false
)
abstract class WifiCensorDatabase : RoomDatabase() {
    abstract fun rssiDao(): RssiSnapshotDao
    abstract fun presenceDao(): PresenceEventDao
    abstract fun alertDao(): AlertEventDao

    companion object {
        @Volatile private var INSTANCE: WifiCensorDatabase? = null

        fun getInstance(context: android.content.Context): WifiCensorDatabase =
            INSTANCE ?: synchronized(this) {
                Room.databaseBuilder(
                    context.applicationContext,
                    WifiCensorDatabase::class.java,
                    "wificensor.db"
                ).build().also { INSTANCE = it }
            }
    }
}
