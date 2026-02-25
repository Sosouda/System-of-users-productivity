package data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Database(
    entities = [TaskEntity::class, TaskTypeEntity::class, DailyStatsEntity::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class MainDb : RoomDatabase() {

    abstract fun taskDao(): TaskDao
    abstract fun dailyStatsDao(): DailyStatsDao

    companion object {
        @Volatile
        private var INSTANCE: MainDb? = null

        fun createDatabase(context: Context): MainDb {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    MainDb::class.java,
                    "SPS.db"
                )
                    .addCallback(DatabaseCallback())
                    .build()
                INSTANCE = instance
                instance
            }
        }


        private class DatabaseCallback : RoomDatabase.Callback() {
            override fun onCreate(db: SupportSQLiteDatabase) {
                super.onCreate(db)
                INSTANCE?.let { database ->
                    CoroutineScope(Dispatchers.IO).launch {
                        val taskDao = database.taskDao()


                        val initialTypes = listOf(
                            "Other", "Meeting", "Dust Cleaning", "Documentation",
                            "Customer Support", "Code Bug Fix", "Research",
                            "Optimization", "Deployment", "Project Management",
                            "Feature Development"
                        )

                        initialTypes.forEach { typeName ->
                            taskDao.insertTaskType(TaskTypeEntity(name = typeName))
                        }
                    }
                }
            }
        }
    }
}