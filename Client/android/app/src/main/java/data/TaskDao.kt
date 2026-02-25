package data

import androidx.room.*
import kotlinx.coroutines.flow.Flow
import java.time.LocalDate
import java.time.OffsetDateTime

@Dao
interface TaskDao {

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertTaskType(type: TaskTypeEntity)

    @Query("SELECT id FROM task_types WHERE name = :name LIMIT 1")
    suspend fun getTypeIdByName(name: String): Int

    @Query("SELECT id FROM task_types WHERE name = :name LIMIT 1")
    suspend fun getTaskTypeIdByName(name: String): Int?

    @Query("SELECT name FROM task_types WHERE id = :id")
    suspend fun getTaskTypeNameById(id: Int): String?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTask(task: TaskEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(task: TaskEntity)

    @Query("SELECT * FROM tasks WHERE id = :id LIMIT 1")
    suspend fun getTaskById(id: String): TaskEntity?

    @Query("SELECT * FROM tasks WHERE title = :title LIMIT 1")
    suspend fun getTaskByTitle(title: String): TaskEntity?

    @Query("SELECT * FROM tasks WHERE title = :name LIMIT 1")
    suspend fun selectTaskForEdit(name: String): TaskEntity?

    @Query("SELECT * FROM tasks WHERE updated_at > :lastSync")
    suspend fun getTasksUpdatedAfter(lastSync: OffsetDateTime): List<TaskEntity>

    @Query("SELECT COUNT(*) FROM tasks")
    suspend fun getTasksCount(): Int

    @Query("""
        UPDATE tasks 
        SET deadline = :deadline, status = :status, personal_priority = :priority, 
            final_priority = :priority, task_type_id = :taskTypeId, updated_at = :updatedAt 
        WHERE title = :title
    """)
    suspend fun updateTaskProperties(
        title: String, deadline: OffsetDateTime?, status: String,
        priority: Int, taskTypeId: Int, updatedAt: OffsetDateTime
    )

    @Query("""
        UPDATE tasks SET status = 'Overdue' 
        WHERE deadline < :now AND status != 'completed' AND status != 'Overdue'
    """)
    suspend fun updateTasksStatus(now: OffsetDateTime)

    @Query("SELECT final_priority AS label, CAST(COUNT(*) AS FLOAT) AS value FROM tasks GROUP BY final_priority")
    suspend fun selectPriorityCounts(): List<ChartData>

    @Query("SELECT status AS label, CAST(COUNT(*) AS FLOAT) AS value FROM tasks GROUP BY status")
    suspend fun selectAllTasks(): List<ChartData>

    @Query("""
        SELECT tt.name AS label, CAST(COUNT(t.id) AS FLOAT) AS value 
        FROM task_types tt LEFT JOIN tasks t ON tt.id = t.task_type_id GROUP BY tt.name
    """)
    suspend fun selectTasksByType(): List<ChartData>

    @Query("""
        SELECT tt.name AS label, CAST(COUNT(t.id) AS FLOAT) AS value 
        FROM task_types tt INNER JOIN tasks t ON tt.id = t.task_type_id 
        WHERE t.status = 'completed' OR t.status = 'completed' GROUP BY tt.name
    """)
    suspend fun selectCompletedByTypes(): List<ChartData>

    @Query("SELECT * FROM daily_stats WHERE date = :date LIMIT 1")
    suspend fun findDailyStats(date: LocalDate): DailyStatsEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDailyStats(stats: DailyStatsEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertDailyStats(stats: DailyStatsEntity)

    @Query("UPDATE daily_stats SET total_tasks = total_tasks + :addTotal, in_progress_tasks = in_progress_tasks + :addInProgress WHERE date = :date")
    suspend fun updateDailyAdd(date: LocalDate, addTotal: Int, addInProgress: Int)

    @Query("""
        INSERT INTO daily_stats (date, completed_tasks, in_progress_tasks, total_tasks, overdue_tasks) 
        VALUES (:date, :completed, 0, 0, 0) 
        ON CONFLICT(date) DO UPDATE SET completed_tasks = :completed
    """)
    suspend fun upsertCompletedStats(date: LocalDate, completed: Int)

    @Query("SELECT * FROM daily_stats ORDER BY date DESC LIMIT 10")
    suspend fun selectDailyStatsForTrend(): List<DailyStatsEntity>

    @Query("SELECT COUNT(*) FROM tasks WHERE status != 'completed'")
    suspend fun countActiveTasks(): Int

    @Query("SELECT COUNT(*) FROM tasks WHERE deadline < :now AND status != 'completed'")
    suspend fun countOverdueTasks(now: OffsetDateTime): Int

    @Query("SELECT COUNT(*) FROM tasks WHERE status = 'underway'")
    suspend fun countUnderwayTasks(): Int

    @Query("SELECT COUNT(*) FROM tasks WHERE status = 'completed' AND date(updated_at) = date(:dateStr)")
    suspend fun countCompletedTasksByDate(dateStr: String): Int

    @Query("""
        SELECT AVG(CASE 
            WHEN final_priority = 'Casual' THEN 1 WHEN final_priority = 'Low' THEN 2 
            WHEN final_priority = 'Mid' THEN 3 WHEN final_priority = 'High' THEN 4 
            WHEN final_priority = 'Extreme' THEN 5 ELSE 0 END) 
        FROM tasks WHERE status != 'completed'
    """)
    suspend fun getAvgPriority(): Double?

    @Query("""
        SELECT MAX(CASE 
            WHEN final_priority = 'Casual' THEN 1 WHEN final_priority = 'Low' THEN 2 
            WHEN final_priority = 'Mid' THEN 3 WHEN final_priority = 'High' THEN 4 
            WHEN final_priority = 'Extreme' THEN 5 ELSE 0 END) 
        FROM tasks
    """)
    suspend fun getMaxPriority(): Int?

    @Query("SELECT AVG((julianday(deadline) - julianday(:now)) * 24) FROM tasks WHERE status != 'completed' AND deadline IS NOT NULL")
    suspend fun getAvgHoursToDeadline(now: OffsetDateTime): Double?

    @Query("""
        SELECT COUNT(*) as activeTasks,
            AVG(CASE WHEN final_priority = 'Casual' THEN 1 WHEN final_priority = 'Low' THEN 2 WHEN final_priority = 'Mid' THEN 3 WHEN final_priority = 'High' THEN 4 WHEN final_priority = 'Extreme' THEN 5 ELSE 0 END) as avgPriority,
            MAX(CASE WHEN final_priority = 'Casual' THEN 1 WHEN final_priority = 'Low' THEN 2 WHEN final_priority = 'Mid' THEN 3 WHEN final_priority = 'High' THEN 4 WHEN final_priority = 'Extreme' THEN 5 ELSE 0 END) as maxPriority
        FROM tasks WHERE status = 'underway'
    """)
    suspend fun getCapacityMetrics(): CapacityMetrics?

    // --- СЕКЦИЯ 7: ПОТОКИ ДАННЫХ ДЛЯ UI (FLOW) ---
    @Query("SELECT * FROM daily_stats ORDER BY date DESC LIMIT 7")
    fun selectLastWeekStats(): Flow<List<DailyStatsEntity>>

    @Query("SELECT * FROM tasks WHERE status NOT IN ('completed') AND deadline > :now ORDER BY deadline ASC LIMIT 3")
    fun selectClosestTasks(now: OffsetDateTime): Flow<List<TaskEntity>>

    @Query("SELECT * FROM tasks WHERE deadline >= :start AND deadline < :end")
    fun selectDailyTasks(start: OffsetDateTime, end: OffsetDateTime): Flow<List<TaskEntity>>

    @Query("SELECT * FROM tasks WHERE status != 'completed'")
    fun selectTasksForInventory(): Flow<List<TaskEntity>>

    @Query("SELECT * FROM tasks")
    suspend fun getAllTasksOnce(): List<TaskEntity>

    @Query("SELECT * FROM tasks WHERE id = :id LIMIT 1")
    suspend fun selectTaskById(id: String): TaskEntity?

    @Query("UPDATE tasks SET deadline = :deadline, status = :status, final_priority = :priority, task_type_id = :taskTypeId, updated_at = :updatedAt WHERE id = :id")
    suspend fun updateTaskPropertiesById(id: String, deadline: OffsetDateTime, status: String, priority: Int, taskTypeId: Int, updatedAt: OffsetDateTime)


}


data class ChartData(
    @ColumnInfo(name = "label") val label: String,
    @ColumnInfo(name = "value") val value: Float
)

data class CapacityMetrics(
    val activeTasks: Int,
    val avgPriority: Double,
    val maxPriority: Int
)