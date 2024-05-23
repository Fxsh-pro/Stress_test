package com.example.term_paper

import com.example.term_paper.model.HttpMethod
import com.example.term_paper.model.TestConfig
import com.example.term_paper.repository.TestConfigsRepository
import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.future.await
import kotlinx.coroutines.launch
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Component
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.ByteBuffer
import java.time.Duration
import java.time.Instant
import java.util.Collections
import java.util.concurrent.Executors
import java.util.concurrent.Flow
import java.util.concurrent.atomic.AtomicInteger
import kotlin.system.exitProcess

@Component
class Controller(var rep: TestConfigsRepository) {

    val httpClient = HttpClient.newHttpClient()
    val threadPool = Executors.newFixedThreadPool(10).asCoroutineDispatcher()
    // @Scheduled(fixedRate = 10000000)
    // fun printHello() {
    //     val res = rep.findAll()
    //     res.filter { it.endpoint.contains("user_actions") }
    //         .forEach {
    //             println(it.toString())
    //             val url = URI.create(it.endpoint)
    //
    //             val httpRequest = when (it.method) {
    //                 HttpMethod.GET -> HttpRequest.newBuilder(url)
    //                     .GET()
    //                     .build()
    //
    //                 HttpMethod.POST -> {
    //                     val requestBody = it.requestBody ?: ""
    //                     HttpRequest.newBuilder(url)
    //                         .POST(HttpRequest.BodyPublishers.ofString(requestBody))
    //                         .build()
    //                 }
    //                 HttpMethod.PUT -> {
    //                     val requestBody = it.requestBody ?: ""
    //                     HttpRequest.newBuilder(url)
    //                         .PUT(HttpRequest.BodyPublishers.ofString(requestBody))
    //                         .build()
    //                 }
    //                 HttpMethod.DELETE -> HttpRequest.newBuilder(url)
    //                     .DELETE()
    //                     .build()
    //
    //                 else -> TODO()
    //             }
    //
    //             try {
    //                 val httpResponse = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString())
    //                 println("Response Code: ${httpResponse.statusCode()}")
    //                 println("Response : ${httpResponse.body()}")
    //                 // Handle response body as needed
    //             } catch (e: Exception) {
    //                 e.printStackTrace()
    //             }
    //         }
    //
    //     println("Hello")
    // }

    @Scheduled(fixedRate = 10000000)
    fun printHello() {
        GlobalScope.launch {
            val res = rep.findAll()
            res.filter { it.endpoint.contains("user_actions") }
                .forEach { config ->
                    println(config.toString())

                    val url = URI.create(config.endpoint)
                    val httpRequest = buildRequest(config, url)

                    // println(processRequestBody(httpRequest.bodyPublisher().get()))

                    try {
                        val res = makeRequests(httpRequest, config.countOfTests)
                        // val httpResponse = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString())
                        // println("Response Code: ${httpResponse.statusCode()}")
                        println(res)
                        // println("Response : ${httpResponse.body()}")
                        // Handle response body as needed
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }

            println("Hello")
        }
    }

    private suspend fun <T> retry(times: Int, initialDelay: Long = 100, factor: Double = 2.0, block: suspend () -> T): T {
        var currentDelay = initialDelay
        repeat(times - 1) {
            try {
                return block()
            } catch (e: Exception) {
                // e.printStackTrace() // Log the error
            }
            delay(currentDelay)
            currentDelay = (currentDelay * factor).toLong()
        }
        return block() // Last attempt
    }

    private suspend fun makeRequests(httpRequest: HttpRequest, testsCount: Int) : StressTestResult = coroutineScope {
        val results = Collections.synchronizedList(mutableListOf<Deferred<TestResult>>())
        val generalStartTime = Instant.now()

        var r = AtomicInteger(testsCount)
        // repeat(testsCount) {
        //     val startTime = Instant.now()
        //     val httpResponse = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString())
        //     val endTime = Instant.now()
        //     println(httpResponse.body())
        //     results.add(TestResult(httpResponse.statusCode(), Duration.between(startTime, endTime)))
        // }

        var i = 0;
        val delayBetweenRequests = 10L
        repeat(testsCount) {
            results.add(async(threadPool) {
                try {
                    retry(times = 3) {
                        val startTime = Instant.now()
                        val httpResponse =
                            httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString())
                        val endTime = Instant.now()
                        val rt = Duration.between(startTime, endTime)
                        TestResult(httpResponse.statusCode(), rt.toMillis())
                    }
                } catch (e : Exception) {
                    println(e.message)
                    println(++i)
                    TestResult(500, Duration.ZERO.toMillis())
                }
            })
            delay(delayBetweenRequests)
        }

        val completedResults = results.awaitAll()

        val totalTime = Duration.between(generalStartTime,Instant.now()).toMillis() - testsCount * delayBetweenRequests

        val avgTime = completedResults.sumOf { it.responseTime } / testsCount

        val maxTime = completedResults.maxOfOrNull { it.responseTime } ?: 0
        val minTime = completedResults.map { it.responseTime }
            .filter { it > 0 }
            .minOrNull() ?: 0
        val failedRequests = completedResults.count { it.statusCode >= 300 }

        StressTestResult(avgTime, maxTime, minTime, totalTime, failedRequests)
    }

    private fun buildRequest(config: TestConfig, url: URI): HttpRequest {
        val builder = HttpRequest.newBuilder(url)
        println(config.requestBody)
        when (config.method) {
            HttpMethod.GET -> builder.GET()
            HttpMethod.POST -> {
                val requestBody = config.requestBody ?: ""
                builder.POST(HttpRequest.BodyPublishers.ofString(requestBody))
            }

            HttpMethod.PUT -> {
                val requestBody = config.requestBody ?: ""
                builder.PUT(HttpRequest.BodyPublishers.ofString(requestBody))
            }

            HttpMethod.DELETE -> builder.DELETE()
            else -> TODO()
        }

        config.requestArguments?.let { builder.uri(URI.create("$url?$it")) }

        config.headers?.let { parseHeaders(it).forEach { (name, value) -> builder.header(name, value) } }

        return builder.build()
    }

    private fun parseHeaders(headers: String): Map<String, String> {
        if (headers.isBlank()) return emptyMap()

        return headers.split(";")
            .mapNotNull { it.trim().split(":").takeIf { it.size == 2 } }
            .associate { (name, value) -> name.trim() to value.trim() }
    }

    private fun processRequestBody(publisher: Flow.Publisher<ByteBuffer>): JsonNode? {
        val accumulator = StringBuilder()
        val objectMapper = ObjectMapper()
        var jsonNode: JsonNode? = null

        val subscriber = object : Flow.Subscriber<ByteBuffer> {
            override fun onSubscribe(subscription: Flow.Subscription) {
                subscription.request(Long.MAX_VALUE)
            }

            override fun onNext(item: ByteBuffer) {
                val byteArray = ByteArray(item.remaining())
                item.get(byteArray)
                accumulator.append(String(byteArray))
            }

            override fun onError(throwable: Throwable) {
                println("Error reading request body: ${throwable.message}")
            }

            override fun onComplete() {
                val jsonBody = accumulator.toString()
                jsonNode = objectMapper.readTree(jsonBody)
            }
        }

        publisher.subscribe(subscriber)
        return jsonNode
    }
}

data class TestResult(
    val statusCode: Int,
    val responseTime: Long,
)

data class StressTestResult(
    val avgTime: Long,
    val maxTime: Long,
    val minTime: Long,
    val totalTime: Long,
    val failedRequests: Int
)