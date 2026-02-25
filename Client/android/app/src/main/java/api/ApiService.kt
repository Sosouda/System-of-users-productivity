package api

import android.util.Log
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*

data class AuthResponse(
    val access_token: String,
    val token_type: String
)

data class TaskDto(
    val id: String,
    val title: String,
    val description: String?,
    val task_type_id: Int,
    val personal_priority: Int,
    val influence: Int,
    val status: String,
    val deadline: String?,
    val created_at: String,
    val updated_at: String,
    val final_priority: String
)

data class SyncPushRequest(
    val tasks: List<TaskDto>
)

data class PullResponse(
    val tasks: List<TaskDto>,
    val server_time: String
)

interface ApiService {
    @POST("auth/login")
    @FormUrlEncoded
    suspend fun login(
        @Field("username") email: String,
        @Field("password") pass: String
    ): Response<AuthResponse>

    @POST("auth/register")
    suspend fun register(@Body user: Map<String, String>): Response<Unit>

    @POST("sync/push")
    suspend fun pushTasks(
        @Header("Authorization") token: String,
        @Body payload: SyncPushRequest
    ): Response<Unit>

    @GET("sync/pull")
    suspend fun pullTasks(
        @Header("Authorization") token: String,
        @Query("last_sync") lastSync: String
    ): Response<PullResponse>
}

object RetrofitClient {
    private var baseUrl: String = "http://10.0.2.2:8000/"
    private var apiService: ApiService? = null

    fun initialize(context: android.content.Context) {
        baseUrl = ConfigManager.getServerUrl(context)
        apiService = null
    }

    val instance: ApiService
        get() {
            if (apiService == null) {
                apiService = Retrofit.Builder()
                    .baseUrl(baseUrl)
                    .addConverterFactory(GsonConverterFactory.create())
                    .build()
                    .create(ApiService::class.java)
            }
            return apiService!!
        }

    fun reset() {
        apiService = null
    }
}

suspend fun register(login: String, email: String, pass: String): Boolean {
    return try {
        val payload = mapOf(
            "username" to login,
            "email" to email,
            "password" to pass
        )
        val response = RetrofitClient.instance.register(payload)
        if (!response.isSuccessful) {
            Log.e("AUTH", "Register failed: ${response.errorBody()?.string()}")
        }
        response.isSuccessful
    } catch (e: Exception) {
        Log.e("AUTH", "Register error: ${e.message}")
        false
    }
}