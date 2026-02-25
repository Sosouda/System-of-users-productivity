package api

import android.content.Context
import android.util.Log
import data.MainDb
import data.TaskEntity
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

object SyncManager {
    private const val DEFAULT_SYNC_TIME = "2000-01-01T00:00:00Z"

    private fun mapPriorityForServer(localPriority: String): String {
        val allowed = listOf("Casual", "Low", "Mid", "High", "Extreme")
        if (allowed.contains(localPriority)) return localPriority
        return when (localPriority) {
            "1" -> "Casual"
            "2" -> "Low"
            "3" -> "Mid"
            "4" -> "High"
            "5" -> "Extreme"
            else -> "Mid"
        }
    }

    private fun parseServerDate(dateStr: String?): OffsetDateTime? {
        if (dateStr.isNullOrBlank()) return null
        return try {
            OffsetDateTime.parse(dateStr)
        } catch (e: Exception) {
            try {
                LocalDateTime.parse(dateStr).atOffset(ZoneOffset.UTC)
            } catch (e2: Exception) {
                Log.e("SYNC_ERROR", "Не удалось распарсить дату: $dateStr")
                null
            }
        }
    }

    suspend fun runSync(context: Context): Pair<Boolean, String> {
        val database = MainDb.createDatabase(context)
        val taskDao = database.taskDao()
        val apiService = RetrofitClient.instance

        val token = AuthManager.getValidToken(context) ?: return false to "Нет авторизации"
        val bearerToken = "Bearer $token"

        try {
            Log.d("SYNC_DEBUG", "--- Начало синхронизации ---")

            val lastSyncStr = SyncSettings.getLastSync(context).ifBlank { DEFAULT_SYNC_TIME }
            val lastSyncDt = parseServerDate(lastSyncStr) ?: OffsetDateTime.MIN
            Log.d("SYNC_DEBUG", "Метка последней синхронизации: $lastSyncDt")

            val localUpdates = taskDao.getTasksUpdatedAfter(lastSyncDt)
            if (localUpdates.isNotEmpty()) {
                val dtoList = localUpdates.map { task ->
                    TaskDto(
                        id = task.id,
                        title = task.title,
                        description = task.description,
                        task_type_id = task.taskTypeId,
                        personal_priority = task.personalPriority,
                        influence = task.influence,
                        status = task.status,
                        deadline = task.deadline?.toString(),
                        created_at = task.createdAt.toString(),
                        updated_at = task.updatedAt.toString(),
                        final_priority = mapPriorityForServer(task.finalPriority)
                    )
                }

                val pushResp = apiService.pushTasks(bearerToken, SyncPushRequest(dtoList))
                if (!pushResp.isSuccessful) {
                    val error = pushResp.errorBody()?.string()
                    Log.e("SYNC_ERROR", "Ошибка PUSH: $error")
                    return false to "Ошибка PUSH на сервере"
                }
                Log.d("SYNC_DEBUG", "PUSH успешно завершен")
            }

            val pullResp = apiService.pullTasks(bearerToken, lastSyncStr)
            if (pullResp.isSuccessful && pullResp.body() != null) {
                val data = pullResp.body()!!
                Log.d("SYNC_DEBUG", "Получено от сервера: ${data.tasks.size} задач")

                for (rTask in data.tasks) {
                    val local = taskDao.getTaskById(rTask.id)
                    val rUpdated = parseServerDate(rTask.updated_at) ?: OffsetDateTime.MIN

                    if (local == null || rUpdated.isAfter(local.updatedAt)) {
                        taskDao.insertOrUpdate(rTask.toEntity())
                    }
                }

                if (!data.server_time.isNullOrBlank()) {
                    SyncSettings.saveLastSync(context, data.server_time)
                    Log.d("SYNC_DEBUG", "✅ Новая метка времени: ${data.server_time}")
                }
            }

            return true to "Синхронизация завершена успешно"

        } catch (e: Exception) {
            Log.e("SYNC_FATAL", "Ошибка: ${e.message}", e)
            return false to (e.message ?: "Неизвестная ошибка")
        }
    }

    private fun TaskDto.toEntity(): TaskEntity {
        return TaskEntity(
            id = this.id,
            title = this.title,
            description = this.description,
            taskTypeId = this.task_type_id,
            personalPriority = this.personal_priority,
            influence = this.influence,
            status = this.status,
            deadline = parseServerDate(this.deadline),
            createdAt = parseServerDate(this.created_at) ?: OffsetDateTime.now(),
            updatedAt = parseServerDate(this.updated_at) ?: OffsetDateTime.now(),
            finalPriority = this.final_priority
        )
    }
}