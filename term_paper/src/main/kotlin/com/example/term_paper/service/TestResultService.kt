package com.example.term_paper.service

import com.example.term_paper.model.StressTestResult
import com.example.term_paper.model.StressTestResultModel
import com.example.term_paper.repository.StressTestResultRepository
import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.stereotype.Service
import java.time.Instant

@Service
class TestResultService(
    val stressTestResultRepository: StressTestResultRepository,
) {
    var mapper = ObjectMapper()

    fun saveResult(result: StressTestResult, startTime: Instant, testId: Int) {
        val currentVersion = stressTestResultRepository.findLatestByTestId(testId) ?: -1
        val model = mapToModel(result, startTime, testId, currentVersion)
        stressTestResultRepository.save(model)
    }

    private fun mapToModel(
        result: StressTestResult,
        startTime: Instant,
        testId: Int,
        currentVersion: Int
    ): StressTestResultModel {
        return StressTestResultModel().apply {
            this.testId = testId
            this.startTime = startTime
            this.endTime = Instant.now()
            this.metrics = mapper.writeValueAsString(result)
            this.version = currentVersion + 1
        }
    }
}