package data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDate

@Entity(tableName = "daily_stats")
data class DailyStatsEntity(
    @PrimaryKey
    val date: LocalDate,

    @ColumnInfo(name = "total_tasks")
    val totalTasks: Int = 0,

    @ColumnInfo(name = "completed_tasks")
    val completedTasks: Int = 0,

    @ColumnInfo(name = "overdue_tasks")
    val overdueTasks: Int = 0,

    @ColumnInfo(name = "in_progress_tasks")
    val inProgressTasks: Int = 0
)