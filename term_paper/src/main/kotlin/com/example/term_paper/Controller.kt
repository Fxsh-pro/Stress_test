package com.example.term_paper

import com.example.term_paper.model.HttpMethod
import com.example.term_paper.model.StressTestResult
import com.example.term_paper.model.TestConfig
import com.example.term_paper.model.TestResult
import com.example.term_paper.service.TestConfigService
import com.example.term_paper.service.TestResultService
import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import jakarta.transaction.Transactional
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
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

@Component
class Controller(
    var testConfigService: TestConfigService,
    var testResultService: TestResultService
) {

    val httpClient = HttpClient.newHttpClient()
    val threadPool = Executors.newFixedThreadPool(10).asCoroutineDispatcher()
    val delayBetweenRequests = 10L

    @Scheduled(cron = "0 */2 * * * *") // Cron expression for every 2 minutes
    @Transactional
    fun printHello() {
        GlobalScope.launch {
            val testConfigs = testConfigService.getAllNotStartedTests()
            testConfigs.forEach {
                val url = URI.create(it.endpoint)
                val httpRequest = buildRequest(it, url)

                try {
                    val startTime = Instant.now()
                    val result = calculateTestStatistics(httpRequest, it.countOfTests)
                    testResultService.saveResult(result, startTime, it.id)
                    testConfigService.butchUpdateWasTested(listOf(it.id))
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            // println("Hello")
        }
    }

    private suspend fun <T> retry(
        times: Int,
        initialDelay: Long = 100,
        factor: Double = 2.0,
        block: suspend () -> T
    ): T {
        var currentDelay = initialDelay
        repeat(times - 1) {
            try {
                return block()
            } catch (_: Exception) {
            }
            delay(currentDelay)
            currentDelay = (currentDelay * factor).toLong()
        }
        return block() // Last attempt
    }

    private suspend fun makeRequestsV2(httpRequest: HttpRequest, testsCount: Int): List<TestResult> = coroutineScope {
        val results = Collections.synchronizedList(mutableListOf<Deferred<TestResult>>())

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
                } catch (e: Exception) {
                    TestResult(500, Duration.ZERO.toMillis())
                }
            })
            delay(delayBetweenRequests)
        }
        results.awaitAll()
    }

    private suspend fun calculateTestStatistics(httpRequest: HttpRequest, testsCount: Int): StressTestResult =
        coroutineScope {
            val completedResults = makeRequestsV2(httpRequest, testsCount)
            // repeat(testsCount) {
            //     results.add(async(threadPool) {
            //         try {
            //             retry(times = 3) {
            //                 val startTime = Instant.now()
            //                 val httpResponse =
            //                     httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString())
            //                 val endTime = Instant.now()
            //                 val rt = Duration.between(startTime, endTime)
            //                 TestResult(httpResponse.statusCode(), rt.toMillis())
            //             }
            //         } catch (e : Exception) {
            //             println(e.message)
            //             println(++i)
            //             TestResult(500, Duration.ZERO.toMillis())
            //         }
            //     })
            //     delay(delayBetweenRequests)
            // }

            val totalTime = completedResults.sumOf { it.responseTime }

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
        // println(config.requestBody)
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
