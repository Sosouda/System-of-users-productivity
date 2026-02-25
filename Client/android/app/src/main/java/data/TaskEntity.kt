package data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.ForeignKey
import androidx.room.Index
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.util.UUID


@Entity(tableName = "tasks",
    foreignKeys = [
        ForeignKey(
            entity = TaskTypeEntity::class,
            parentColumns = ["id"],
            childColumns = ["task_type_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["task_type_id"])
    ]
)
data class TaskEntity(
    @PrimaryKey
    val id: String = UUID.randomUUID().toString(),
    val title: String,
    val description: String?,
    @ColumnInfo(name="task_type_id")
    val taskTypeId: Int,
    @ColumnInfo(name="personal_priority")
    val personalPriority: Int,
    val influence : Int,
    @ColumnInfo(name="created_at")
    val createdAt: OffsetDateTime = OffsetDateTime.now(ZoneOffset.UTC),
    @ColumnInfo(name = "updated_at")
    val updatedAt: OffsetDateTime = OffsetDateTime.now(ZoneOffset.UTC),
    val deadline: OffsetDateTime?,
    @ColumnInfo(name="final_priority")
    val finalPriority: String,
    val status: String

)




