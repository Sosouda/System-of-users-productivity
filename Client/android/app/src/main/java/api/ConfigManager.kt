package api

import android.content.Context
import android.util.Log

object ConfigManager {
    private const val PREFS_NAME = "ProductivitySyncConfig"
    private const val KEY_SERVER_URL = "server_url"

    private const val DEFAULT_SERVER_URL = "http://10.0.2.2:8000"
    

    fun getServerUrl(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL) ?: DEFAULT_SERVER_URL
    }

    fun setServerUrl(context: Context, url: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_SERVER_URL, url).apply()
        Log.d("CONFIG", "Server URL updated to: $url")
    }

    fun reset(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().clear().apply()
    }
}
