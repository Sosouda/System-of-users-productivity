package data

import androidx.room.ColumnInfo

data class PriorityCount(
    val final_priority: String,
    @ColumnInfo(name = "COUNT(*)")
    val count: Int
)

data class StatusCount(
    val status: String,
    val count: Int
)

data class TypeCount(
    val name: String,
    val count: Int
)

data class TitleDesc(
    val title: String,
    val description: String
)


