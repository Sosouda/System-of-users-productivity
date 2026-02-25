package data

import androidx.room.*

@Dao
interface DailyStatsDao {

    @Query("SELECT * FROM daily_stats WHERE date = :date LIMIT 1")
    suspend fun getStatsByDate(date: String): DailyStatsEntity?

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertStats(stats: DailyStatsEntity)

    @Update
    suspend fun updateStats(stats: DailyStatsEntity)

    // Для первого графика (только завершенные)
    @Query("SELECT date, completed_tasks FROM daily_stats ORDER BY date ASC")
    suspend fun getCompletedTasksHistory(): List<CompletedHistoryData>

    // Для второго графика (только в процессе)
    @Query("SELECT date, in_progress_tasks FROM daily_stats ORDER BY date ASC")
    suspend fun getInProgressHistory(): List<InProgressHistoryData>

    @Query("SELECT COUNT(*) FROM tasks")
    suspend fun getTotalTasksCount(): Int
}

data class DailyHistoryData(
    val date: String,
    val completed_tasks: Int = 0,
    val in_progress_tasks: Int = 0
)
data class CompletedHistoryData(val date: String, val completed_tasks: Int)
data class InProgressHistoryData(val date: String, val in_progress_tasks: Int)