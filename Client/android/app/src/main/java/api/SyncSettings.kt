package api

import android.content.Context

object SyncSettings {
    private const val PREFS_NAME = "SyncSettings"
    private const val KEY_LAST_SYNC = "last_sync_time"

    fun getLastSync(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_LAST_SYNC, "") ?: ""
    }

    fun saveLastSync(context: Context, time: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_LAST_SYNC, time).apply()
    }

    fun clearSyncTime(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().remove(KEY_LAST_SYNC).apply()
    }
}