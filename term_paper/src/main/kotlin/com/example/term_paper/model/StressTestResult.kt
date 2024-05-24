package com.example.term_paper.model

data class StressTestResult(
    val avgTime: Long,
    val maxTime: Long,
    val minTime: Long,
    val totalTime: Long,
    val failedRequests: Int
)