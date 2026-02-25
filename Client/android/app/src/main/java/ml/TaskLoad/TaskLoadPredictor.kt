package ml.TaskLoad

import android.content.Context
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import org.json.JSONObject
import java.nio.FloatBuffer

class TaskLoadPredictor(context: Context) {

    private val env: OrtEnvironment = OrtEnvironment.getEnvironment()
    private val session: OrtSession
    private val scalersJson: JSONObject

    init {
        val modelBytes = context.assets.open("tlm.onnx").use { it.readBytes() }

        session = env.createSession(modelBytes)

        val jsonString = context.assets.open("tlm_scalers.json").bufferedReader().use { it.readText() }
        scalersJson = JSONObject(jsonString)
    }

    private fun scaleValue(value: Float, key: String): Float {
        val config = scalersJson.getJSONObject(key)
        // В JSON значения mean и scale лежат в массивах [value]
        val mean = config.getJSONArray("mean").getDouble(0).toFloat()
        val scale = config.getJSONArray("scale").getDouble(0).toFloat()
        return (value - mean) / scale
    }

    fun predictCapacity(
        activeTasks: Int,
        avgPriority: Float,
        maxPriority: Int,
        avgHoursToDeadline: Int,
        overdueTasks: Int
    ): Int {
        if (activeTasks == 0 && overdueTasks == 0) return 0

        val inputs = floatArrayOf(
            scaleValue(activeTasks.toFloat(), "active_tasks"),
            scaleValue(avgPriority, "avg_priority"),
            scaleValue(maxPriority.toFloat(), "max_priority"),
            scaleValue(avgHoursToDeadline.toFloat(), "avg_hours_to_deadline"),
            scaleValue(overdueTasks.toFloat(), "overdue_tasks")
        )

        val inputName = session.inputNames.iterator().next()
        val tensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(inputs), longArrayOf(1, 5))

        val result = session.run(mapOf(inputName to tensor))

        @Suppress("UNCHECKED_CAST")
        val output = result[0].value as FloatArray
        val predictedValue = output[0]
        return predictedValue.toInt().coerceIn(0, 100)
    }

    fun close() {
        session.close()
        env.close()
    }
}