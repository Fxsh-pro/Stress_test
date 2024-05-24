package com.example.term_paper.service

import com.example.term_paper.model.TestConfig
import com.example.term_paper.repository.TestConfigsRepository
import jakarta.transaction.Transactional
import org.springframework.data.domain.PageRequest
import org.springframework.jdbc.core.JdbcTemplate
import org.springframework.stereotype.Service
import java.util.Collections

@Service
class TestConfigService(
    val testConfigsRepository: TestConfigsRepository,
    val jdbcTemplate: JdbcTemplate
) {
    val limit = 5

    @Transactional
    fun getAllNotStartedTests(): List<TestConfig> {
        val pageable = PageRequest.of(0, limit)
        val tests = testConfigsRepository.findAllNotTested(pageable)
        tests.forEach { it.wasTested = 1 }
        return tests
    }

    fun butchUpdateWasTested(testIds: Collection<Int>) {
        val placeholders = testIds.joinToString(separator = ",", prefix = "(", postfix = ")") { "?" }
        val sql = "UPDATE test_configs SET was_tested = 2 WHERE id IN $placeholders"
        jdbcTemplate.update(sql, *testIds.toTypedArray())
    }
}