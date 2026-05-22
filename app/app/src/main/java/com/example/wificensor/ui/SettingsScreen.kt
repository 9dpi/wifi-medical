package com.example.wificensor.ui

import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.wificensor.sensing.SensingService

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val sharedPrefs = remember { context.getSharedPreferences("wifi_censor_prefs", Context.MODE_PRIVATE) }

    // --- State ---
    var driveFileName by remember { mutableStateOf(sharedPrefs.getString("drive_file_name", "wificensor_status.json") ?: "wificensor_status.json") }
    
    var telegramEnabled by remember { mutableStateOf(sharedPrefs.getBoolean("telegram_enabled", false)) }
    var telegramToken by remember { mutableStateOf(sharedPrefs.getString("telegram_token", "") ?: "") }
    var telegramChatId by remember { mutableStateOf(sharedPrefs.getString("telegram_chat_id", "") ?: "") }

    var immobilityThreshold by remember { mutableFloatStateOf(sharedPrefs.getFloat("immobility_threshold", 45f)) }
    var sensitivityMultiplier by remember { mutableFloatStateOf(sharedPrefs.getFloat("sensitivity_multiplier", 3.0f)) }

    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(scrollState)
    ) {
        // --- Header Section ---
        Surface(
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 2.dp
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Text(
                    "Cấu hình & Cài đặt",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.ExtraBold,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    "Tùy chỉnh hệ thống giám sát và thông báo",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // --- Google Drive / JSON File Sync Section ---
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Share, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(24.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Đồng bộ & Lưu trữ", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.height(12.dp))
                
                OutlinedTextField(
                    value = driveFileName,
                    onValueChange = { driveFileName = it },
                    label = { Text("Tên File JSON Trạng Thái") },
                    placeholder = { Text("wificensor_status.json") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    "File này lưu cục bộ tại thư mục External Files và được đồng bộ lên Google Drive (Google One) để Web Dashboard đọc dữ liệu.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // --- Telegram Alerts Section ---
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Notifications, null, tint = Color(0xFF3B82F6), modifier = Modifier.size(24.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("Cảnh Báo Telegram", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    }
                    Switch(
                        checked = telegramEnabled,
                        onCheckedChange = { telegramEnabled = it }
                    )
                }
                
                if (telegramEnabled) {
                    Spacer(Modifier.height(12.dp))
                    OutlinedTextField(
                        value = telegramToken,
                        onValueChange = { telegramToken = it },
                        label = { Text("Telegram Bot Token") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = telegramChatId,
                        onValueChange = { telegramChatId = it },
                        label = { Text("Telegram Chat ID") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Dùng để gửi tin nhắn thông báo té ngã hoặc không di chuyển thời gian dài tới điện thoại người thân qua Telegram.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // --- Algorithms Threshold Section ---
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("⚙️", fontSize = 20.sp)
                    Spacer(Modifier.width(8.dp))
                    Text("Cảm Biến & Ngưỡng Kích Hoạt", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.height(16.dp))
                
                Text(
                    "Thời gian bất động tối đa: ${immobilityThreshold.toInt()} phút",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium
                )
                Slider(
                    value = immobilityThreshold,
                    onValueChange = { immobilityThreshold = it },
                    valueRange = 15f..120f,
                    steps = 6,
                    modifier = Modifier.fillMaxWidth()
                )
                Text(
                    "Nếu không phát hiện bất kỳ cử động nào vượt quá thời gian này, hệ thống sẽ kích hoạt cảnh báo bất tỉnh.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    "Độ nhạy quét hiện diện: ${"%.1f".format(sensitivityMultiplier)}x",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium
                )
                Slider(
                    value = sensitivityMultiplier,
                    onValueChange = { sensitivityMultiplier = it },
                    valueRange = 1.5f..5.0f,
                    modifier = Modifier.fillMaxWidth()
                )
                Text(
                    "Hệ số nhân so với phương sai gốc. Hệ số càng thấp, độ nhạy phát hiện chuyển động nhỏ càng cao.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // --- System Recalibration Section ---
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Refresh, null, tint = Color(0xFFF59E0B), modifier = Modifier.size(24.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Hiệu chuẩn hệ thống", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.height(8.dp))
                Text(
                    "Nhấn nút dưới đây khi phòng hoàn toàn trống để thiết lập lại phương sai nền Wi-Fi (baseline variance). Việc này mất khoảng 30 giây.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(12.dp))
                Button(
                    onClick = {
                        val intent = Intent(context, SensingService::class.java).apply {
                            action = "RECALIBRATE"
                        }
                        context.startService(intent)
                        Toast.makeText(context, "🔄 Đã gửi yêu cầu hiệu chuẩn lại!", Toast.LENGTH_SHORT).show()
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFF59E0B)),
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Icon(Icons.Default.Refresh, null)
                    Spacer(Modifier.width(8.dp))
                    Text("Thiết Lập Lại Baseline")
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // --- Save Buttons ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Button(
                onClick = {
                    sharedPrefs.edit().apply {
                        putString("drive_file_name", driveFileName)
                        putBoolean("telegram_enabled", telegramEnabled)
                        putString("telegram_token", telegramToken)
                        putString("telegram_chat_id", telegramChatId)
                        putFloat("immobility_threshold", immobilityThreshold)
                        putFloat("sensitivity_multiplier", sensitivityMultiplier)
                        apply()
                    }
                    Toast.makeText(context, "💾 Đã lưu cấu hình cài đặt!", Toast.LENGTH_SHORT).show()
                },
                modifier = Modifier
                    .weight(1f)
                    .height(48.dp),
                shape = RoundedCornerShape(24.dp)
            ) {
                Icon(Icons.Default.Send, null)
                Spacer(Modifier.width(8.dp))
                Text("Lưu Cấu Hình", fontWeight = FontWeight.Bold)
            }
        }

        Spacer(modifier = Modifier.height(100.dp))
    }
}
