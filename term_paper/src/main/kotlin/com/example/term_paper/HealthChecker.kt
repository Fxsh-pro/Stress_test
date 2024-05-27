package com.example.term_paper

import com.example.term_paper.service.TestConfigService
import lombok.extern.slf4j.Slf4j
import org.slf4j.LoggerFactory
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Service

@Service
@Slf4j
class HealthChecker(val testConfigService: TestConfigService) {

    companion object {
        private val LOG = LoggerFactory.getLogger(HealthChecker::class.java)
    }

    @Scheduled(cron = "0 0 * * * ?")
    fun healCheck() {
        LOG.info("Started heal check")
        testConfigService.resetWasTestedStatusForStaleTests()
    }

}