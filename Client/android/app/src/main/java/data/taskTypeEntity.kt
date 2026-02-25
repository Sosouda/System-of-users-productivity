package data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "task_types")
data class TaskTypeEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Int? = null,
    val name: String
)
